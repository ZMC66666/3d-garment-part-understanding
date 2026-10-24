# Dress annotation example

This directory contains the dress sample shown on the project page. The four
compressed array files hold the assembled triangle mesh, global 12-class
semantic labels, and five annotated vertex-index sets: neckline, waistline,
hemline, left cuff, and right cuff. The two cuff sets are combined into the
single Cuff field. `metadata.json` contains only the public ID and category.

The sample is intentionally free of server paths, captions, predictions, and
internal cache metadata. Run the repository-level command in
`docs/annotation_example.md` to reproduce its four structural targets.
