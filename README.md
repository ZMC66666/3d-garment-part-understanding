# 3D Garment Part Understanding

Supplementary materials for **Fine-Grained 3D Garment Part Segmentation with Topology-Aware Structural Fields for Virtual Try-On**.

## Simulation Results

<table>
  <tr>
    <td width="50%" align="center">
      <a href="assets/simulation/dress_rollout.mp4">
        <img src="assets/simulation/dress_showcase_grid.png" width="100%" alt="Dress simulation">
      </a>
      <br>
      <b>Dress</b> · <a href="assets/simulation/dress_rollout.mp4">▶ Play video</a>
    </td>
    <td width="50%" align="center">
      <a href="assets/simulation/pants_rollout.mp4">
        <img src="assets/simulation/pants_showcase_grid.png" width="100%" alt="Pants simulation">
      </a>
      <br>
      <b>Pants</b> · <a href="assets/simulation/pants_rollout.mp4">▶ Play video</a>
    </td>
  </tr>
  <tr>
    <td width="50%" align="center">
      <a href="assets/simulation/skirt_rollout.mp4">
        <img src="assets/simulation/skirt_showcase_grid.png" width="100%" alt="Skirt simulation">
      </a>
      <br>
      <b>Skirt</b> · <a href="assets/simulation/skirt_rollout.mp4">▶ Play video</a>
    </td>
    <td width="50%" align="center">
      <a href="assets/simulation/top_rollout.mp4">
        <img src="assets/simulation/top_showcase_grid.png" width="100%" alt="Top simulation">
      </a>
      <br>
      <b>Top</b> · <a href="assets/simulation/top_rollout.mp4">▶ Play video</a>
    </td>
  </tr>
</table>

*Click any preview to open the corresponding simulation video.*

## Overview

Our work studies **fine-grained 3D garment part understanding** on assembled garment meshes. In contrast to garment-category segmentation, the task assigns functional part labels *within each garment* and augments them with continuous topology-aware structural fields.

The representation contains:

- **12 functional part labels**: collar, waist, hem, cuff, sleeve, body front, body back, lower front, lower back, pocket, ruffles, and hat.
- **4 topology-aware structural fields** defined from mesh geodesic distances to neckline, waistline, hemline, and cuff anchors.

The predicted semantics identify **what functional part a vertex belongs to**, while the structural fields describe **where the vertex lies within the garment structure**.

> The full training and alignment code is not released at this stage.

## Supplementary Materials

- [assets/segmentation/](assets/segmentation/) — qualitative garment-part segmentation results
- [assets/structural_fields/](assets/structural_fields/) — neckline / waistline / hemline / cuff field visualizations
- [assets/alignment/](assets/alignment/) — garment-to-body alignment comparisons
- [assets/simulation/](assets/simulation/) — dynamic simulation videos
- [assets/failure_cases/](assets/failure_cases/) — representative failure cases
- [docs/annotation_example.md](docs/annotation_example.md) — annotation and structural-target illustration
- [docs/evaluation_protocol.md](docs/evaluation_protocol.md) — downstream alignment evaluation protocol

## Notes

The source garment meshes are derived from the dataset used in the paper under its original terms. This repository is intended to host our own visualizations, derived annotations where redistribution is permitted, and supplementary evaluation material.
