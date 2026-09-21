# T-pose garment-to-body alignment meshes

Each `tpose_on_body.ply` is a full-resolution binary PLY scene containing both
the SMPL-X body and the garment aligned on the body. The body is gray and the
garment retains its semantic vertex colors.

The geometry is the exact warmup-rollout frame 0 used to render the matching
`tpose_on_body.png` showcase image.

| Category | Garment ID | Total vertices | Total faces | Garment vertices |
| --- | --- | ---: | ---: | ---: |
| Dress | `7ede5ae39a1a90c605de25aaabc83f5b` | 63,338 | 126,302 | 52,863 |
| Skirt | `9e28239697d5d2a9f5261f15f0121f35` | 56,656 | 112,332 | 46,181 |
| Top | `30628164375b24f1b56cee846177eede` | 67,113 | 133,878 | 56,638 |
| Pants | `3997439ee4c9381a81e4b39f210e1f66` | 39,995 | 79,197 | 29,520 |

All four scenes contain 10,475 body vertices. Faces for the body and garment
remain separate within the combined mesh topology.
