# Garment-to-Body Alignment

Fine-grained semantics identify a garment vertex's functional role, while structural fields describe its continuous position relative to garment anchors. Alignment combines these complementary cues: semantics identify compatible anatomical support, structural coordinates distinguish positions within that support, and geometry selects the final body-surface point.

Related: [Evaluation protocol and Table 3](evaluation_protocol.md).

## 1. Inputs and alignment settings

The inputs are a garment triangle mesh, its garment category, and an SMPL-X body triangle mesh. The learned garment cues are predicted part semantics and four predicted structural fields. The output is the aligned garment mesh.

| Setting | Geometry and garment category | Predicted semantics | Predicted structural fields |
|---|:---:|:---:|:---:|
| Geo.+Cat. | Yes | No | No |
| +Sem. | Yes | Yes | No |
| +Fields | Yes | Yes | Yes |

The network receives coordinates, normals, and uniform RGB. Panel identifiers, stitch information, semantic colors, and ground-truth structural fields are not inference inputs. Alignment hyperparameters are selected on the validation set and fixed before test evaluation.

## 2. Structural fields: from supervision to alignment

Four anchor sets correspond to neckline, waistline, hemline, and cuff openings. The two cuff openings are merged into one set, preserving left–right symmetry under garment flipping.

Distances to an anchor are computed by multi-source Dijkstra on the mesh graph, with edge lengths as weights. Each valid channel is normalized by the 99th percentile of its finite distances and clipped to $[0,1]$. Absent anchors, unreachable vertices, and invalid normalization scales are excluded by the validity mask. A valid field extends across the anchor's reachable component rather than being restricted to its associated semantic label.

The shared Utonia-pretrained PT-v3m3 backbone produces 54-dimensional features. A linear 54-to-12 head predicts semantics, and a 54-to-27-to-4 MLP with GELU and sigmoid predicts structural fields. Structural L1 supervision gives weight 3 to vertices within two mesh hops of a ground-truth semantic interface and weight 1 elsewhere ($H=2$, $\lambda_b=2$, $\lambda_s=1$).

Mesh topology enters through the geodesic supervision. At inference, the network predicts the learned representation from surface inputs without requiring the annotation anchors or their geodesic targets.

| Channel | Anchor-relative representation | Role in alignment |
|---|---|---|
| Neck | Distance from neckline anchors | Match relative position around the posed neck ring |
| Waist | Distance from waistline anchors | Match relative position around the Spine1 waist band |
| Cuff | Distance from the union of cuff anchors | Reorient to the shoulder-to-wrist coordinate before matching |
| Hem | Distance from hemline anchors | Minimum-clearance control rather than anatomical attraction; the field and residual have distinct roles (Section 6) |

## 3. Body-side anatomical coordinates

SMPL-X joints recovered from the current body vertices define anatomical coordinates. Each arm coordinate increases from shoulder (0), through elbow (0.5), to wrist (1). Left/right arm assignment uses linear-blend-skinning (LBS) confidence rather than the sign of a world-coordinate axis.

For neckline and waistline, local coordinates increase with distance from the posed neck ring and Spine1 waist band. The LBS-based confidence identifies anatomically relevant body support.

For point $x$ on body triangle $(a,b,c)$ with barycentric weights $(\alpha,\beta,\chi)$, interpolate the coordinate and confidence:

$$
\tau_r(x)=\alpha\tau_r(b_a)+\beta\tau_r(b_b)+\chi\tau_r(b_c),
\qquad
\kappa_r(x)=\alpha\kappa_r(b_a)+\beta\kappa_r(b_b)+\chi\kappa_r(b_c).
$$

This provides continuous anatomical attributes at the exact surface point used for matching.

## 4. Coarse placement and semantic support

Category-dependent coarse registration places the garment in a T-pose configuration. Semantic local adjustments address structurally important regions such as the neckline, waist, and sleeves.

| Predicted garment region | Anatomical support |
|---|---|
| Upper-body regions, including body front/back | Torso |
| Lower regions, including lower front/back | Lower body |
| Collar | Neck region |
| Waist | Waist band |
| Sleeve/cuff | Corresponding arm |

