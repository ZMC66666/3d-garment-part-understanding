# 3D Garment Part Understanding

Project page and supplementary materials for **Fine-Grained 3D Garment Part Segmentation with Topology-Aware Structural Fields for Virtual Try-On**.

**Project page:** https://zmc66666.github.io/3d-garment-part-understanding/

The project page presents autoplay simulation rollouts, fine-grained garment-part segmentation, topology-aware structural fields, and garment-to-body alignment results.

## Technical supplement

Read the supplementary explanations on the project website:

- [Alignment method and structural-field usage](https://zmc66666.github.io/3d-garment-part-understanding/alignment_method.html)
- [Evaluation protocol and Table 3](https://zmc66666.github.io/3d-garment-part-understanding/evaluation_protocol.html)

The method page explains how predicted garment cues determine anatomical surface correspondences. The protocol page defines the metrics and regional aggregation used in Table 3. Editable sources are the corresponding Markdown files in `docs/`.

## Repository contents

- `assets/segmentation/` — qualitative garment-part segmentation results
- `assets/structural_fields/` — structural-field visualizations
- `assets/alignment/` — garment-to-body alignment comparisons
- `assets/simulation/` — dynamic simulation videos
- `tools/build_structural_fields.py` — portable structural-target generator
- `examples/dress_4140df311cf31024c3beb40f8af7c480/` — runnable dress annotation example
- `examples/label_map_12cls.json` — machine-readable global label map
- `docs/annotation_example.md` — annotation process and file schema
- `docs/evaluation_protocol.md` — downstream evaluation protocol
- `docs/index.html` — project-page source

## Reproduce the annotation example

```bash
python -m pip install -r scripts/requirements-annotation.txt
python tools/build_structural_fields.py \
  examples/dress_4140df311cf31024c3beb40f8af7c480 \
  examples/dress_4140df311cf31024c3beb40f8af7c480/structural_fields.npz
python -m unittest tests/test_structural_fields.py
```

The annotation representation, example dress, and deterministic structural-field
generation are released now. The full training and alignment code is planned
for release after acceptance.

## Updating the technical reading pages

GitHub Pages serves `docs/` as static files. The technical `.html` pages are generated from their matching `.md` sources:

```bash
python -m pip install -r scripts/requirements-docs.txt
python scripts/build_technical_docs.py
python scripts/build_technical_docs.py --check
```

Commit the generated HTML together with any Markdown changes. Equations are displayed with MathJax; navigation, tables, and document text are static HTML.
