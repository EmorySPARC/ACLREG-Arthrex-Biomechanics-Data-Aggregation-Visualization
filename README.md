# Qualisys Biomechanics Pipeline

End-to-end pipeline for processing motion capture data from JSON outputs:

1. **Export time-series data from Qualisys JSON → CSV**
2. **Generate group-level biomechanics plots from CSV**

This repo contains workflows for ACLREG/Arthrex where you want a clean, repeatable path from raw exports to prelim figures. Could be modified for anything that utilizes Qualisys reporting outputs.

---

## Pipeline Overview

```text
Qualisys JSON
      ↓
[ Script 1 ] JSON → CSV Export
      ↓
Processed CSV files
      ↓
[ Script 2 ] CSV → Plot Generator
      ↓
Group comparison figures (PNG)
```

Outputs include:
- Joint angles
- Joint moments
- GRF
- ACL strain
- Group mean + 95% CI plots

---

## Repository Structure

```text
repo/
├── json_to_csv.py
├── plot_generator.py
├── README.md
├── examples/
│   ├── dvj_angles.png
│   └── dvj_moments.png
└── data/
```

---

## Requirements

- Python 3.9+
- numpy
- pandas
- matplotlib

Install:

```bash
pip install numpy pandas matplotlib
```

---

# Step 1 — JSON → CSV Export

## What it does

- Reads Qualisys JSON files
- Uses event markers to define movement windows
- Extracts selected time-series variables
- Computes ACL strain (`ACLam`)
- Writes structured CSV files

## Key features

- Batch processing
- Event-based segmentation
- Customizable variables
- Subject metadata extraction
- Age calculation
- Derived ACL strain output

## Event logic

Currently uses: (For the DVJ task)

```python
EVENT_IDS = ["LON", "LOFF", "RON", "ROFF"]
```

Window:
- Start = min(LON, RON)
- End = max(LOFF, ROFF)

## Output format

Each CSV contains:
- Subject metadata (top rows)
- Time-normalized data
- Multi-column structure for each measurement

## Run

```bash
python QualisysJSONparse_v2.py
```

---

# Step 2 — CSV → Plot Generator

## What it does

- Reads exported CSV files
- Selects correct limb per group
- Resamples to normalized stance (0–100%)
- Computes group mean + 95% CI
- Generates publication-style figures

## Output (As an example)

- `dvj_angles_contra.png`
- `dvj_moments_contra.png`

## Features

- Multi-group comparison
- Limb selection (injured/uninjured/etc.)
- Automatic trial selection
- Unit conversion (Nm, N)
- COM-based stance shading
- Directional annotations
- 3×3 panel plots

---

## Groups

```python
GROUP_KEYS = ["RET", "CTRL"]
```

## Limb selection

```python
GROUP_LIMB_MODE = {
    "RET": "uninjured",
    "CTRL": "uninjured",
}
```

---

## Run

```bash
python ACLREG_PlotGenerator_v4.py
```

Workflow:
1. Select folder for each group
2. Select output folder
3. Plots are generated automatically

---

## Key Assumptions

- CSVs come from the exporter script
- Variable names match expected mappings
- Weight (kg) exists for unit conversion
- COM signal is present for shading

---

## Common Issues

### Missing plots
- Variable mismatch
- Empty data

### Wrong limb
- Metadata missing → use manual override

### Incorrect units
- Missing weight

### Wrong trial selected
- Update `TRIAL_PREFERENCE`

---

## Customization

You can easily modify:

- Groups and labels
- Colors
- Limb selection logic
- Panel definitions
- Variables included
- Plot styling

---

## Potential Improvements

- CLI interface instead of dialogs
- Save summary CSVs
- Add statistical testing
- Modularize scripts
- Add config file

---

## Notes

This pipeline is currently tuned for:

**Drop Vertical Jump (DVJ) contralateral comparisons**

Before reuse:
- verify events
- verify variables
- verify units
- verify limb logic

---

## Author

Andrew Schille - Research Technical Specialist - Emory SPARC - 2021-present