Semantics constrain anatomical support rather than imposing a one-to-one correspondence between the 12 garment labels and body labels.

For garment vertex $v_i$, geometric retrieval and anatomical support restriction yield nearby candidate body triangles $C_i$. For each candidate $f_j^B$, calculate

$$
x_{ij}=\operatorname*{argmin}_{x\in f_j^B}\|v_i-x\|_2.
$$

The closest-point calculation is exact within each retrieved triangle. Retaining its face index and barycentric coordinates permits anatomical attributes to be evaluated at that same point.

## 5. Structural matching within anatomical support

A semantic region alone cannot distinguish all relative positions within it. For example, sleeve/cuff support identifies the arm, but does not determine the appropriate shoulder-to-wrist position. Structural matching supplies this additional coordinate.

For neckline and waistline, use

$$
\gamma_i^r=\hat s_i^r,\qquad r\in\{\mathrm{neck},\mathrm{waist}\}.
$$

For cuff, let $P_{95}$ be the 95th percentile of predicted cuff-field values within predicted sleeve/cuff support. Reverse the coordinate to match the body arm direction:

$$
\gamma_i^{\mathrm{cuff}}=
1-\operatorname{clip}\left(\frac{\hat s_i^{\mathrm{cuff}}}{P_{95}},0,1\right).
$$

The geodesic target is zero at the cuff anchor, whereas the body arm coordinate increases toward the wrist; the reversal aligns their orientations.

Retain candidates satisfying both coordinate compatibility and anatomical confidence:

$$
C_i^{\mathrm{str}}=
\left\{j\in C_i:
|\gamma_i^r-\tau_r(x_{ij})|\le\epsilon_r,\quad
\kappa_r(x_{ij})\ge\eta_r\right\}.
$$

| Region | Structural threshold $\epsilon_r$ | Confidence threshold $\eta_r$ |
|---|---:|---:|
| Neckline | 0.20 | 0.05 |
| Waistline | 0.20 | 0.05 |
| Cuff | 0.18 | 0.05 |

Select the Euclidean-nearest surviving point:

$$
j_i^*=\operatorname*{argmin}_{j\in C_i^{\mathrm{str}}}\|v_i-x_{ij}\|_2.
$$

If the filtered set is empty, fall back to the anatomical or geometric correspondence. This retains geometry as the final selection criterion while using structural coordinates to reject anatomically inconsistent matches.

## 6. Hem minimum-clearance constraint

Loose hems require a different constraint from neckline, waistline, and cuff attraction. Pulling all hem vertices toward the body would discourage the clearance needed by loose garments. Hem alignment uses the predicted Hem field to localize and weight a one-sided minimum-clearance update.

### Predicted-field region and weights

Let $\hat s_i^{\mathrm{hem}}\in[0,1]$ be the predicted Hem value, and let $S_{\mathrm{hem}}$ denote a compatible support selected from predicted garment semantics. For a field-band radius $r_{\mathrm{hem}}>0$, define the active neighborhood

$$
\Omega_{\mathrm{hem}}=
\left\{i\in S_{\mathrm{hem}}:
\hat s_i^{\mathrm{hem}}<r_{\mathrm{hem}}\right\}.
$$

Low predicted values indicate proximity to the hem anchor in the learned geodesic representation. Thus the active region is selected by structural position rather than by a global height cutoff. Restricting it to compatible predicted semantic support prevents unrelated regions from being selected solely because of a low Hem prediction.

Assign a smoothly decreasing weight

$$
w_i^{\mathrm{hem}}=
\begin{cases}
\left(1-\dfrac{\hat s_i^{\mathrm{hem}}}{r_{\mathrm{hem}}}\right)^p,
&i\in\Omega_{\mathrm{hem}},\\
0,&\text{otherwise},
\end{cases}
\qquad p>0.
$$

This concentrates the correction near the predicted hem and reduces its strength toward the edge of the active band.

### Why the Hem field and clearance residual are separate

The predicted Hem field answers **where the garment boundary is**: it selects a narrow, topology-aware neighborhood around the predicted hem and assigns a confidence-like falloff within that neighborhood. It does not decide the direction or magnitude of the geometric correction.

