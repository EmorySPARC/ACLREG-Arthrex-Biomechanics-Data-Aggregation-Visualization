import math
import re
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
import tkinter as tk
from tkinter import filedialog


# =========================
# Config
# =========================

GROUP_KEYS = ["RET", "CTRL"]

GROUP_NAME_MAP = {
    "RET": "Contralateral Re-Tear UNV Limb (6m)",
    "CTRL": "ACLR Control UNV Limb (6m)",
}

COLOR_MAP = {
    "RET": "#d7191c",   
    "CTRL": "#2c7bb6",  
}

BAND_ALPHA = 0.18
LINE_WIDTH = 2.4

TRIAL_PREFERENCE = [
    "Drop jump/DJ_B 2",
    "Drop jump/DJ_B 1",
    "Drop jump/DJ_B 3",
]

N_POINTS = 101

OUT_ANGLES_PNG = "dvj_angles_contra.png"
OUT_MOMENTS_PNG = "dvj_moments_contra.png"


# =========================
# Limb Selection (per group)
# =========================
# Modes:
#   "injured"   -> injured/ACLR limb
#   "uninjured" -> contralateral limb
#   "left"      -> always left
#   "right"     -> always right
#   "both_avg"  -> average left+right (old behavior)
GROUP_LIMB_MODE: Dict[str, str] = {
    "RET": "uninjured",
    "CTRL": "uninjured",
}

# If injured limb cannot be inferred from metadata, hardcode here by subject ID.
# ID is derived from filename via parse_id_from_filename(), e.g. ACLREG_0045
MANUAL_INJURED_LIMB: Dict[str, str] = {
    # "ACLREG_0045": "L",
}


# =========================
# Panels
# =========================
ANGLES_PANELS = [
    ("Hip Angle", "Sagittal"),
    ("Hip Angle", "Frontal"),
    ("Hip Angle", "Transverse"),
    ("Knee Angle", "Sagittal"),
    ("Knee Angle", "Frontal"),
    ("Knee Angle", "Transverse"),
    ("Ankle Angle", "Sagittal"),
    ("Ankle Angle", "Frontal"),
    ("ACL Strain", ""),
]

MOMENTS_PANELS = [
    ("Hip Moment", "Sagittal"),
    ("Hip Moment", "Frontal"),
    ("Hip Moment", "Transverse"),
    ("Knee Moment", "Sagittal"),
    ("Knee Moment", "Frontal"),
    ("Knee Moment", "Transverse"),
    ("Ankle Moment", "Sagittal"),
    ("Ankle Moment", "Frontal"),
    ("GRF", "Vertical"),
]


# =========================
# Col Mapping
# =========================
ANGLE_VARS: Dict[Tuple[str, str], List[str]] = {
    ("Hip Angle", "Sagittal"):      ["Left Hip Angles_X", "Right Hip Angles_X"],
    ("Hip Angle", "Frontal"):       ["Left Hip Angles_Y", "Right Hip Angles_Y"],
    ("Hip Angle", "Transverse"):    ["Left Hip Angles_Z", "Right Hip Angles_Z"],

    ("Knee Angle", "Sagittal"):     ["Left Knee Angles_X", "Right Knee Angles_X"],
    ("Knee Angle", "Frontal"):      ["Left Knee Angles_Y", "Right Knee Angles_Y"],
    ("Knee Angle", "Transverse"):   ["Left Knee Angles_Z", "Right Knee Angles_Z"],

    ("Ankle Angle", "Sagittal"):    ["Left Ankle Angles_X", "Right Ankle Angles_X"],
    ("Ankle Angle", "Frontal"):     ["Left Ankle Angles_Y", "Right Ankle Angles_Y"],

    ("ACL Strain", ""):            ["Left Knee ACLam", "Right Knee ACLam"],
}

