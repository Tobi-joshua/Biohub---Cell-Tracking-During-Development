"""Anisotropy-aware cell centroid detection (v1.1)."""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np
from scipy.ndimage import gaussian_filter, maximum_filter
from scipy.spatial import cKDTree

from biohub.config import Config

try:
    from skimage.feature import peak_local_max
    from skimage.filters import threshold_otsu
except ImportError:
    peak_local_max = None
    threshold_otsu = None


def block_mean_xy(vol: np.ndarray, factor: int) -> np.ndarray:
    """Average-pool XY while preserving Z. Makes the grid ~isotropic in microns."""
    z, y, x = vol.shape
    y2, x2 = (y // factor) * factor, (x // factor) * factor
    arr = vol[:, :y2, :x2].astype(np.float32, copy=False)
    return arr.reshape(z, y2 // factor, factor, x2 // factor, factor).mean(axis=(2, 4))


def robust_threshold(
    sm: np.ndarray,
    cfg: Config,
    thresh_rel: Optional[float] = None,
) -> Tuple[float, float, float]:
    """Otsu with a relative-rise floor; optional per-pass threshold override."""
    alpha = cfg.thresh_rel if thresh_rel is None else float(thresh_rel)
    bg = float(np.median(sm))
    hi = float(np.percentile(sm, cfg.thresh_hi_percentile))
    dyn = max(hi - bg, 1e-6)
    rel_thr = bg + alpha * dyn
    try:
        otsu = float(threshold_otsu(sm)) if threshold_otsu else float(np.percentile(sm, 96.0))
    except Exception:
        otsu = float(np.percentile(sm, 96.0))
    return max(otsu, rel_thr), bg, dyn


def adaptive_thresh_rel(cfg: Config, prev_count: Optional[int], n_detected: int) -> float:
    """Tighten threshold when a frame suddenly exceeds the previous count."""
    rel = cfg.thresh_rel
    if not cfg.use_adaptive_frame_threshold or prev_count is None or prev_count < 8:
        return rel
    if n_detected > int(prev_count * cfg.max_frame_count_mult):
        rel += cfg.adaptive_overcount_penalty
    return rel


def _fallback_peaks(sm: np.ndarray, threshold_abs: float, min_distance: int) -> np.ndarray:
    size = 2 * min_distance + 1
    mx = maximum_filter(sm, size=(size, size, size), mode="nearest")
    mask = (sm >= mx) & (sm > threshold_abs)
    coords = np.argwhere(mask)
    if coords.size == 0:
        return coords.astype(np.int32)
    vals = sm[coords[:, 0], coords[:, 1], coords[:, 2]]
    return coords[np.argsort(-vals)].astype(np.int32)


def _find_peaks(sm: np.ndarray, threshold_abs: float, min_distance: int) -> np.ndarray:
    if peak_local_max is not None:
        return peak_local_max(
            sm,
            min_distance=min_distance,
            threshold_abs=threshold_abs,
            exclude_border=False,
        ).astype(np.int32)
    return _fallback_peaks(sm, threshold_abs, min_distance)


def refine_centroid(
    vol: np.ndarray,
    approx_zyx: np.ndarray,
    cfg: Config,
) -> Tuple[np.ndarray, float]:
    """Intensity-weighted centroid in a local neighborhood."""
    zc, yc, xc = [int(round(v)) for v in approx_zyx]
    z0 = max(0, zc - cfg.refine_radius_z)
    z1 = min(vol.shape[0], zc + cfg.refine_radius_z + 1)
    y0 = max(0, yc - cfg.refine_radius_yx)
    y1 = min(vol.shape[1], yc + cfg.refine_radius_yx + 1)
    x0 = max(0, xc - cfg.refine_radius_yx)
    x1 = min(vol.shape[2], xc + cfg.refine_radius_yx + 1)
    crop = vol[z0:z1, y0:y1, x0:x1].astype(np.float32, copy=False)
    if crop.size == 0:
        return approx_zyx.astype(np.float64), 0.0

    bg = float(np.percentile(crop, 20.0))
    weights = np.clip(crop - bg, 0.0, None)
    total = float(weights.sum())
    if total <= 1e-6:
        loc = np.unravel_index(int(np.argmax(crop)), crop.shape)
        return np.array([z0 + loc[0], y0 + loc[1], x0 + loc[2]], dtype=np.float64), float(crop[loc])

    zz, yy, xx = np.indices(crop.shape)
    refined = np.array(
        [
            z0 + float((zz * weights).sum() / total),
            y0 + float((yy * weights).sum() / total),
            x0 + float((xx * weights).sum() / total),
        ],
        dtype=np.float64,
    )
    return refined, float(weights.max())


def sample_intensity(vol: np.ndarray, coords: np.ndarray) -> np.ndarray:
    """Max intensity in a 3x3x3 neighborhood at each centroid."""
    if len(coords) == 0:
        return np.empty((0,), dtype=np.float32)
    out = np.empty(len(coords), dtype=np.float32)
    z_dim, y_dim, x_dim = vol.shape
    for i, (z, y, x) in enumerate(coords):
        zc, yc, xc = int(round(z)), int(round(y)), int(round(x))
        z0, z1 = max(0, zc - 1), min(z_dim, zc + 2)
        y0, y1 = max(0, yc - 1), min(y_dim, yc + 2)
        x0, x1 = max(0, xc - 1), min(x_dim, xc + 2)
        out[i] = float(vol[z0:z1, y0:y1, x0:x1].max())
    return out


def physical_nms(
    coords_vox: np.ndarray,
    scores: np.ndarray,
    radius_um: float,
    scale: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    if len(coords_vox) <= 1:
        return coords_vox, scores
    pts = coords_vox.astype(np.float64) * scale[None, :]
    order = np.argsort(-scores)
    tree = cKDTree(pts)
    suppressed = np.zeros(len(coords_vox), dtype=bool)
    keep = []
    for i in order:
        if suppressed[i]:
            continue
        keep.append(i)
        for j in tree.query_ball_point(pts[i], r=radius_um):
            suppressed[j] = True
    keep = np.array(keep, dtype=np.int64)
    return coords_vox[keep], scores[keep]


def _map_ds_to_full(coords_ds: np.ndarray, xy_ds: int) -> np.ndarray:
    approx = coords_ds.astype(np.float64)
    approx[:, 1] = approx[:, 1] * xy_ds + (xy_ds - 1) / 2.0
    approx[:, 2] = approx[:, 2] * xy_ds + (xy_ds - 1) / 2.0
    return approx


def _merge_peak_sets(
    primary: np.ndarray,
    secondary: np.ndarray,
    sm: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    if len(primary) == 0 and len(secondary) == 0:
        return primary, np.empty((0,), dtype=np.float32)
    if len(primary) == 0:
        coords = secondary
    elif len(secondary) == 0:
        coords = primary
    else:
        coords = np.vstack([primary, secondary])
        coords = np.unique(coords, axis=0)
    scores = sm[coords[:, 0], coords[:, 1], coords[:, 2]].astype(np.float32)
    return coords, scores


def detect_cells(
    vol: np.ndarray,
    cfg: Config,
    prev_count: Optional[int] = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Detect cell centroids in one 3D frame.

    Returns integer (z, y, x) coordinates, detector scores, and sampled intensities.
    """
    z_dim, y_dim, x_dim = vol.shape
    ds = block_mean_xy(vol, cfg.xy_ds)
    sm = gaussian_filter(ds, sigma=cfg.smooth_sigma, mode="nearest")

    thresh_rel = adaptive_thresh_rel(cfg, prev_count, n_detected=0)
    threshold_abs, bg, dyn = robust_threshold(sm, cfg, thresh_rel=thresh_rel)

    coords_primary = _find_peaks(sm, threshold_abs, cfg.min_peak_dist)
    coords_dense = np.empty((0, 3), dtype=np.int32)
    if cfg.use_dense_cluster_pass:
        dense_rel = max(0.08, thresh_rel + cfg.dense_thresh_rel_delta)
        dense_thr, _, _ = robust_threshold(sm, cfg, thresh_rel=dense_rel)
        coords_dense = _find_peaks(sm, dense_thr, cfg.dense_min_peak_dist)

    coords_ds, peak_scores = _merge_peak_sets(coords_primary, coords_dense, sm)
    if coords_ds.size == 0:
        flat = np.argpartition(sm.ravel(), -3)[-3:]
        coords_ds = np.array(np.unravel_index(flat, sm.shape)).T.astype(np.int32)
        peak_scores = sm[coords_ds[:, 0], coords_ds[:, 1], coords_ds[:, 2]].astype(np.float32)

    rel_contrast = (peak_scores - bg) / max(dyn, 1e-6)
    keep = rel_contrast >= cfg.min_rel_contrast
    coords_ds, peak_scores = coords_ds[keep], peak_scores[keep]
    if len(coords_ds) == 0:
        return (
            np.empty((0, 3), dtype=np.int32),
            np.empty((0,), dtype=np.float32),
            np.empty((0,), dtype=np.float32),
        )

    approx = _map_ds_to_full(coords_ds, cfg.xy_ds)
    refined, refined_scores = [], []
    for a, s in zip(approx, peak_scores):
        r, rs = refine_centroid(vol, a, cfg)
        refined.append(r)
        refined_scores.append(max(float(s), rs))
    coords = np.vstack(refined)
    scores = np.array(refined_scores, dtype=np.float32)

    # Hard minimum Z for weak detections (reduces bottom-slice artifacts).
    if cfg.min_z_hard > 0 and len(coords):
        z_floor_score = float(np.quantile(scores, 0.85)) if len(scores) > 8 else np.inf
        keep = (coords[:, 0] >= cfg.min_z_hard) | (scores >= z_floor_score)
        coords, scores = coords[keep], scores[keep]

    cz, cy, cx = coords[:, 0], coords[:, 1], coords[:, 2]
    border = (
        (cz <= cfg.border_z)
        | (cz >= z_dim - 1 - cfg.border_z)
        | (cy <= cfg.border_yx)
        | (cy >= y_dim - 1 - cfg.border_yx)
        | (cx <= cfg.border_yx)
        | (cx >= x_dim - 1 - cfg.border_yx)
    )
    floor = float(np.quantile(scores, cfg.border_keep_quantile)) if len(scores) > 8 else -np.inf
    keep = (~border) | (scores >= floor)
    coords, scores = coords[keep], scores[keep]

    coords, scores = physical_nms(coords, scores, cfg.nms_radius_um, cfg.scale_array)
    if cfg.use_dense_cluster_pass and len(coords) > 1:
        coords, scores = physical_nms(coords, scores, cfg.nms_dense_radius_um, cfg.scale_array)

    if prev_count is not None and prev_count >= 8:
        cap = int(prev_count * cfg.max_frame_count_mult + cfg.max_frame_count_add)
        if len(coords) > cap:
            order = np.argsort(-scores)[:cap]
            coords, scores = coords[order], scores[order]

    if len(coords) > cfg.max_nodes_per_frame:
        order = np.argsort(-scores)[: cfg.max_nodes_per_frame]
        coords, scores = coords[order], scores[order]

    coords = np.rint(coords).astype(np.int32)
    coords[:, 0] = np.clip(coords[:, 0], 0, z_dim - 1)
    coords[:, 1] = np.clip(coords[:, 1], 0, y_dim - 1)
    coords[:, 2] = np.clip(coords[:, 2], 0, x_dim - 1)
    intensities = sample_intensity(vol, coords)
    return coords, scores, intensities
