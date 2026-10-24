# Real garment panels and stitch topology

These SVGs visualize GarmageSet sample `4140df311cf31024c3beb40f8af7c480`. The paired raw OBJ
identifies its exporter as **Style3D V7.1.1089**. Source assets remain subject
to the upstream GarmageSet terms; this directory does not relicense them.

## Source and statistics

- Raw source: `GarmageSet/raw/41/4140df311cf31024c3beb40f8af7c480.obj`.
- Paired paper-pattern annotation: `GarmageSet/patterns/4140df311cf31024c3beb40f8af7c480.json`.
- 15 OBJ panel groups, matched by ID to 15 JSON panels.
- 72,186 3D vertices, 72,186 2D `vt` coordinates,
  140,908 faces (140,908 triangles).
- 59 JSON stitches describe paper-edge segments, not individual vertex pairs.
- 1,549 raw OBJ `l` pair records; 0-based stitch indices.
- Remove 0 invalid pairs, 10 self-pairs,
  and 5 repeated unordered pairs: **1,534 clean vertex pairs**.

## Geometry and display

`sewing_pattern.svg` follows the actual per-panel mesh boundary edges in the
OBJ's `vt` coordinates. It does not replace the outlines with stylized shapes.
Panel 01–15 follow the OBJ group order. Display labels omit original
panel UUIDs and original-language part labels.

Both SVGs use the **same original 2D layout** and one common uniform scale,
translation, and screen-axis reversal. No panel-wise scaling, rotation,
repacking, smoothing, or contour simplification is applied. Coordinates are
rounded to 0.1 display pixels in the SVG output.

`stitch_topology.svg` shows **68 real vertex pairs**: up to two spatially
spread samples from each unordered panel-pair group, including within-panel
seams. Curves are visual connectors, not physical seam paths. Their endpoints
are the actual paired `vt` positions. Colors distinguish panel-pair groups
and may repeat. Sampling is only for readability; all **1,534** cleaned
pairs are used to compute the statistics. No pairing is invented.

## Processing boundary

The raw OBJ **already contains triangle faces**. The project's connected-mesh
preprocessing reads the discrete OBJ `l` pairs and performs **seam welding**;
it does not claim to reconstruct or retriangulate the raw mesh from the JSON.
The JSON supplies panel and paper-edge annotations. These figures visualize
the supplied pattern layout and stitch topology, not a newly evaluated
triangulation or simulation method.

## Reproduce

Run from the repository root, supplying local input paths:

```sh
python tools/render_dataset_pipeline_assets.py \
  --obj INPUT.obj --pattern INPUT.json \
  --output-dir docs/assets/dataset/dress_4140df311cf31024c3beb40f8af7c480 \
  --sample-id 4140df311cf31024c3beb40f8af7c480 --stitch-index-base 0
```

The generator uses only the Python standard library and requires no GUI.
It validates JSON/OBJ panel identity, closed panel boundaries, and stitch
indexing, and parses both output SVGs as XML before reporting their size
and element counts. It reads source inputs without modifying them.
