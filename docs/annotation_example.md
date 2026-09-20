# Annotation and Structural-Field Example

This page explains the annotation format used for fine-grained 3D garment part understanding.

## Functional part labels

Each vertex of an assembled garment mesh is assigned one of 12 functional labels:

1. collar
2. waist
3. hem
4. cuff
5. sleeve
6. body front
7. body back
8. lower front
9. lower back
10. pocket
11. ruffles
12. hat

These labels describe the **functional role of a surface region within an individual garment**, rather than the garment category or its original sewing-panel identity.

## Structural anchors

Four anchor types are used:

- neckline
- waistline
- hemline
- cuff

Anchors are curve-like vertex sets constructed from garment annotations. Structural targets are then defined on the assembled mesh using geodesic distance to the corresponding anchor set.

## Structural fields

For each valid anchor channel, the geodesic distance is computed over the garment mesh graph and normalized to obtain a value in `[0, 1]`.

The four channels are:

- Neck
- Waist
- Hem
- Cuff

A channel is excluded where the corresponding anchor is absent, the vertex is unreachable, or the normalization scale is invalid.

## Planned example

A compact example will be added here showing:

- the garment mesh,
- the 12-class part segmentation,
- the four anchor curves,
- the four normalized structural fields.
