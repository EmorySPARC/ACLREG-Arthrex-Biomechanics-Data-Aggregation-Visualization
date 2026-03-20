# This script extracts time-series data from Qualisys JSON exports and writes them to CSV files.
# It looks for specific event IDs to define the start/end of measurement segments, and extracts specified
# result time-series for those segments. It also computes a derived ACL strain measure based on knee angles.

import csv
import json
import tkinter as tk
from datetime import date
from itertools import zip_longest
from pathlib import Path
from tkinter import filedialog
import numpy as np

# Event IDs used to define the start/end 
# This may need to be changed depending on the task you are analyzing
# For example, for a drop vertical jump, you might have "LON" (left foot on), "LOFF" (left foot off), "RON" (right foot on), "ROFF" (right foot off).
# While a single-leg hop might just have "ON" and "OFF" events for the single leg.
EVENT_IDS = ["LON", "LOFF", "RON", "ROFF"]

# Result time-series to extract for each measurement
# Change these depending on what you want to export
RESULT_IDS = [
    "Left Knee Angles_X",  "Left Knee Angles_Y",  "Left Knee Angles_Z",
    "Right Knee Angles_X", "Right Knee Angles_Y", "Right Knee Angles_Z",
    "Left Hip Angles_X",   "Left Hip Angles_Y",   "Left Hip Angles_Z",
    "Right Hip Angles_X",  "Right Hip Angles_Y",  "Right Hip Angles_Z",
    "Left Ankle Angles_X", "Left Ankle Angles_Y", "Left Ankle Angles_Z",
    "Right Ankle Angles_X","Right Ankle Angles_Y","Right Ankle Angles_Z",
    "Left Knee Moment_X",  "Left Knee Moment_Y",  "Left Knee Moment_Z",
    "Right Knee Moment_X", "Right Knee Moment_Y", "Right Knee Moment_Z",
    "Left Hip Moment_X",   "Left Hip Moment_Y",   "Left Hip Moment_Z",
    "Right Hip Moment_X",  "Right Hip Moment_Y",  "Right Hip Moment_Z",
    "Left Ankle Moment_X", "Left Ankle Moment_Y", "Left Ankle Moment_Z",
    "Right Ankle Moment_X","Right Ankle Moment_Y","Right Ankle Moment_Z",
    "Left GRF_Z",
    "Right GRF_Z",        
    "Pelvis_COM_Z"
]
# Qualisys json Joint Angle Convention:
# Hip +x/y/z: flexion, adduction, internal rotation
# Knee +x/y/z: flexion, adduction, internal rotation
# Ankle + x/y/z: dorsiflexion, inversion, internal rotation

# Subject metadata fields to print at the top of the CSV
SUBJECT_FIELD_IDS = {
    "ID": "ID",
    "Sex": "Sex",
    "Injured side": "Injured side",
    "Height (m)": "Height",
    "Weight (kg)": "Weight",
}

# Sample rate in Hz
FPS = 120


# -----------------------------
# File dialog helpers (Tkinter)
# -----------------------------
def pick_files_open():
    root = tk.Tk()
    root.withdraw()
    paths = filedialog.askopenfilenames(
        title="Select JSON file(s)",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
    )
    root.destroy()
    return list(paths)


def pick_output_dir():
    root = tk.Tk()
    root.withdraw()
    out_dir = filedialog.askdirectory(title="Select output folder for CSVs")
    root.destroy()
    return out_dir


# -----------------------------------
# Small data-cleanup / utility helpers
# -----------------------------------
def first_scalar(v):
    return v[0] if isinstance(v, list) and v else v


def build_event_frames(event, fps=FPS):
    m2f = {}
    for row in event.get("data", []):
        if not isinstance(row, dict):
            continue
        m = row.get("measurement")
        t = first_scalar(row.get("values"))
        if m is None or t is None or m in m2f:
            continue
        m2f[m] = int(round(float(t) * fps))
    return m2f


def clamp_range(s, e, n):
    if n <= 0:
        return 0, -1
    s2 = max(0, min(int(s), n - 1))
    e2 = max(0, min(int(e), n - 1))
    return s2, e2


def looks_like_yyyy_mm_dd(s: str) -> bool:
    if not isinstance(s, str) or len(s) < 10:
        return False
    try:
        y, m, d = s[:10].split("-")
        int(y); int(m); int(d)
        return len(y) == 4 and len(m) == 2 and len(d) == 2
    except Exception:
        return False


