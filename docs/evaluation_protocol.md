# Alignment Evaluation Protocol

This protocol defines the garment-to-body alignment comparison in Section 3.3 and Table 3. Every learned cue consumed by alignment is a model prediction. Annotation-derived structural coordinates may be used only as evaluator-side references and are never available to the alignment method.

Related: [Alignment method and predicted-field usage](alignment_method.md).

## 1. Compared settings

| Setting | Garment cues available to alignment |
|---|---|
| Geo.+Cat. | Geometry and garment category |
| +Sem. | Geometry, category, and predicted garment-part semantics |
| +Fields | Geometry, category, predicted semantics, and predicted structural fields |

Geo.+Cat. does not receive placeholder semantic or structural tensors. +Sem. adds semantic region selection and compatible anatomical support, but omits every structural-field band, falloff weight, and coordinate filter. +Fields additionally uses the predicted structural fields for regional localization, soft weighting, and coordinate-compatible correspondence. Its predicted Hem field localizes and weights the one-sided minimum-clearance constraint described in [the alignment method](alignment_method.md#6-hem-minimum-clearance-constraint).

### Numerical controls

The +Fields configuration is:

| Region | Field radius | Falloff | Strength | Step cap | Iterations | Surface offset or clearance |
|---|---:|---:|---:|---:|---:|---:|
| Neckline | 0.10 | 1.5 | 0.30 | 6 mm | 2 | 4 mm |
| Waistline | 0.10 | 1.5 | 0.30 | 6 mm | 2 | 2 mm |
| Cuff | 0.50 | 1.5 | 0.30 | 6 mm | 2 | 6 mm |
| Hem | 0.08 | 1.5 | 1.00 | 8 mm | 3 | 18/12/8/18 mm by category |

Structural correspondence retains up to 64 candidates, uses mismatch thresholds 0.20 for neckline and waistline and 0.18 for cuff, and requires anatomical confidence of at least 0.05. Up to four geometric safety-pushout iterations correct residual penetration after the anatomically filtered update.

Table 3 follows a progression of increasingly informative predicted garment cues. Semantics provide discrete anatomical support, while structural fields provide continuous localization, weighting, and coordinate compatibility. The field-dependent rules are deterministic functions of the predicted values: they introduce no additional learned parameters and do not access annotation-derived fields during alignment.

Table 2 evaluates whether the structural fields are predicted accurately, whereas Table 3 evaluates whether supplying those predictions improves downstream alignment. The gain from +Sem. to +Fields therefore measures the utility of the predicted continuous representation when consumed by its deterministic localization and matching rules.

## 2. Evaluation cases and regions

All three settings use the same held-out garment identities, garment categories, body assets, active-region cases, and failure policy. Hyperparameters are selected on validation data and frozen before test evaluation.

Evaluation regions are defined independently of the predictions consumed by alignment. This is particularly important for +Fields: using its own predicted low-field band as the scoring region would allow different settings to be evaluated on different vertices. Annotation-derived region masks and structural coordinates are therefore permitted inside the offline evaluator, but not inside any alignment setting.

A run is one garment-region case. Table 3 uses 120 attraction runs (40 each for neckline, waistline, and cuff alignment) and 40 additional Hem-clearance runs, for 160 runs from 104 unique garments. A garment may therefore contribute multiple attraction or clearance cases. Empty regions and failed fits are handled by one rule shared across settings.

## 3. Metrics

Let $q$ index a run, $V_q$ be its aligned garment vertices, and $\mathcal B_q$ the body surface. Let $\Omega_q^{r,\mathrm{eval}}$ be the fixed evaluator-side vertex set for attraction region $r$, and let $\Omega_q^{\mathrm{hem,eval}}$ be the fixed evaluator-side Hem region.

### Structural mismatch: Struct.

Let $g_{qi}^{r,\mathrm{ref}}$ be the evaluator-side garment structural coordinate. Let $x_{qi}^{\mathrm{eval}}$ be the body-surface correspondence obtained with the same evaluation query for every setting, and let $\tau_r(x)$ be the interpolated body anatomical coordinate. Then

$$
\mathrm{Struct}_q=
\frac{1}{|\Omega_q^{r,\mathrm{eval}}|}
\sum_{i\in\Omega_q^{r,\mathrm{eval}}}
\left|g_{qi}^{r,\mathrm{ref}}-\tau_r(x_{qi}^{\mathrm{eval}})\right|.
$$

Struct. is dimensionless. The reference coordinate is used only for scoring; the alignment method receives the predicted coordinate in +Fields and no structural coordinate in the other settings.

### Unsigned attraction distance: Gap

Using the same fixed attraction region and evaluation surface point,

$$
\mathrm{Gap}_q[\mathrm{mm}]=
\frac{1000}{|\Omega_q^{r,\mathrm{eval}}|}
\sum_{i\in\Omega_q^{r,\mathrm{eval}}}
\|v_{qi}-x_{qi}^{\mathrm{eval}}\|_2.
$$

The factor 1000 converts metres to millimetres. Gap measures unsigned attachment distance; signed gap visualizations are a separate diagnostic.

### Minimum-clearance violation: Hem

$$
\mathrm{Hem}_q[\mathrm{mm}]=
\frac{1000}{|\Omega_q^{\mathrm{hem,eval}}|}
\sum_{i\in\Omega_q^{\mathrm{hem,eval}}}
\left[\delta_{\mathrm{cat}(q)}-
d_{\mathrm{signed}}(v_{qi},\mathcal B_q)\right]_+.
$$

The minimum clearances are 18 mm for dresses, 12 mm for tops, 8 mm for pants, and 18 mm for skirts. A vertex satisfying the clearance contributes zero. The evaluator-side Hem region is fixed across settings; it is distinct from the predicted Hem band that controls the +Fields update.

### Full-garment penetration: Pen.

$$
\mathrm{Pen}_q[\%]=
\frac{100}{|V_q|}
\sum_{i\in V_q}
\mathbf1\!\left[d_{\mathrm{signed}}(v_{qi},\mathcal B_q)<0\right].
$$

Pen. is computed over the full garment rather than only the active region. A vertex contributes exactly when its signed gap is negative, matching the definition used in the paper. The same signed-distance implementation is used for all settings.

## 4. Aggregation

Each metric is first averaged over eligible vertices within a run and then averaged over runs with equal weight:

$$
\overline M=
\frac{1}{|\mathcal R_M|}
\sum_{q\in\mathcal R_M}M_q.
$$

Attraction runs contribute Struct. and Gap, Hem runs contribute Hem, and all completed runs contribute Pen. Because one garment may appear in several region-specific runs, confidence intervals or statistical resampling should cluster by garment identity. Any category macro-averaging must be stated explicitly.

## 5. Table 3

Lower is better for all metrics. Struct. and Gap use the 120 attraction runs, Hem uses the 40 Hem-clearance runs, and Pen. uses all 160 runs.

| Alignment | Struct. ↓ | Gap (mm) ↓ | Hem (mm) ↓ | Pen. (%) ↓ |
|---|---:|---:|---:|---:|
| Geo.+Cat. | 0.4280 | 33.897 | 9.2533 | 32.2667 |
| +Sem. | 0.3307 | 25.812 | 5.1113 | 21.5535 |
| +Fields | **0.1261** | **14.646** | **3.0519** | **16.5071** |