MOMENT_VARS: Dict[Tuple[str, str], List[str]] = {
    ("Hip Moment", "Sagittal"):     ["Left Hip Moment_X", "Right Hip Moment_X"],
    ("Hip Moment", "Frontal"):      ["Left Hip Moment_Y", "Right Hip Moment_Y"],
    ("Hip Moment", "Transverse"):   ["Left Hip Moment_Z", "Right Hip Moment_Z"],

    ("Knee Moment", "Sagittal"):    ["Left Knee Moment_X", "Right Knee Moment_X"],
    ("Knee Moment", "Frontal"):     ["Left Knee Moment_Y", "Right Knee Moment_Y"],
    ("Knee Moment", "Transverse"):  ["Left Knee Moment_Z", "Right Knee Moment_Z"],

    ("Ankle Moment", "Sagittal"):   ["Left Ankle Moment_X", "Right Ankle Moment_X"],
    ("Ankle Moment", "Frontal"):    ["Left Ankle Moment_Y", "Right Ankle Moment_Y"],
}

# GRF now left/right (BW-normalized)
GRF_VARS_LR = ["Left GRF_Z", "Right GRF_Z"]

# COM (used for lowest COM timing / shading)
COM_VAR = "Pelvis_COM_Z"


# =========================
# Directions
# =========================
DIR_ANNOT = {
    ("Hip Angle", "Sagittal", "Angles"): ("Flexion", "up"),
    ("Hip Angle", "Frontal", "Angles"): ("Adduction", "up"),
    ("Hip Angle", "Transverse", "Angles"): ("Internal Rot.", "up"),

    ("Hip Moment", "Sagittal", "Moments"): ("Flexion", "up"),
    ("Hip Moment", "Frontal", "Moments"): ("Adduction", "up"),
    ("Hip Moment", "Transverse", "Moments"): ("Internal Rot.", "up"),

    ("Knee Angle", "Sagittal", "Angles"): ("Flexion", "down"),
    ("Knee Angle", "Frontal", "Angles"): ("Abduction", "up"),
    ("Knee Angle", "Transverse", "Angles"): ("Internal Rot.", "up"),

    ("Knee Moment", "Sagittal", "Moments"): ("Flexion", "down"),
    ("Knee Moment", "Frontal", "Moments"): ("Abduction", "down"),
    ("Knee Moment", "Transverse", "Moments"): ("Internal Rot.", "up"),

    ("Ankle Angle", "Sagittal", "Angles"): ("Dorsiflexion", "up"),
    ("Ankle Angle", "Frontal", "Angles"): ("Eversion", "down"),

    ("Ankle Moment", "Sagittal", "Moments"): ("Dorsiflexion", "up"),
    ("Ankle Moment", "Frontal", "Moments"): ("Eversion", "down"),

    ("ACL Strain", "", "Angles"): ("Strain", "up"),
}

# Manual direction label positions (axes-fraction coords)
MANUAL_DIR_POS: Dict[Tuple[str, str], Tuple[float, float]] = {
    ("Hip Angle", "Sagittal"):      (0.10, 0.85),
    ("Hip Angle", "Frontal"):       (0.10, 0.85),
    ("Hip Angle", "Transverse"):    (0.10, 0.85),

    ("Knee Angle", "Sagittal"):     (0.10, 0.20),
    ("Knee Angle", "Frontal"):      (0.10, 0.20),
    ("Knee Angle", "Transverse"):   (0.10, 0.20),

    ("Ankle Angle", "Sagittal"):    (0.10, 0.20),
    ("Ankle Angle", "Frontal"):     (0.10, 0.20),
    ("Ankle Angle", "Transverse"):  (0.10, 0.20),  # not used right now

    ("Hip Moment", "Sagittal"):     (0.10, 0.85),
    ("Hip Moment", "Frontal"):      (0.10, 0.85),
    ("Hip Moment", "Transverse"):   (0.10, 0.85),

    ("Knee Moment", "Sagittal"):    (0.10, 0.20),
    ("Knee Moment", "Frontal"):     (0.10, 0.20),
    ("Knee Moment", "Transverse"):  (0.10, 0.20),

    ("Ankle Moment", "Sagittal"):   (0.10, 0.20),
    ("Ankle Moment", "Frontal"):    (0.10, 0.20),
}


