#!/usr/bin/env python3
"""Render real OBJ panel boundaries and sampled stitch pairs as portable SVGs.

Standard library only. No GUI, triangulation, remeshing, or source-data writes.
Example:
  python tools/render_dataset_pipeline_assets.py --obj INPUT.obj \
    --pattern INPUT.json --output-dir OUTPUT --stitch-index-base 0
"""

import argparse
from collections import Counter, defaultdict
from html import escape
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET


WIDTH, HEIGHT = 1200, 960
PALETTE = (
    '#a8d5d0', '#b9c9e8', '#e7bdd9', '#bfcde3', '#d7c4e7',
    '#92c8bc', '#a8bddf', '#eab7bb', '#efc6a3', '#b5d1df',
    '#c0d9b2', '#e9d298', '#d8b9af', '#bfc4df', '#d8c79e',
)
LINK_COLORS = ('#147d92', '#9262b6', '#c26c3b', '#25866c', '#476bb1', '#b94f78')


def obj_index(token, count):
    value = int(token)
    return value - 1 if value > 0 else count + value


def load_geometry(obj_path, pattern_path, index_base):
    vertices, texcoords, panels, raw_stitches = [], [], [], []
    panel_names, uv_by_vertex, owner = [], {}, {}
    group = None
    face_count = triangle_count = 0
    for line in obj_path.read_text(encoding='utf-8').splitlines():
        parts = line.split()
        if not parts:
            continue
        kind = parts[0]
        if kind == 'v':
            vertices.append(tuple(map(float, parts[1:4])))
        elif kind == 'vt':
            texcoords.append(tuple(map(float, parts[1:3])))
        elif kind == 'g':
            name = parts[1]
            if name not in panel_names:
                panel_names.append(name)
                panels.append(Counter())
            group = panel_names.index(name)
        elif kind == 'f':
            if group is None:
                raise ValueError('Every face must have an explicit panel group.')
            ids = []
            for corner in parts[1:]:
                fields = corner.split('/')
                if len(fields) < 2 or not fields[1]:
                    raise ValueError('Faces must reference real two-dimensional vt coordinates.')
                vi = obj_index(fields[0], len(vertices))
                ti = obj_index(fields[1], len(texcoords))
                if vi in uv_by_vertex and uv_by_vertex[vi] != texcoords[ti]:
                    raise ValueError('A vertex has multiple UV positions; split it explicitly first.')
                if vi in owner and owner[vi] != group:
                    raise ValueError('A raw vertex belongs to multiple panels.')
                uv_by_vertex[vi] = texcoords[ti]
                owner[vi] = group
                ids.append(vi)
            panels[group].update(tuple(sorted(e)) for e in zip(ids, ids[1:] + ids[:1]))
            face_count += 1
            triangle_count += len(ids) == 3
        elif kind == 'l':
            ids = [int(p.split('/')[0]) for p in parts[1:]]
            raw_stitches.extend(zip(ids[:-1], ids[1:]))
    pattern = json.loads(pattern_path.read_text(encoding='utf-8'))
    if set(panel_names) != {p['id'] for p in pattern['panels']}:
        raise ValueError('Pattern panel IDs do not match OBJ groups.')
    if not raw_stitches:
        raise ValueError('No discrete stitch records found.')
    flat = [i for pair in raw_stitches for i in pair]
    if index_base == 'auto':
        if 0 in flat:
            index_base = '0'
        elif len(vertices) in flat:
            index_base = '1'
        else:
            raise ValueError('Ambiguous stitch indexing: supply --stitch-index-base 0 or 1.')
    offset = int(index_base)
    valid, invalid, self_pairs = [], 0, 0
    for a, b in raw_stitches:
        a, b = a - offset, b - offset
        if not (0 <= a < len(vertices) and 0 <= b < len(vertices)):
            invalid += 1
        elif a == b:
            self_pairs += 1
        else:
            valid.append(tuple(sorted((a, b))))
    clean = sorted(set(valid))
    if any(a not in owner or b not in owner for a, b in clean):
        raise ValueError('A stitch endpoint has no panel geometry.')
    boundaries = []
    for edge_counts in panels:
        edges = {e for e, count in edge_counts.items() if count == 1}
        adjacency = defaultdict(list)
        for a, b in edges:
            adjacency[a].append(b)
            adjacency[b].append(a)
        if any(len(neighbors) != 2 for neighbors in adjacency.values()):
            raise ValueError('Panel boundary must consist of closed degree-two loops.')
        loops = []
        while edges:
            a, b = min(edges)
            start, prev, current = a, a, b
            loop = [a]
            edges.remove((a, b))
            while current != start:
                loop.append(current)
                nxt = next(v for v in sorted(adjacency[current]) if v != prev)
                edges.remove(tuple(sorted((current, nxt))))
                prev, current = current, nxt
            loops.append(loop)
        boundaries.append(loops)
    stats = {
        'vertices': len(vertices), 'vt': len(texcoords), 'faces': face_count,
        'triangle_faces': triangle_count, 'panels': len(panels),
        'pattern_stitches': len(pattern.get('stitches', [])),
        'raw_l_records': len(raw_stitches), 'invalid_pairs_removed': invalid,
        'self_pairs_removed': self_pairs, 'duplicate_pairs_removed': len(valid) - len(clean),
        'clean_stitch_pairs': len(clean), 'stitch_index_base': offset,
        'boundary_vertices': sum(len(loop) for loops in boundaries for loop in loops),
    }
    return uv_by_vertex, owner, boundaries, clean, stats


