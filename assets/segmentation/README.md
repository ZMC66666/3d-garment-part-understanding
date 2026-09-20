# Qualitative segmentation results

Each row compares the ground-truth labels, our topology-aware model, and the
semantic-only PT-v3m1 baseline on a held-out garment.

| Category | Ground truth | Ours | PT-v3m1 |
| --- | --- | --- | --- |
| Top | ![Top ground truth](tops_gt_semantic.png) | ![Top prediction](tops_ours_semantic.png) | ![Top PT-v3m1 baseline](tops_ptv3m1_semantic.png) |
| Dress | ![Dress ground truth](dresses_gt_semantic.png) | ![Dress prediction](dresses_ours_semantic.png) | ![Dress PT-v3m1 baseline](dresses_ptv3m1_semantic.png) |
| Skirt | ![Skirt ground truth](skirts_gt_semantic.png) | ![Skirt prediction](skirts_ours_semantic.png) | ![Skirt PT-v3m1 baseline](skirts_ptv3m1_semantic.png) |
| Pants | ![Pants ground truth](pants_gt_semantic.png) | ![Pants prediction](pants_ours_semantic.png) | ![Pants PT-v3m1 baseline](pants_ptv3m1_semantic.png) |

The `simulation_inputs/` subdirectory contains the semantic render associated
with each dynamic simulation example.
