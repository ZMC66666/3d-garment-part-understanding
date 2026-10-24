#!/usr/bin/env python3
"""Build four topology-aware garment structural fields from mesh anchors.

The input is an ``.npz`` file containing a triangle mesh, semantic labels, and
annotated anchor-vertex sets.  Distances are measured on the weighted mesh
graph and normalized independently at the requested quantile.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Mapping

import numpy as np
from scipy import sparse
from scipy.sparse.csgraph import dijkstra


ANCHOR_NAMES = ("neckline", "waistline", "hemline", "cuff_union")
ANCHOR_KEYS = (
    ("group__anchor_neckline",),
    ("group__anchor_waistline",),
    ("group__anchor_hemline",),
    ("group__anchor_left_cuff", "group__anchor_right_cuff"),
)
REQUIRED_KEYS = {
    "vertices",
    "faces",
    "face_semantic_id",
    "vertex_semantic_id",
    "semantic_names",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input", type=Path, help="annotated garment .npz or split annotation directory"
    )
    parser.add_argument("output", type=Path, help="output structural-field .npz")
    parser.add_argument(
        "--normalization-quantile",
        type=float,
        default=0.99,
        help="per-channel distance quantile mapped to 1 (default: 0.99)",
    )
    parser.add_argument(
        "--overwrite", action="store_true", help="replace an existing output file"
    )
    args = parser.parse_args()
    if not 0.0 < args.normalization_quantile <= 1.0:
        parser.error("--normalization-quantile must be in (0, 1]")
    if args.output.suffix.lower() != ".npz":
        parser.error("output must end in .npz")
    return args


def unique_weighted_edges(
    vertices: np.ndarray, faces: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    raw = np.concatenate(
        (faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]), axis=0
    ).astype(np.int64, copy=False)
    raw.sort(axis=1)
    raw = raw[raw[:, 0] != raw[:, 1]]
    edges = np.unique(raw, axis=0)
    lengths = np.linalg.norm(vertices[edges[:, 0]] - vertices[edges[:, 1]], axis=1)
    lengths = np.maximum(lengths, np.finfo(np.float64).eps)
    return edges, lengths.astype(np.float64, copy=False)


def mesh_graph(
    num_vertices: int, edges: np.ndarray, lengths: np.ndarray
) -> sparse.csr_matrix:
    rows = np.concatenate((edges[:, 0], edges[:, 1]))
    cols = np.concatenate((edges[:, 1], edges[:, 0]))
    weights = np.concatenate((lengths, lengths))
    return sparse.csr_matrix(
        (weights, (rows, cols)), shape=(num_vertices, num_vertices)
    )


def read_anchor_sources(
    annotation: Mapping[str, np.ndarray], num_vertices: int
) -> list[np.ndarray]:
    sources: list[np.ndarray] = []
    for keys in ANCHOR_KEYS:
        arrays = [
            np.asarray(annotation[key], dtype=np.int64)
            for key in keys
            if key in annotation and annotation[key].size
        ]
        source = (
            np.unique(np.concatenate(arrays))
            if arrays
            else np.empty(0, dtype=np.int64)
        )
        if source.size and (source.min() < 0 or source.max() >= num_vertices):
            raise ValueError(f"anchor index out of range for {keys}")
        sources.append(source)
    return sources


def load_annotation(path: Path) -> dict[str, np.ndarray]:
    if path.is_file():
        with np.load(path, allow_pickle=False) as source:
            return {key: source[key] for key in source.files}
    if not path.is_dir():
        raise FileNotFoundError(path)

    annotation: dict[str, np.ndarray] = {}
    for filename in ("vertices.npz", "faces.npz", "semantics.npz", "anchors.npz"):
        source_path = path / filename
        if not source_path.is_file():
            raise FileNotFoundError(f"split annotation is missing {source_path}")
        with np.load(source_path, allow_pickle=False) as source:
            overlap = set(annotation) & set(source.files)
            if overlap:
                raise ValueError(f"duplicate keys in split annotation: {sorted(overlap)}")
            annotation.update({key: source[key] for key in source.files})

    metadata_path = path / "metadata.json"
    if metadata_path.is_file():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        for key in ("garment_id", "garment_category"):
            if key in metadata:
                annotation[key] = np.asarray(str(metadata[key]))
    return annotation


def validate_annotation(annotation: Mapping[str, np.ndarray]) -> None:
    missing = REQUIRED_KEYS - set(annotation)
    if missing:
        raise ValueError(f"input is missing keys: {sorted(missing)}")
    vertices = annotation["vertices"]
    faces = annotation["faces"]
    if vertices.ndim != 2 or vertices.shape[1] != 3:
        raise ValueError(f"vertices must have shape (N, 3), got {vertices.shape}")
    if faces.ndim != 2 or faces.shape[1] != 3:
        raise ValueError(f"faces must have shape (F, 3), got {faces.shape}")
    if faces.size and (faces.min() < 0 or faces.max() >= len(vertices)):
        raise ValueError("face index out of range")
    if annotation["vertex_semantic_id"].shape != (len(vertices),):
        raise ValueError("vertex_semantic_id must contain one label per vertex")
    if annotation["face_semantic_id"].shape != (len(faces),):
        raise ValueError("face_semantic_id must contain one label per face")
    class_count = len(annotation["semantic_names"])
    for key in ("vertex_semantic_id", "face_semantic_id"):
        labels = annotation[key]
        if labels.size and (labels.min() < 0 or labels.max() >= class_count):
            raise ValueError(f"{key} contains an ID outside semantic_names")


def build_fields(
    vertices: np.ndarray,
    faces: np.ndarray,
    sources: list[np.ndarray],
    quantile: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, int]:
    edges, lengths = unique_weighted_edges(vertices, faces)
    graph = mesh_graph(len(vertices), edges, lengths)
    channel_count = len(ANCHOR_NAMES)
    fields = np.full((len(vertices), channel_count), np.nan, dtype=np.float32)
    valid_mask = np.zeros_like(fields, dtype=np.bool_)
    scales = np.full(channel_count, np.nan, dtype=np.float64)
    epsilon = 1e-12

    for channel, source in enumerate(sources):
        if not source.size:
            continue
        distances = dijkstra(
            graph, directed=False, indices=source, min_only=True
        )
        reachable = np.isfinite(distances)
        if not reachable.any():
            continue
        scale = float(np.quantile(distances[reachable], quantile))
        if not np.isfinite(scale) or scale <= epsilon:
            continue
        values = np.clip(distances[reachable] / (scale + epsilon), 0.0, 1.0)
        fields[reachable, channel] = values.astype(np.float32)
        valid_mask[reachable, channel] = True
        scales[channel] = scale

    return fields, valid_mask, valid_mask.any(axis=0), scales, len(edges)


def validate_output(
    fields: np.ndarray,
    valid_mask: np.ndarray,
    dim_valid: np.ndarray,
    sources: list[np.ndarray],
) -> None:
    if not np.array_equal(dim_valid, valid_mask.any(axis=0)):
        raise RuntimeError("dimension-valid flags disagree with vertex masks")
    if not np.isfinite(fields[valid_mask]).all():
        raise RuntimeError("valid field entries contain NaN or infinity")
    if not np.isnan(fields[~valid_mask]).all():
        raise RuntimeError("invalid field entries must use NaN")
    if valid_mask.any():
        values = fields[valid_mask]
        if values.min() < -1e-6 or values.max() > 1.0 + 1e-6:
            raise RuntimeError("normalized fields fall outside [0, 1]")
    for channel, source in enumerate(sources):
        if dim_valid[channel] and not np.allclose(
            fields[source, channel], 0.0, atol=1e-6
        ):
            raise RuntimeError(f"{ANCHOR_NAMES[channel]} is nonzero at its anchor")


def scalar_string(annotation: Mapping[str, np.ndarray], key: str) -> str:
    return str(np.asarray(annotation[key]).item()) if key in annotation else ""


def main() -> None:
    args = parse_args()
    if args.output.exists() and not args.overwrite:
        raise FileExistsError(f"output exists; pass --overwrite: {args.output}")

    annotation = load_annotation(args.input)
    validate_annotation(annotation)
    vertices = annotation["vertices"].astype(np.float64)
    faces = annotation["faces"].astype(np.int64)
    sources = read_anchor_sources(annotation, len(vertices))
    garment_id = scalar_string(annotation, "garment_id")
    garment_category = scalar_string(annotation, "garment_category")

    fields, valid_mask, dim_valid, scales, edge_count = build_fields(
        vertices, faces, sources, args.normalization_quantile
    )
    validate_output(fields, valid_mask, dim_valid, sources)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.output,
        struct_coord=fields,
        struct_valid_mask=valid_mask,
        struct_dim_valid=dim_valid,
        anchor_names=np.asarray(ANCHOR_NAMES),
        anchor_source_keys=np.asarray(["|".join(keys) for keys in ANCHOR_KEYS]),
        anchor_vertex_counts=np.asarray([len(source) for source in sources], dtype=np.int64),
        normalization_scale=scales,
        normalization_quantile=np.asarray(args.normalization_quantile, dtype=np.float64),
        garment_id=np.asarray(garment_id),
        garment_category=np.asarray(garment_category),
        num_vertices=np.asarray(len(vertices), dtype=np.int64),
        num_faces=np.asarray(len(faces), dtype=np.int64),
        unique_edge_count=np.asarray(edge_count, dtype=np.int64),
    )

    summary = {
        "input": str(args.input),
        "output": str(args.output),
        "vertices": len(vertices),
        "faces": len(faces),
        "anchors": dict(
            zip(ANCHOR_NAMES, [int(len(source)) for source in sources])
        ),
        "normalization_scale": dict(zip(ANCHOR_NAMES, scales.tolist())),
        "valid_dimensions": dict(zip(ANCHOR_NAMES, dim_valid.tolist())),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