def layout(uv, boundaries):
    """Keep the original paper layout; apply one shared similarity for display."""
    points = [uv[i] for loops in boundaries for loop in loops for i in loop]
    xmin, xmax = min(p[0] for p in points), max(p[0] for p in points)
    ymin, ymax = min(p[1] for p in points), max(p[1] for p in points)
    scale = min(1080 / (xmax - xmin), 726 / (ymax - ymin))
    left = (WIDTH - (xmax - xmin) * scale) / 2
    top = 143 + (726 - (ymax - ymin) * scale) / 2
    return {i: (left + (x - xmin) * scale, top + (ymax - y) * scale)
            for i, (x, y) in uv.items()}


def sample_stitches(clean, owner, positions, per_pair):
    groups = defaultdict(list)
    for a, b in clean:
        ga, gb = owner[a], owner[b]
        if ga > gb:
            a, b, ga, gb = b, a, gb, ga
        groups[(ga, gb)].append((a, b))
    sampled = []
    for number, (panel_pair, pairs) in enumerate(sorted(groups.items())):
        # Spread picks along the first endpoint's longer 2-D spatial axis.
        span = [max(positions[a][k] for a, _ in pairs) -
                min(positions[a][k] for a, _ in pairs) for k in (0, 1)]
        axis = int(span[1] > span[0])
        ordered = sorted(pairs, key=lambda ab: (positions[ab[0]][axis], ab))
        count = min(per_pair, len(ordered))
        for j in range(count):
            idx = min(len(ordered) - 1, int((j + .5) * len(ordered) / count))
            sampled.append((panel_pair, number, ordered[idx]))
    return sampled, len(groups)


def panel_layers(positions, boundaries):
    shapes, labels = [], []
    for group, loops in enumerate(boundaries):
        coords = [positions[i] for loop in loops for i in loop]
        commands = []
        for loop in loops:
            commands.append('M' + ' L'.join(f'{positions[i][0]:.1f},{positions[i][1]:.1f}'
                                          for i in loop) + ' Z')
        shapes.append(f'<path class="panel" id="panel-{group + 1:02d}" '
                      f'd="{" ".join(commands)}" fill="{PALETTE[group % len(PALETTE)]}"/>')
        xmin, xmax = min(p[0] for p in coords), max(p[0] for p in coords)
        ymin, ymax = min(p[1] for p in coords), max(p[1] for p in coords)
        x, y = (xmin + xmax) / 2, (ymin + ymax) / 2
        if ymax - ymin < 28:
            y = ymin - 15
            labels.append(f'<path class="label-leader" d="M{x:.1f},{y + 7:.1f} '
                          f'L{x:.1f},{ymin:.1f}"/>')
        labels.append(f'<rect x="{x - 35:.1f}" y="{y - 10:.1f}" width="70" height="20" '
                      f'rx="5" fill="#ffffff" fill-opacity=".9"/>')
        labels.append(f'<text class="panel-label" x="{x:.1f}" y="{y + 4:.1f}" '
                      f'fill="#22364a" font-size="12" font-weight="600" text-anchor="middle">'
                      f'Panel {group + 1:02d}</text>')
    return '\n'.join(shapes), '\n'.join(labels)