def desired_csv_stem_from_subject_id(subject_id: str) -> str:
    if not subject_id or not isinstance(subject_id, str):
        return ""
    parts = subject_id.split("_")
    if len(parts) >= 2 and looks_like_yyyy_mm_dd(parts[-1]):
        return "_".join(parts[:-1])
    return subject_id


# -----------------------------
# Subject header (top-of-CSV)
# -----------------------------
def parse_ymd(s):
    if not s or not isinstance(s, str):
        return None
    try:
        y, m, d = s[:10].split("-")
        return date(int(y), int(m), int(d))
    except Exception:
        return None


def age_years(dob, on_date):
    if not dob or not on_date:
        return None
    return (on_date - dob).days / 365.2425


def extract_subject_header(data):
    measurements = data.get("measurements") or []
    if isinstance(measurements, dict):
        meas_iter = measurements.values()
    elif isinstance(measurements, list):
        meas_iter = measurements
    else:
        return []

    for meas in meas_iter:
        fields = (meas or {}).get("fields")
        if not isinstance(fields, list):
            continue

        field_map = {f.get("id"): f.get("value") for f in fields if isinstance(f, dict)}
        if not field_map:
            continue

        dob = parse_ymd(field_map.get("DOB"))
        created = parse_ymd(field_map.get("Creation date"))
        age = age_years(dob, created)

        rows = [
            (label, "" if field_map.get(fid) is None else str(field_map.get(fid)))
            for label, fid in SUBJECT_FIELD_IDS.items()
        ]
        rows.append(("Age (years)", "" if age is None else str(age)))
        return rows

    return []


# -----------------------------
# JSON extraction helpers
# -----------------------------
def build_measurement_order(events_by_id):
    all_measurements = []
    seen = set()

    for eid in EVENT_IDS:
        for row in events_by_id[eid].get("data", []):
            if not isinstance(row, dict):
                continue
            m = row.get("measurement")
            if m is not None and m not in seen:
                seen.add(m)
                all_measurements.append(m)

    return all_measurements


def build_result_maps(results_by_id):
    result_maps = {}
    for rid in RESULT_IDS:
        meas_map = {}

        block = results_by_id.get(rid)
        if not isinstance(block, dict):
            result_maps[rid] = {}
            continue

        for row in block.get("data", []):
            if not isinstance(row, dict):
                continue
            m = row.get("measurement")
            if m is None:
                continue

            vals = row.get("values")
            if vals is None:
                vals = []
            elif not isinstance(vals, list):
                vals = [vals]

            meas_map[m] = vals

        result_maps[rid] = meas_map

    return result_maps


def get_subject_id(data) -> str:
    subj = data.get("subject")
    if isinstance(subj, dict):
        sid = subj.get("id") or subj.get("ID")
        return sid if isinstance(sid, str) else ""
    return ""


# -----------------------------
# ACL strain model
# Explicitly for knee flexion, adduction, internal rotation
# Based off equation/sample from Sam:
'''
def ACLam(knee_flexion, knee_adduction, knee_internalrotation)

flx= np.asarray(knee_flexion) 
add = np.asarray(knee_adduction)
rot = np.asarray(knee_internalrotation) 

e = ((add * 0.20823456) + 0.6353392) + ( ((((((rot * -0.122331135) - 14.163) + flx) * -0.0048952736) ** 2 + rot) * ((0.15136042 - ((rot + add) * 0.00048596063)) + (flx * -0.00041619135))) )

return e_ACLam
'''
# -----------------------------
def ACLam(knee_flexion, knee_adduction, knee_internalrotation):
    flx = np.asarray(knee_flexion, dtype=float)
    add = np.asarray(knee_adduction, dtype=float)
    rot = np.asarray(knee_internalrotation, dtype=float)

    e_ACLam = ((add * 0.20823456) + 0.6353392) + (
        ((((((rot * -0.122331135) - 14.163) + flx) * -0.0048952736) ** 2 + rot) *
         ((0.15136042 - ((rot + add) * 0.00048596063)) + (flx * -0.00041619135)))
    )
    return e_ACLam