The signed-distance residual answers **whether the selected boundary needs correction**. A selected hem vertex is moved only when it penetrates the body or violates the category-dependent minimum clearance. A selected vertex that already satisfies the clearance remains unchanged. This separation is essential for loose garments: using Hem as an attraction target would pull valid loose boundaries toward the body, whereas the one-sided residual can only preserve or increase clearance.

### Clearance residual

For each active vertex, calculate

$$
\xi_i^{\mathrm{hem}}=
\left[\delta_{\mathrm{cat}}-d_{\mathrm{signed}}(v_i,\mathcal B)\right]_+.
$$

The signed distance is positive outside the body and negative for penetration. The category-specific clearances are:

| Category | Minimum clearance |
|---|---:|
| Dresses | 18 mm |
| Tops | 12 mm |
| Pants | 8 mm |
| Skirts | 18 mm |

A positive residual identifies a penetrating vertex or an exterior vertex with insufficient clearance. A vertex already satisfying the minimum clearance has zero residual.

### Weighted outward update

Let $n_i$ be the outward normal at the queried body-surface point. With update strength $\alpha\in[0,1]$ and displacement cap $\Delta_{\max}>0$, the local update is

$$
v_i^{t+1}=
v_i^t+
\alpha\,w_i^{\mathrm{hem}}\,
\min\left(\xi_i^{\mathrm{hem}},\Delta_{\max}\right)n_i.
$$

Surface queries and residuals are recomputed at the current vertex positions for successive updates. The predicted field determines where the constraint acts and how strongly it acts; the geometric residual determines whether an outward correction is needed. Vertices outside the active band, or already satisfying clearance, receive zero displacement from this constraint. Since the residual is nonnegative, the update introduces no inward attraction.

Here $r_{\mathrm{hem}}$, $p$, $\alpha$, and $\Delta_{\max}$ are the neighborhood, falloff, strength, and displacement parameters of the predicted-input update. The category clearances are 18/12/8/18 mm for dresses/tops/pants/skirts, respectively.

## 7. Local garment deformation

The field-driven local-update operator connects the selected surface correspondence to garment motion. Its inputs are predicted semantics and predicted structural fields; the body-side quantities are obtained from the SMPL-X surface queries. The predicted field values enter the regional weighting and correspondence rules directly.

### Attraction-region weights

For region $r\in\{\mathrm{neck},\mathrm{waist},\mathrm{cuff}\}$, let $S_r$ be the predicted semantic support. The predicted anchor-distance channel defines the field-localized weight

$$
w_i^r=
\mathbf1[i\in S_r]\,
\left[1-\frac{\hat s_i^r}{\rho_r}\right]_+^{p_r},
\qquad \rho_r>0,\quad p_r>0.
$$

This weight uses the anchor-distance prediction $\hat s_i^r$. It is distinct from the body-compatible coordinate $\gamma_i^r$ used for candidate filtering; in particular, cuff matching reverses the field direction as described in Section 5.

### Target, capped displacement, and iteration

At iteration $t$, query the selected surface point $x_i^{*,t}$ and its outward normal $n_i^t$. Let $c_r\ge0$ denote an outward surface offset. Define

$$
z_i^t=x_i^{*,t}+c_r n_i^t.
$$

The displacement from the current vertex to this target is

$$
\mathbf{u}_i^t=z_i^t-v_i^t.
$$

The local weighted update is

$$
\Delta v_i^t=
\alpha_r w_i^r
\min\left(1,\frac{\ell_r}
{\max(\|\mathbf{u}_i^t\|_2,\varepsilon)}\right)\mathbf{u}_i^t,
\qquad
v_i^{t+1}=v_i^t+\Delta v_i^t,
$$

where $\alpha_r\in[0,1]$ is the update strength, $\ell_r>0$ the per-step displacement cap, and $\varepsilon>0$ a numerical stabilizer. Setting $c_r=0$ makes the queried surface point itself the target. An outward offset allows a positive garment–body clearance.

The surface correspondence is recomputed at the current vertex positions for successive iterations. A finite iteration budget $T_r$ bounds the process, with early termination when no active vertex has a displacement exceeding a stopping tolerance. Vertices with zero regional weight remain unchanged by that regional update.