# =========================
# COM Marker/Shading
# =========================
COM_TICK_COLOR = "#0a7d0a"   
COM_TICK_LW = 3.0
COM_TICK_LEN = 0.05         

COM_GREY_COLOR = "#a6a6a6"  
COM_GREY_ALPHA = 0.25


# =========================
# Data Structures
# =========================
@dataclass
class SubjectData:
    weight_kg: Optional[float]
    trial_name: str
    series: Dict[str, np.ndarray]     # var -> (N_POINTS,) resampled
    com_pct: Optional[float]          # 0..100 (lowest COM timing)
    injured_limb: Optional[str]       # "L" or "R"


# =========================
# Helpers
# =========================
def _safe_float(x: str) -> Optional[float]:
    try:
        if x is None:
            return None
        s = str(x).strip()
        if s == "":
            return None
        return float(s)
    except Exception:
        return None


def _norm_limb_token(v: str) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip().lower()
    if s == "":
        return None

    if s in {"l", "lt", "left"}:
        return "L"
    if s in {"r", "rt", "right"}:
        return "R"

    if "left" in s:
        return "L"
    if "right" in s:
        return "R"

    if re.fullmatch(r"\s*[l]\s*", s):
        return "L"
    if re.fullmatch(r"\s*[r]\s*", s):
        return "R"

    return None


def parse_id_from_filename(p: Path) -> str:
    name = p.stem
    m = re.match(r"(.+?)_([0-9]+[mM]|[0-9]+[mM][oO]?|[0-9]+[mM][tT])$", name)
    return m.group(1) if m else name


def read_qualisys_csv_anyformat(csv_path: Path) -> Tuple[Dict[str, str], pd.DataFrame, bool]:
    """
    Returns:
      meta dict
      df numeric block (old or multi-trial)
      has_multitrial: bool
    """
    with csv_path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        rows = list(csv.reader(f))

    time_row_idx = None
    for i, r in enumerate(rows):
        if len(r) > 0 and str(r[0]).strip() == "time_s":
            time_row_idx = i
            break
    if time_row_idx is None:
        raise ValueError("Could not find DVJ table start row ('time_s,...').")

    meta: Dict[str, str] = {}
    for r in rows[:time_row_idx]:
        if len(r) >= 2:
            k = str(r[0]).strip()
            v = str(r[1]).strip()
            if k != "":
                meta[k] = v

    has_multitrial = False
    if time_row_idx + 1 < len(rows):
        r1 = rows[time_row_idx + 1]
        if len(r1) > 2 and str(r1[0]).strip() == "":
            has_multitrial = True

    if not has_multitrial:
        header = rows[time_row_idx]
        data_rows = rows[time_row_idx + 1:]

        max_len = max(len(r) for r in ([header] + data_rows)) if data_rows else len(header)
        header = header + [""] * (max_len - len(header))
        data_rows = [r + [""] * (max_len - len(r)) for r in data_rows]

        df = pd.DataFrame(data_rows, columns=header)
        df = df.apply(pd.to_numeric, errors="coerce")
        return meta, df, False

    trial_row = rows[time_row_idx]
    var_row = rows[time_row_idx + 1]
    data_rows = rows[time_row_idx + 2:]

    max_len = max(len(trial_row), len(var_row), *(len(r) for r in data_rows))
    trial_row = trial_row + [""] * (max_len - len(trial_row))
    var_row = var_row + [""] * (max_len - len(var_row))
    data_rows = [r + [""] * (max_len - len(r)) for r in data_rows]

    cols = ["time_s"]
    for j in range(1, max_len):
        trial = str(trial_row[j]).strip()
        var = str(var_row[j]).strip()
        if var == "":
            cols.append(f"{trial}|__EMPTY__")
        else:
            cols.append(f"{trial}|{var}")

    df = pd.DataFrame(data_rows, columns=cols)
    df = df.apply(pd.to_numeric, errors="coerce")
    return meta, df, True