def process_json(in_path):
    with open(in_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    subject_id = get_subject_id(data)
    csv_stem = desired_csv_stem_from_subject_id(subject_id)

    # Events
    events = data.get("events", [])
    events_by_id = {e.get("id"): e for e in events if isinstance(e, dict)}

    missing_events = [eid for eid in EVENT_IDS if eid not in events_by_id]
    if missing_events:
        raise ValueError("Missing event id(s): " + ", ".join(missing_events))

    all_measurements = build_measurement_order(events_by_id)

    f_LON = build_event_frames(events_by_id["LON"])
    f_RON = build_event_frames(events_by_id["RON"])
    f_LOFF = build_event_frames(events_by_id["LOFF"])
    f_ROFF = build_event_frames(events_by_id["ROFF"])

    ranges = [
        (m, min(f_LON[m], f_RON[m]), max(f_LOFF[m], f_ROFF[m]))
        for m in all_measurements
        if m in f_LON and m in f_RON and m in f_LOFF and m in f_ROFF
    ]
    if not ranges:
        raise ValueError("No measurements had all four event times (LON, RON, LOFF, ROFF).")

    # Results
    results = data.get("results", [])
    results_by_id = {r.get("id"): r for r in results if isinstance(r, dict)}

    missing_results = [rid for rid in RESULT_IDS if rid not in results_by_id]
    if missing_results:
        raise ValueError("Missing result id(s): " + ", ".join(missing_results))

    result_maps = build_result_maps(results_by_id)

    meas_header = ["time_s"]
    rid_header = [""]
    columns = []
    max_len = 0

    for m, s, e in ranges:
        def get_seg(rid_name):
            vals = result_maps.get(rid_name, {}).get(m, [])
            s2, e2 = clamp_range(s, e, len(vals))
            return vals[s2:e2 + 1] if e2 >= s2 else []

        # Export requested series
        for rid in RESULT_IDS:
            meas_header.append(m)
            rid_header.append(rid)
            seg = get_seg(rid)
            columns.append(seg)
            max_len = max(max_len, len(seg))

        # Derived ACLam (Knee X/Y/Z)
        lkx = get_seg("Left Knee Angles_X")
        lky = get_seg("Left Knee Angles_Y")
        lkz = get_seg("Left Knee Angles_Z")

        rkx = get_seg("Right Knee Angles_X")
        rky = get_seg("Right Knee Angles_Y")
        rkz = get_seg("Right Knee Angles_Z")

        if len(lkx) and len(lky) and len(lkz):
            n = min(len(lkx), len(lky), len(lkz))
            acl_left = ACLam(lkx[:n], lky[:n], lkz[:n]).tolist()
        else:
            acl_left = []

        meas_header.append(m)
        rid_header.append("Left Knee ACLam")
        columns.append(acl_left)
        max_len = max(max_len, len(acl_left))

        if len(rkx) and len(rky) and len(rkz):
            n = min(len(rkx), len(rky), len(rkz))
            acl_right = ACLam(rkx[:n], rky[:n], rkz[:n]).tolist()
        else:
            acl_right = []

        meas_header.append(m)
        rid_header.append("Right Knee ACLam")
        columns.append(acl_right)
        max_len = max(max_len, len(acl_right))

    if max_len == 0:
        raise ValueError("No time-series data found in the requested frame ranges.")

    time_col = [i / FPS for i in range(max_len)]
    subject_rows = extract_subject_header(data)

    return subject_rows, meas_header, rid_header, time_col, columns, csv_stem


def write_csv(out_path, subject_rows, meas_header, rid_header, time_col, columns):
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)

        if subject_rows:
            w.writerows(subject_rows)
            w.writerow([])

        w.writerow(meas_header)
        w.writerow(rid_header)

        for t, *row_vals in zip_longest(time_col, *columns, fillvalue=""):
            w.writerow([t, *row_vals])


def main():
    in_paths = pick_files_open()
    if not in_paths:
        print("No files selected.")
        raise SystemExit

    out_dir = pick_output_dir()
    if not out_dir:
        print("No output folder selected.")
        raise SystemExit

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    ok = 0
    skipped = 0
    failed = 0

    for in_path in in_paths:
        in_path = Path(in_path)

        try:
            subject_rows, meas_header, rid_header, time_col, columns, csv_stem = process_json(in_path)

            stem = csv_stem if csv_stem else in_path.stem
            out_path = out_dir / f"{stem}.csv"

            write_csv(out_path, subject_rows, meas_header, rid_header, time_col, columns)

            print(f"[OK] {out_path}")
            ok += 1

        except ValueError as e:
            msg = str(e)
            if msg.startswith("Missing event id(s):") or msg.startswith("Missing result id(s):"):
                print(f"[SKIPPED] {in_path} -> {e}")
                skipped += 1
            else:
                print(f"[FAILED] {in_path} -> {e}")
                failed += 1

        except Exception as e:
            print(f"[FAILED] {in_path} -> {e}")
            failed += 1

    print(f"Done. OK: {ok} | Skipped: {skipped} | Failed: {failed} | Output folder: {out_dir}")


if __name__ == "__main__":
    main()