The correspondence remains an exact point on a retrieved body triangle; the offset affects the subsequent deformation target. These updates preserve mesh connectivity but do not enforce exact edge-length preservation or solve a global ARAP or Laplacian deformation energy.

### Geometric safety correction

An anatomically compatible target may lie behind a nearer body surface. An additional geometric query addresses residual penetration independently of the structural candidate filter. For a penetrating vertex, the capped outward-normal step is

$$
v_i\leftarrow v_i+
\min\left(
[-d_{\mathrm{signed}}(v_i,\mathcal B)]_+,\ell_{\mathrm{safe}}
\right)n_i^{\mathrm{geo}}.
$$

This correction responds to penetration, not structural-coordinate mismatch. The safety pass stops when no penetrating vertex exceeds the numerical tolerance or when its iteration budget is reached.

The neighborhood radii, offsets, strengths, caps, and iteration budgets control the support and magnitude of the local deformation. The coordinate conversions and matching thresholds are given in Section 5, and the category-specific hem clearances in Section 6. Cross-setting cue usage is detailed below; numerical-configuration reporting is addressed in the [evaluation protocol](evaluation_protocol.md#2-compared-settings).

## 8. Predicted-cue progression across alignment settings

The three settings differ in the garment information available to the alignment stages. In particular, the field-dependent weights in Sections 6–7 belong to the +Fields refinement, not to the two settings without structural predictions.

| Setting | Region selection | Local weighting | Correspondence selection |
|---|---|---|---|
| Geo.+Cat. | Geometry and category-dependent coarse placement; no predicted part masks | No structural-field weighting | Geometry-based surface matching, without predicted semantic or structural filtering |
| +Sem. | Predicted part labels identify regions for semantic local adjustment | Semantic local-adjustment rules; no structural-field falloff | Restrict candidates to compatible semantic/anatomical support; no structural-coordinate mismatch test |
| +Fields | Predicted semantic support intersected with the predicted field band | Predicted-field falloff $w_i^r$ in Section 7 and $w_i^{\mathrm{hem}}$ in Section 6 | Apply semantic/anatomical support and structural-coordinate filtering, then choose the nearest surviving surface point; use the stated fallback if necessary |

Thus Geo.+Cat. and +Sem. do not need to evaluate $w_i^r$ from an unavailable field. Removing structural refinement means omitting its field-band localization, field-dependent weights, and coordinate-compatibility test; it does not mean inserting a zero-valued structural prediction into those formulas. Semantic local adjustments and the subsequent field-driven refinement are distinct stages.

All settings use the same held-out cases, body assets, evaluation regions, and aggregation, with hyperparameters selected on validation and fixed before test evaluation. The progression measures how each predicted representation contributes to alignment: semantics supply discrete anatomical support, and structural fields supply continuous within-region coordinates and localized weights. Field filtering, weighting, and Hem localization are deterministic uses of the predicted structural values; they add no learned parameters and never access ground-truth fields at inference.

## 9. Algorithm outline: +Fields

    Inputs: garment mesh, category, SMPL-X body,
            predicted semantics and four predicted structural fields

    Construct body anatomical coordinates and LBS confidences
    Perform category-dependent coarse T-pose registration
    Apply semantic local adjustments

    For each active attraction region (neckline, waistline, cuff):
        Construct regional weights from the predicted anchor-distance field
        Convert predicted fields to body-compatible matching coordinates
        For each local update iteration:
            Query nearby triangles on compatible anatomical support
            Compute closest points and interpolated body attributes
            Filter candidates by coordinate mismatch and confidence
            Select the Euclidean-nearest surviving point
            If the filtered set is empty, use anatomical/geometric fallback
            Form the surface-offset target
            Apply the weighted, capped displacement
            Stop early when all active displacements are below tolerance
        Apply geometric safety correction for residual penetration

    Select the hem band and weights from the predicted Hem field
    Apply the weighted, pushout-only minimum-clearance update
    Return the aligned garment mesh

Table 3 uses the shared evaluation regions and metric definitions in the evaluation protocol.

