# 3D Garment Part Understanding

Supplementary materials for **Fine-Grained 3D Garment Part Segmentation with Topology-Aware Structural Fields for Virtual Try-On**.

This repository is intended to provide supplementary qualitative results, structural-field visualizations, garment-to-body alignment / simulation examples, and illustrations of the annotations and evaluation protocol used in the paper.

> The full training and alignment code is not released at this stage.

## Overview

Our work studies **fine-grained 3D garment part understanding** on assembled garment meshes. In contrast to garment-category segmentation, the task assigns functional part labels *within each garment* and augments them with continuous topology-aware structural fields.

The representation contains:

- **12 functional part labels**: collar, waist, hem, cuff, sleeve, body front, body back, lower front, lower back, pocket, ruffles, and hat.
- **4 topology-aware structural fields** defined from mesh geodesic distances to neckline, waistline, hemline, and cuff anchors.

The predicted semantics identify **what functional part a vertex belongs to**, while the structural fields describe **where the vertex lies within the garment structure**.

## Repository contents

- `assets/segmentation/` — qualitative garment-part segmentation results
- `assets/structural_fields/` — neckline / waistline / hemline / cuff field visualizations
- `assets/alignment/` — garment-to-body alignment comparisons
- `assets/simulation/` — dynamic simulation examples
- `assets/failure_cases/` — representative failure cases
- `docs/annotation_example.md` — annotation and structural-target illustration
- `docs/evaluation_protocol.md` — downstream alignment evaluation protocol

## Notes

The source garment meshes are derived from the dataset used in the paper under its original terms. This repository is intended to host our own visualizations, derived annotations where redistribution is permitted, and supplementary evaluation material.

## Status

Materials will be added progressively.