def choose_trial_from_df(df: pd.DataFrame) -> str:
    trial_names = set()
    for c in df.columns:
        if "|" in c:
            t = c.split("|", 1)[0].strip()
            if t and t != "time_s":
                trial_names.add(t)

    for pref in TRIAL_PREFERENCE:
        if pref in trial_names:
            return pref

    best_trial = None
    best_count = -1
    for t in trial_names:
        col = f"{t}|{GRF_VARS_LR[0]}"
        if col in df.columns:
            cnt = int(df[col].notna().sum())
        else:
            trial_cols = [c for c in df.columns if c.startswith(t + "|")]
            cnt = int(df[trial_cols].notna().sum().sum()) if trial_cols else 0

        if cnt > best_count:
            best_count = cnt
            best_trial = t

    if best_trial is None:
        raise ValueError("Could not determine trial name from multi-trial CSV.")
    return best_trial


def extract_series(df: pd.DataFrame, var_name: str, trial: Optional[str]) -> Optional[np.ndarray]:
    if trial is None:
        if var_name not in df.columns:
            return None
        return df[var_name].to_numpy(dtype=float)

    col = f"{trial}|{var_name}"
    if col not in df.columns:
        return None
    return df[col].to_numpy(dtype=float)


def resample_to_percent(y: np.ndarray, n_points: int = N_POINTS) -> np.ndarray:
    y = np.asarray(y, dtype=float)
    if np.all(np.isnan(y)):
        return np.full(n_points, np.nan)

    idx = np.arange(len(y))
    good = ~np.isnan(y)
    if good.sum() < 2:
        return np.full(n_points, np.nan)

    x_old = idx[good].astype(float)
    y_old = y[good].astype(float)
    x_new = np.linspace(x_old.min(), x_old.max(), n_points)
    return np.interp(x_new, x_old, y_old)


def extract_weight_kg(meta: Dict[str, str]) -> Optional[float]:
    for k in meta.keys():
        if k.strip().lower() == "weight (kg)":
            return _safe_float(meta.get(k))
    return None


def compute_lowest_com_pct(com_series_resampled: np.ndarray) -> Optional[float]:
    if com_series_resampled is None:
        return None
    y = np.asarray(com_series_resampled, dtype=float)
    if np.all(np.isnan(y)):
        return None
    i = int(np.nanargmin(y))
    return float(100.0 * i / (len(y) - 1))


def _find_injured_limb_from_meta(meta: Dict[str, str]) -> Optional[str]:
    if not meta:
        return None

    key_hits = []
    for k, v in meta.items():
        ks = str(k).strip().lower()
        if any(tok in ks for tok in ["injur", "aclr", "surg", "involv", "operat", "graft", "affected", "side", "limb"]):
            key_hits.append((k, v))

    strong = [
        (k, v) for (k, v) in key_hits
        if any(tok in str(k).lower() for tok in ["injur", "operat", "aclr", "affected", "involved"])
    ]
    ordered = strong + [kv for kv in key_hits if kv not in strong]

    for _, v in ordered:
        limb = _norm_limb_token(v)
        if limb:
            return limb

    return None


def _find_injured_limb_from_meta_values(meta: Dict[str, str]) -> Optional[str]:
    if not meta:
        return None
    for v in meta.values():
        limb = _norm_limb_token(v)
        if limb:
            return limb
    return None


def get_injured_limb(csv_path: Path, meta: Dict[str, str]) -> Optional[str]:
    sid = parse_id_from_filename(csv_path)
    if sid in MANUAL_INJURED_LIMB:
        limb = _norm_limb_token(MANUAL_INJURED_LIMB[sid])
        if limb:
            return limb

    limb = _find_injured_limb_from_meta(meta)
    if limb:
        return limb

    limb = _find_injured_limb_from_meta_values(meta)
    if limb:
        return limb

    return None