def render_svg(positions, boundaries, sampled, stats, topology):
    shapes, labels = panel_layers(positions, boundaries)
    title = 'Discrete stitch topology' if topology else 'Sewing-pattern panels'
    subtitle = ('Real vertex pairs, sampled for legibility; all panels retain their original 2D layout.'
                if topology else '15 real panel boundaries from the garment mesh\u2019s 2D pattern coordinates.')
    if len(boundaries) != 15 and not topology:
        subtitle = subtitle.replace('15 real', f'{len(boundaries)} real')
    metadata = {**stats, 'source': 'GarmageSet / Style3D-exported OBJ and paired pattern JSON',
                'layout': 'original vt layout; uniform display scale, translation and y-axis reversal only',
                'visual_stitch_links': len(sampled) if topology else 0,
                'sampling': 'up to two real pairs per panel-pair; full cleaned relation used for statistics',
                'mesh_origin': 'raw OBJ already contains faces; no JSON retriangulation'}
    links = []
    if topology:
        for (ga, gb), number, (a, b) in sampled:
            x1, y1 = positions[a]
            x2, y2 = positions[b]
            dx, dy = x2 - x1, y2 - y1
            length = math.hypot(dx, dy)
            bend = min(38, max(9, length * .13))
            nx, ny = (-dy / length, dx / length) if length else (0, 1)
            if ga == gb:
                bend = max(bend, 16)
            cx, cy = (x1 + x2) / 2 + nx * bend, (y1 + y2) / 2 + ny * bend
            color = LINK_COLORS[number % len(LINK_COLORS)]
            links.append(f'<g class="stitch" stroke="{color}" fill="{color}">'
                         f'<path d="M{x1:.1f},{y1:.1f} Q{cx:.1f},{cy:.1f} {x2:.1f},{y2:.1f}" '
                         f'fill="none" stroke-width="1.3" stroke-opacity=".55"/>'
                         f'<circle cx="{x1:.1f}" cy="{y1:.1f}" r="2.2" stroke="none" fill-opacity=".88"/>'
                         f'<circle cx="{x2:.1f}" cy="{y2:.1f}" r="2.2" stroke="none" fill-opacity=".88"/></g>')
    footer = (f'{stats["raw_l_records"]:,} source records  /  {stats["clean_stitch_pairs"]:,} clean pairs'
              f'  /  {len(sampled)} links shown' if topology else
              f'{stats["panels"]} panels  /  {stats["vertices"]:,} source vertices'
              f'  /  {stats["faces"]:,} existing triangle faces')
    note = ('Colors distinguish panel-pair groups; colors may repeat. Endpoints are real paired vertices.'
            if topology else 'Boundary geometry is preserved. Panel numbers are display labels, not semantic classes.')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">
