"""Anisotropy-aware cell centroid detection."""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np
from scipy.ndimage import gaussian_filter, maximum_filter
from scipy.spatial import cKDTree

from biohub.config import Config, SCALE

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


def robust_threshold(sm: np.ndarray, cfg: Config) -> Tuple[float, float, float]:
    """Otsu with a relative-rise floor."""
    bg = float(np.median(sm))
    hi = float(np.percentile(sm, cfg.thresh_hi_percentile))
    dyn = max(hi - bg, 1e-6)
    rel_thr = bg + cfg.thresh_rel * dyn
    try:
        otsu = float(threshold_otsu(sm)) if threshold_otsu else float(np.percentile(sm, 96.0))
    except Exception:
        otsu = float(np.percentile(sm, 96.0))
    return max(otsu, rel_thr), bg, dyn


def _fallback_peaks(sm: np.ndarray, threshold_abs: float, min_distance: int) -> np.ndarray:
    size = 2 * min_distance + 1
    mx = maximum_filter(sm, size=(size, size, size), mode="nearest")
    mask = (sm >= mx) & (sm > threshold_abs)
    coords = np.argwhere(mask)
    if coords.size == 0:
        return coords.astype(np.int32)
    vals = sm[coords[:, 0], coords[:, 1], coords[:, 2]]
    return coords[np.argsort(-vals)].astype(np.int32)


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


def detect_cells(
    vol: np.ndarray,
    cfg: Config,
    prev_count: Optional[int] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Detect cell centroids in one 3D frame.

    Returns integer (z, y, x) coordinates and detector scores.
    """
    z_dim, y_dim, x_dim = vol.shape
    ds = block_mean_xy(vol, cfg.xy_ds)
    sm = gaussian_filter(ds, sigma=cfg.smooth_sigma, mode="nearest")
    threshold_abs, bg, dyn = robust_threshold(sm, cfg)

    if peak_local_max is not None:
        coords_ds = peak_local_max(
            sm,
            min_distance=cfg.min_peak_dist,
            threshold_abs=threshold_abs,
            exclude_border=False,
        ).astype(np.int32)
    else:
        coords_ds = _fallback_peaks(sm, threshold_abs, cfg.min_peak_dist)

    if coords_ds.size == 0:
        flat = np.argpartition(sm.ravel(), -3)[-3:]
        coords_ds = np.array(np.unravel_index(flat, sm.shape)).T.astype(np.int32)

    peak_scores = sm[coords_ds[:, 0], coords_ds[:, 1], coords_ds[:, 2]].astype(np.float32)
    rel_contrast = (peak_scores - bg) / max(dyn, 1e-6)
    keep = rel_contrast >= cfg.min_rel_contrast
    coords_ds, peak_scores = coords_ds[keep], peak_scores[keep]
    if len(coords_ds) == 0:
        return np.empty((0, 3), dtype=np.int32), np.empty((0,), dtype=np.float32)

    approx = coords_ds.astype(np.float64)
    approx[:, 1] = approx[:, 1] * cfg.xy_ds + (cfg.xy_ds - 1) / 2.0
    approx[:, 2] = approx[:, 2] * cfg.xy_ds + (cfg.xy_ds - 1) / 2.0

    refined, refined_scores = [], []
    for a, s in zip(approx, peak_scores):
        r, rs = refine_centroid(vol, a, cfg)
        refined.append(r)
        refined_scores.append(max(float(s), rs))
    coords = np.vstack(refined)
    scores = np.array(refined_scores, dtype=np.float32)

    # Drop weak border artifacts.
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
    return coords, scores