def parse_subject(csv_path: Path) -> SubjectData:
    meta, df, is_multi = read_qualisys_csv_anyformat(csv_path)
    weight_kg = extract_weight_kg(meta)

    trial = choose_trial_from_df(df) if is_multi else None

    series: Dict[str, np.ndarray] = {}

    for _, vars_list in ANGLE_VARS.items():
        for v in vars_list:
            if v in series:
                continue
            raw = extract_series(df, v, trial)
            if raw is not None:
                series[v] = resample_to_percent(raw)

    for _, vars_list in MOMENT_VARS.items():
        for v in vars_list:
            if v in series:
                continue
            raw = extract_series(df, v, trial)
            if raw is not None:
                series[v] = resample_to_percent(raw)

    for v in GRF_VARS_LR:
        raw = extract_series(df, v, trial)
        if raw is not None:
            series[v] = resample_to_percent(raw)

    raw_com = extract_series(df, COM_VAR, trial)
    if raw_com is not None:
        series[COM_VAR] = resample_to_percent(raw_com)

    com_pct = compute_lowest_com_pct(series.get(COM_VAR)) if COM_VAR in series else None
    injured_limb = get_injured_limb(csv_path, meta)

    return SubjectData(
        weight_kg=weight_kg,
        trial_name=(trial if trial is not None else "SINGLE"),
        series=series,
        com_pct=com_pct,
        injured_limb=injured_limb
    )


def moment_to_Nm(moment_norm: np.ndarray, weight_kg: Optional[float]) -> np.ndarray:
    if weight_kg is None or not np.isfinite(weight_kg):
        return moment_norm
    return moment_norm * float(weight_kg)


def grf_to_newtons(grf_bw: np.ndarray, weight_kg: Optional[float]) -> np.ndarray:
    if weight_kg is None or not np.isfinite(weight_kg):
        return grf_bw
    return grf_bw * float(weight_kg) * 9.81


def _pick_side_var(var_names_lr: List[str], limb_mode: str, injured_limb: Optional[str]) -> List[str]:
    mode = (limb_mode or "").strip().lower()

    if mode == "left":
        return [var_names_lr[0]]
    if mode == "right":
        return [var_names_lr[1]]
    if mode == "both_avg":
        return var_names_lr

    if injured_limb == "L":
        if mode == "injured":
            return [var_names_lr[0]]
        if mode == "uninjured":
            return [var_names_lr[1]]
    if injured_limb == "R":
        if mode == "injured":
            return [var_names_lr[1]]
        if mode == "uninjured":
            return [var_names_lr[0]]

    return var_names_lr


def build_group_matrices(
    csv_files: List[Path],
    kind: str,
    group_key: str,
    group_limb_mode: Dict[str, str],
) -> Tuple[Dict[Tuple[str, str], np.ndarray], List[float], int]:
    """
    Build per-panel matrices for one group.

    Returns:
      out[(joint, plane)] = matrix (n_subjects, N_POINTS)
      com_pcts = list of lowest-COM % per subject
      used = number of files successfully parsed
    """
    data_by_panel: Dict[Tuple[str, str], List[np.ndarray]] = {}
    com_pcts: List[float] = []
    used = 0

    limb_mode = (group_limb_mode.get(group_key, "both_avg") if group_limb_mode else "both_avg")
    limb_mode = (limb_mode or "both_avg").strip().lower()

    for f in csv_files:
        try:
            subj = parse_subject(f)
            used += 1

            if subj.com_pct is not None:
                com_pcts.append(subj.com_pct)

            injured_limb = getattr(subj, "injured_limb", None)  # "L"/"R"/None

            if kind == "Angles":
                for key, lr_vars in ANGLE_VARS.items():
                    chosen_vars = _pick_side_var(lr_vars, limb_mode, injured_limb)
                    arrs = [subj.series[v] for v in chosen_vars if v in subj.series]
                    if len(arrs) == 0:
                        continue
                    y = arrs[0] if len(arrs) == 1 else np.nanmean(np.vstack(arrs), axis=0)
                    data_by_panel.setdefault(key, []).append(y)

            else:
                for key, lr_vars in MOMENT_VARS.items():
                    chosen_vars = _pick_side_var(lr_vars, limb_mode, injured_limb)

                    arrs = []
                    for v in chosen_vars:
                        if v in subj.series:
                            arrs.append(moment_to_Nm(subj.series[v], subj.weight_kg))

                    if len(arrs) == 0:
                        continue

                    y = arrs[0] if len(arrs) == 1 else np.nanmean(np.vstack(arrs), axis=0)
                    data_by_panel.setdefault(key, []).append(y)

                chosen_grf_vars = _pick_side_var(GRF_VARS_LR, limb_mode, injured_limb)
                arrs = [
                    grf_to_newtons(subj.series[v], subj.weight_kg)
                    for v in chosen_grf_vars
                    if v in subj.series
                ]
                if len(arrs) > 0:
                    y = arrs[0] if len(arrs) == 1 else np.nanmean(np.vstack(arrs), axis=0)
                    data_by_panel.setdefault(("GRF", "Vertical"), []).append(y)

        except Exception as e:
            print(f"[FAILED] {f} -> {e}")

    out: Dict[Tuple[str, str], np.ndarray] = {}
    for key, rows in data_by_panel.items():
        if len(rows) == 0:
            continue
        out[key] = np.vstack(rows)

    return out, com_pcts, used


