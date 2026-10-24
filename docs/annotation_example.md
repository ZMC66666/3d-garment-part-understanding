# Annotation and Structural-Field Example

This page documents the annotation process used to construct the semantic and
structural targets. The released example is the same dress shown on the
project page (`4140df311cf31024c3beb40f8af7c480`).

## 1. Semantic annotation

Annotations are transferred from the sewing panels to the assembled triangle
mesh. Every face inherits its panel's functional label; each vertex then takes
the majority label of its incident faces. The global 12-class vocabulary and
IDs are:

| ID | Label | ID | Label |
|---:|---|---:|---|
| 0 | body_front | 6 | waist |
| 1 | body_back | 7 | cuff |
| 2 | lower_front | 8 | hem |
| 3 | lower_back | 9 | pocket |
| 4 | sleeve | 10 | ruffles |
| 5 | collar | 11 | hat |

The dress example contains the nine classes that are present on that garment;
classes absent from the mesh are simply unused. Labels describe the functional
role of a surface region, not the garment category or sewing-panel identity.

## 2. Anchor annotation

Five curve-like vertex sets are constructed from the panel semantics and mesh
geometry before sewing-panel vertices are welded:

- neckline,
- waistline,
- hemline,
- left cuff, and
- right cuff.

The neckline is the collar boundary, and the waistline is the waist region. If
an explicit Hem region is present, it supplies the hemline; otherwise the lower
12% (in the vertical axis) of the outer body/lower-region boundary is used.
Cuff boundaries are split about the median horizontal coordinate and their
outer 25% supplies the left and right cuff anchors. When no Cuff region is
present, the outer 12% of each sleeve is used. These vertex sets are then
remapped through stitch welding onto the assembled mesh and stored with the
annotation. Constructing them before welding preserves panel-side interface
vertices that cannot be recovered exactly from majority-voted labels on the
final mesh.

The left and right cuff anchors are united before distance computation, so the
learning target has four channels: **Neck, Waist, Hem, and Cuff**. The rules
avoid a second point-by-point anchor-labeling stage.

Fallbacks are used only when their primary semantic region is absent: the top
20% of the torso boundary for Neck and the top 20% of the lower-region boundary
for Waist. An anchor is stored as a one-dimensional array of zero-based mesh
vertex indices. A channel is invalid when neither its primary rule nor fallback
can construct an anchor.

For the released dress, the Neck, Waist, Hem, and combined Cuff anchors contain
129, 1,640, 193, and 52 vertices, respectively.

## 3. From anchors to structural fields

For channel \(k\), the anchor set is \(A_k\). Mesh edges are weighted by their
3D Euclidean lengths, and multi-source Dijkstra gives

\[
d_k(v)=\min_{a\in A_k} d_G(v,a).
\]

Let \(q_k\) be the 99th percentile of finite values in \(d_k\). The stored
target is

\[
s_k(v)=\operatorname{clip}\!\left(\frac{d_k(v)}{q_k+10^{-12}},0,1\right).
\]

Unreachable vertices and absent channels are marked invalid rather than
silently filled with zeros. The validity mask is trained and evaluated with
the structural coordinates.

## 4. Released files and input schema

The runnable example is in
`examples/dress_4140df311cf31024c3beb40f8af7c480/`. The arrays are split into
four compressed files so the mesh, semantics, and anchors remain visibly
separate; the script also accepts the same keys in a single `.npz` file.

| File | Keys and meaning |
|---|---|
| `vertices.npz` | `vertices`: `float32 [N,3]` assembled-mesh coordinates |
| `faces.npz` | `faces`: `int64 [F,3]` triangle vertex indices |
| `semantics.npz` | per-face and per-vertex global IDs, plus `semantic_names` |
| `anchors.npz` | neckline, waistline, hemline, left-cuff, and right-cuff vertex-index arrays |
| `metadata.json` | public sample ID and garment category |

Install the two lightweight dependencies and generate the four fields:

```bash
python -m pip install -r scripts/requirements-annotation.txt
python tools/build_structural_fields.py \
  examples/dress_4140df311cf31024c3beb40f8af7c480 \
  examples/dress_4140df311cf31024c3beb40f8af7c480/structural_fields.npz
```

The script validates mesh indices, semantic IDs, anchor indices, output range,
validity masks, and zero distance at every anchor. On this example it produces
four valid channels over all 70,678 vertices. The P99 scales are 1.141102
(Neck), 0.708534 (Waist), 0.874744 (Hem), and 1.060630 (Cuff).

Run the reproducibility test with:

```bash
python -m unittest tests/test_structural_fields.py
```

The test checks the public example's dimensions, anchor counts, value range,
validity, and normalization scales. The generated coordinates were also
checked element-by-element against the structural targets used by the project.

## Scope of this release

This release covers the annotation representation and deterministic generation
of the four structural-field targets. It does not include the training or
garment-to-body alignment implementation; those components are planned for
release after acceptance.