<title id="title">{title}</title>
<desc id="desc">{escape(subtitle)} {escape(footer)}. {escape(note)}</desc>
<metadata>{escape(json.dumps(metadata, sort_keys=True))}</metadata>
<style>
text {{font-family: DejaVu Sans, Arial, sans-serif; fill:#22364a}}
.panel {{stroke:#53677b;stroke-width:1.25;stroke-linejoin:round;fill-rule:evenodd}}
.panel-label {{font-size:12px;font-weight:600;text-anchor:middle}}
.label-leader {{stroke:#65788b;stroke-width:1;fill:none}}
.stitch path {{fill:none;stroke-width:1.3;stroke-opacity:.55}}
.stitch circle {{stroke:none;fill-opacity:.88}}
</style>
<rect width="1200" height="960" rx="20" fill="#f7f9fc"/>
<text x="60" y="47" font-size="12" font-weight="700" letter-spacing="2" fill="#65788b">DATASET CONSTRUCTION</text>
<text x="60" y="86" font-size="29" font-weight="700">{title}</text>
<text x="60" y="116" font-size="14">{escape(subtitle)}</text>
<g id="panels">{shapes}</g>
<g id="sampled-stitches">{' '.join(links)}</g>
<g id="panel-labels">{labels}</g>
<path d="M60,887 H1140" stroke="#dce3ec"/>
<text x="60" y="914" font-size="15" font-weight="600">{escape(footer)}</text>
<text x="60" y="938" font-size="12">{escape(note)}</text>
</svg>
'''


def write_readme(directory, sample_id, stats, shown):
    if not all(c.isalnum() or c in '_-' for c in sample_id):
        raise ValueError('Use a sample identifier, not a filesystem path.')
    text = f'''# Real garment panels and stitch topology

These SVGs visualize GarmageSet sample `{sample_id}`. The paired raw OBJ
identifies its exporter as **Style3D V7.1.1089**. Source assets remain subject
to the upstream GarmageSet terms; this directory does not relicense them.

## Source and statistics

- Raw source: `GarmageSet/raw/{sample_id[:2]}/{sample_id}.obj`.
- Paired paper-pattern annotation: `GarmageSet/patterns/{sample_id}.json`.
- {stats['panels']} OBJ panel groups, matched by ID to {stats['panels']} JSON panels.
- {stats['vertices']:,} 3D vertices, {stats['vt']:,} 2D `vt` coordinates,
  {stats['faces']:,} faces ({stats['triangle_faces']:,} triangles).
- {stats['pattern_stitches']} JSON stitches describe paper-edge segments, not individual vertex pairs.
- {stats['raw_l_records']:,} raw OBJ `l` pair records; {stats['stitch_index_base']}-based stitch indices.
- Remove {stats['invalid_pairs_removed']} invalid pairs, {stats['self_pairs_removed']} self-pairs,
  and {stats['duplicate_pairs_removed']} repeated unordered pairs: **{stats['clean_stitch_pairs']:,} clean vertex pairs**.

## Geometry and display

`sewing_pattern.svg` follows the actual per-panel mesh boundary edges in the
OBJ's `vt` coordinates. It does not replace the outlines with stylized shapes.
Panel 01\u2013{stats['panels']:02d} follow the OBJ group order. Display labels omit original
panel UUIDs and original-language part labels.

Both SVGs use the **same original 2D layout** and one common uniform scale,
translation, and screen-axis reversal. No panel-wise scaling, rotation,
repacking, smoothing, or contour simplification is applied. Coordinates are
rounded to 0.1 display pixels in the SVG output.

`stitch_topology.svg` shows **{shown} real vertex pairs**: up to two spatially
spread samples from each unordered panel-pair group, including within-panel
seams. Curves are visual connectors, not physical seam paths. Their endpoints
are the actual paired `vt` positions. Colors distinguish panel-pair groups
and may repeat. Sampling is only for readability; all **{stats['clean_stitch_pairs']:,}** cleaned
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
python tools/render_dataset_pipeline_assets.py \\
  --obj INPUT.obj --pattern INPUT.json \\
  --output-dir docs/assets/dataset/dress_{sample_id} \\
  --sample-id {sample_id} --stitch-index-base {stats['stitch_index_base']}
```

The generator uses only the Python standard library and requires no GUI.
It validates JSON/OBJ panel identity, closed panel boundaries, and stitch
indexing, and parses both output SVGs as XML before reporting their size
and element counts. It reads source inputs without modifying them.
'''
    (directory / 'README.md').write_text(text, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--obj', type=Path, required=True)
    parser.add_argument('--pattern', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--sample-id')
    parser.add_argument('--stitch-index-base', choices=['auto', '0', '1'], default='auto')
    args = parser.parse_args()
    uv, owner, boundaries, clean, stats = load_geometry(args.obj, args.pattern, args.stitch_index_base)
    positions = layout(uv, boundaries)
    sampled, panel_pairs = sample_stitches(clean, owner, positions, per_pair=2)
    stats['panel_pair_groups'] = panel_pairs
    assert all(tuple(sorted(pair)) in set(clean) for _, _, pair in sampled)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, topology in [('sewing_pattern.svg', False), ('stitch_topology.svg', True)]:
        svg = render_svg(positions, boundaries, sampled, stats, topology)
        root = ET.fromstring(svg)
        path = args.output_dir / name
        path.write_text(svg, encoding='utf-8')
        print(json.dumps({'file': name, 'width': WIDTH, 'height': HEIGHT,
                          'elements': len(list(root.iter())), 'bytes': path.stat().st_size}))
    write_readme(args.output_dir, args.sample_id or args.obj.stem, stats, len(sampled))
    print(json.dumps({**stats, 'shown_stitch_links': len(sampled)}, sort_keys=True))


if __name__ == '__main__':
    main()