def summarize_matrix(mat: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    mean = np.nanmean(mat, axis=0)
    sd = np.nanstd(mat, axis=0, ddof=1)
    n = np.sum(~np.isnan(mat), axis=0).astype(float)
    sem = np.divide(sd, np.sqrt(np.maximum(n, 1.0)), out=np.full_like(sd, np.nan), where=n > 0)
    lo = mean - 1.96 * sem
    hi = mean + 1.96 * sem
    return mean, lo, hi


def make_summary_df(group_to_mats: Dict[str, Dict[Tuple[str, str], np.ndarray]], kind: str) -> pd.DataFrame:
    rows = []
    percent = np.linspace(0, 100, N_POINTS)

    for grp, mats in group_to_mats.items():
        for (joint, plane), mat in mats.items():
            mean, lo, hi = summarize_matrix(mat)
            for i in range(N_POINTS):
                rows.append({
                    "group": grp,
                    "joint": joint,
                    "plane": plane,
                    "percent": percent[i],
                    "mean": mean[i],
                    "lo": lo[i],
                    "hi": hi[i],
                    "kind": kind
                })

    return pd.DataFrame(rows)


def compute_com_stats(all_com_pcts: List[float]) -> Optional[Tuple[float, float, float]]:
    if len(all_com_pcts) == 0:
        return None
    v = np.array(all_com_pcts, dtype=float)
    v = v[np.isfinite(v)]
    if v.size == 0:
        return None
    return float(v.mean()), float(v.min()), float(v.max())


def _place_dir_annotation(ax, text: str, direction: str, joint: str, plane: str):
    if (joint, plane) in MANUAL_DIR_POS:
        x, y0 = MANUAL_DIR_POS[(joint, plane)]
    else:
        y_stacks = []
        for ln in ax.lines:
            y = ln.get_ydata()
            if y is None:
                continue
            y = np.asarray(y, dtype=float)
            if y.ndim != 1 or y.size != N_POINTS:
                continue
            if not np.all(np.isnan(y)):
                y_stacks.append(y)

        if len(y_stacks) == 0:
            x, y0 = 0.12, 0.82
        else:
            Y = np.vstack(y_stacks)
            y_min = np.nanmin(Y, axis=0)
            y_max = np.nanmax(Y, axis=0)

            candidates = [
                (0.12, 0.90), (0.12, 0.80), (0.12, 0.70),
                (0.78, 0.90), (0.78, 0.80), (0.78, 0.70),
                (0.12, 0.40), (0.78, 0.40),
            ]

            best = None
            best_score = -np.inf
            for (x_frac, y_frac) in candidates:
                idx = int(round((N_POINTS - 1) * x_frac))
                idx = max(0, min(N_POINTS - 1, idx))

                env_mid = 0.5 * (y_min[idx] + y_max[idx])
                env_span = (y_max[idx] - y_min[idx])

                y_data = ax.transData.inverted().transform(
                    ax.transAxes.transform((0.5, y_frac))
                )[1]

                dist = abs(y_data - env_mid)
                score = dist - 0.25 * env_span
                score += 0.02 * (abs(x_frac - 0.5) + abs(y_frac - 0.5))

                if score > best_score:
                    best_score = score
                    best = (x_frac, y_frac)

            x, y0 = best

    dy = 0.10 if direction == "up" else -0.10

    ax.annotate(
        "",
        xy=(x, y0 + dy),
        xytext=(x, y0),
        xycoords="axes fraction",
        arrowprops=dict(arrowstyle="-|>", lw=2.0, color="black"),
        zorder=10,
        clip_on=True
    )

    ax.text(
        x + 0.05,
        y0 + (dy * 0.35),
        text,
        transform=ax.transAxes,
        fontsize=10,
        fontstyle="italic",
        va="center",
        color="black",
        zorder=10,
        clip_on=True
    )


def plot_panels(
    summary_df: pd.DataFrame,
    group_order: List[str],
    out_png: Path,
    panels: List[Tuple[str, str]],
    kind: str,
    n_by_group: Dict[str, int],
    com_stats: Optional[Tuple[float, float, float]]
):
    group_labels = {}
    for g in group_order:
        disp = GROUP_NAME_MAP.get(g, g)
        group_labels[g] = f"{disp} (N={n_by_group.get(g, 0)})"

    n = len(panels)
    ncols = 3
    nrows = math.ceil(n / ncols)

    fig, axes = plt.subplots(nrows, ncols, figsize=(16, 9.6))
    axes = np.array(axes).ravel()

    mean_pct = None
    if com_stats is not None:
        mean_pct, _, _ = com_stats

    for i, (joint, plane) in enumerate(panels):
        ax = axes[i]

        if mean_pct is not None:
            ax.axvspan(0, mean_pct, color=COM_GREY_COLOR, alpha=COM_GREY_ALPHA, zorder=0)

            ax.plot(
                [mean_pct, mean_pct],
                [-COM_TICK_LEN, 0.0],
                transform=ax.get_xaxis_transform(),
                color=COM_TICK_COLOR,
                linewidth=COM_TICK_LW,
                solid_capstyle="butt",
                zorder=6,
                clip_on=False
            )
            ax.text(
                mean_pct,
                -COM_TICK_LEN - 0.015,
                f"{int(round(mean_pct))}% (avg)",
                transform=ax.get_xaxis_transform(),
                ha="center",
                va="top",
                fontsize=7,
                color=COM_TICK_COLOR,
                clip_on=False
            )

        for grp in group_order:
            s = summary_df[
                (summary_df["group"] == grp) &
                (summary_df["joint"] == joint) &
                (summary_df["plane"] == plane)
            ].sort_values("percent")

            if s.empty:
                continue

            c = COLOR_MAP.get(grp)
            if c is None:
                raise ValueError(f"Group '{grp}' missing from COLOR_MAP keys: {list(COLOR_MAP.keys())}")

            ax.fill_between(
                s["percent"].to_numpy(),
                s["lo"].to_numpy(),
                s["hi"].to_numpy(),
                facecolor=to_rgba(c, BAND_ALPHA),
                edgecolor="none",
                zorder=1,
            )
            ax.plot(
                s["percent"].to_numpy(),
                s["mean"].to_numpy(),
                label=group_labels[grp],
                color=c,
                linewidth=LINE_WIDTH,
                zorder=2,
            )

        if joint == "GRF" and kind == "Moments":
            ax.set_title("GRF (Vertical)", fontweight="bold")
        else:
            if plane is None or str(plane).strip() == "":
                ax.set_title(f"{joint}", fontweight="bold")
            else:
                ax.set_title(f"{joint} ({plane})", fontweight="bold")

        ax.set_xlabel("Stance (%)")

        if kind == "Angles":
            ax.set_ylabel("Strain" if joint == "ACL Strain" else "Degrees (°)")
        else:
            ax.set_ylabel("N" if joint == "GRF" else "Nm")

        ax.grid(True, alpha=0.2)
        ax.set_xlim(0, 100)
        ax.margins(x=0)

        key = (joint, plane, kind)
        if key in DIR_ANNOT:
            text, direction = DIR_ANNOT[key]
            _place_dir_annotation(ax, text, direction, joint, plane)
        else:
            key2 = (joint, "", kind)
            if key2 in DIR_ANNOT:
                text, direction = DIR_ANNOT[key2]
                _place_dir_annotation(ax, text, direction, joint, "")

    for j in range(n, len(axes)):
        axes[j].axis("off")

    handles, labels = axes[0].get_legend_handles_labels()

    fig.subplots_adjust(left=0.06, right=0.99, top=0.92, bottom=0.16, wspace=0.22, hspace=0.35)

    ncol = min(len(group_order), 4)
    fig.legend(
        handles, labels,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.045),
        ncol=ncol,
        frameon=False
    )

    fig.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.close(fig)


