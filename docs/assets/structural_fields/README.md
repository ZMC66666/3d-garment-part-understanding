# Structural-field meshes

Full-resolution binary PLY meshes with per-vertex structural-field colors.
Every garment directory contains GT and E2 prediction meshes for the four
channels: `neckline`, `waistline`, `hemline`, and `cuff_union`.

Structural values use the same clipped `[0, 1]` rainbow palette as the project
page. Magenta (`255, 0, 255`) marks an invalid or inapplicable field. Therefore,
an entirely magenta PLY is intentional for a category without that structural
channel.

Valid channels by category:

- Top: neckline, hemline, cuff union
- Dress: all four channels
- Skirt: waistline and hemline
- Pants: waistline and hemline

File names follow `struct_<channel>_{gt,pred}.ply`.