def pick_folder(prompt: str) -> Path:
    root = tk.Tk()
    root.withdraw()
    folder = filedialog.askdirectory(title=prompt)
    if not folder:
        raise RuntimeError("No folder selected.")
    return Path(folder)


def collect_csvs(folder: Path) -> List[Path]:
    return sorted(folder.rglob("*.csv"))


def main():
    group_folders: Dict[str, Path] = {}
    for g in GROUP_KEYS:
        disp = GROUP_NAME_MAP.get(g, g)
        folder = pick_folder(f"Select folder for group: {disp}")
        group_folders[g] = folder

    out_dir = pick_folder("Select output folder for plots")
    out_dir.mkdir(parents=True, exist_ok=True)

    group_to_angles: Dict[str, Dict[Tuple[str, str], np.ndarray]] = {}
    group_to_moments: Dict[str, Dict[Tuple[str, str], np.ndarray]] = {}
    n_by_group: Dict[str, int] = {}
    all_com_pcts: List[float] = []

    for g, folder in group_folders.items():
        files = collect_csvs(folder)
        if len(files) == 0:
            print(f"[WARN] No CSVs found for group {g} in {folder}")
            continue

        ang_mats, com_pcts, n_used_a = build_group_matrices(
            files, kind="Angles", group_key=g, group_limb_mode=GROUP_LIMB_MODE
        )
        group_to_angles[g] = ang_mats

        mom_mats, com_pcts2, n_used_m = build_group_matrices(
            files, kind="Moments", group_key=g, group_limb_mode=GROUP_LIMB_MODE
        )
        group_to_moments[g] = mom_mats

        n_by_group[g] = max(n_used_a, n_used_m)

        all_com_pcts.extend([x for x in com_pcts if x is not None])
        all_com_pcts.extend([x for x in com_pcts2 if x is not None])

        print(f"[OK] {g}: {len(files)} files scanned, used {n_by_group[g]} | limb_mode={GROUP_LIMB_MODE.get(g, 'both_avg')}")

    angles_df = make_summary_df(group_to_angles, kind="Angles")
    moments_df = make_summary_df(group_to_moments, kind="Moments")

    com_stats = compute_com_stats(all_com_pcts)
    group_order = [g for g in GROUP_KEYS if g in n_by_group]

    plot_panels(
        angles_df,
        group_order=group_order,
        out_png=out_dir / OUT_ANGLES_PNG,
        panels=ANGLES_PANELS,
        kind="Angles",
        n_by_group=n_by_group,
        com_stats=com_stats
    )

    plot_panels(
        moments_df,
        group_order=group_order,
        out_png=out_dir / OUT_MOMENTS_PNG,
        panels=MOMENTS_PANELS,
        kind="Moments",
        n_by_group=n_by_group,
        com_stats=com_stats
    )

    print(f"[DONE] Saved:\n  {out_dir / OUT_ANGLES_PNG}\n  {out_dir / OUT_MOMENTS_PNG}")


if __name__ == "__main__":
    main()
