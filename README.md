# ACLREG-Arthrex-Biomechanics-Data-Aggregation-Visualization
# Qualisys JSON Time-Series Exporter

Export selected time-series variables from Qualisys JSON files to CSV using task-specific event windows, with optional derived ACL strain output (`ACLam`).

---

## Overview

This script is designed for biomechanics workflows that use Qualisys JSON exports. It:

- selects one or more JSON files through a simple file dialog
- selects an output folder through a folder dialog
- reads subject metadata from the JSON
- uses event markers to define the frame range for each measurement
- extracts selected kinematic, kinetic, GRF, and COM time-series
- computes left and right knee `ACLam` values from knee angle data
- writes one CSV per input JSON

This is useful for batch-exporting motion analysis data into a format that is easier to inspect in Excel or process further in Python, R, MATLAB, or statistical pipelines.

---

## Features

- Batch processing of multiple Qualisys JSON files
- GUI-based file and output-folder selection with Tkinter
- Event-based segmentation of time-series data
- Export of joint angles, joint moments, GRF, and COM variables
- Subject metadata written at the top of each CSV
- Automatic age calculation from DOB and creation date
- Derived `ACLam` calculation for left and right knees
- Output filename cleanup based on subject ID

---

## Current event logic

The script is currently configured for the DVJ task using:

```python
EVENT_IDS = ["LON", "LOFF", "RON", "ROFF"]
```

For each measurement, the exported frame window is defined as:

- **start frame** = earlier of `LON` and `RON`
- **end frame** = later of `LOFF` and `ROFF`

---

## Requirements

- Python 3.9+
- NumPy

Install dependency:

```bash
pip install numpy
```

---

## Usage

Run the script:

```bash
python qualisys_json_exporter.py
```

### Workflow
1. Select one or more Qualisys JSON files.
2. Select an output folder.
3. CSV files are generated for each JSON.

---

## Notes

Before using broadly, verify:
- event names
- sample rate
- result IDs
- task-specific event logic
- axis/sign conventions

## Qualisys Biomechanics Plot Generator

Generate group-level biomechanics comparison plots from exported Qualisys CSV files. The script reads per-subject time-series CSVs, selects the desired limb for each group, resamples signals to normalized stance, computes group means with 95% confidence bands, and saves publication-style angle and moment summary figures.

This version is configured to compare:

- **RET** = Contralateral Re-Tear UNV Limb (6m)
- **CTRL** = ACLR Control UNV Limb (6m)

and produces figures like:

- `dvj_angles_contra.png`
- `dvj_moments_contra.png`

---

## Overview

This script is meant for workflows where Qualisys JSON exports have already been converted into CSV format. It:

- loads all CSVs within a folder for each study group
- reads either single-trial or multi-trial CSV layouts
- picks a preferred trial when multiple trials are present
- infers injured side from metadata when needed
- selects the correct limb for each group
- rescales each signal to **101 points across stance**
- converts moments and GRF into physical units when body weight is available
- computes group means and 95% confidence intervals
- adds lowest-COM timing shading to every panel
- exports two 3×3 summary figures:
  - angles
  - moments / GRF

This is useful for group comparisons in ACLR / re-tear studies, especially when you want a consistent, automated figure-generation step for reports, posters, or manuscripts.

---

## Features

- Batch processing of subject CSVs by group
- Supports both **single-trial** and **multi-trial** CSV formats
- Trial selection using a priority list
- Configurable group labels and colors
- Limb selection modes:
  - injured
  - uninjured
  - left
  - right
  - both_avg
- Automatic resampling to normalized stance (`N_POINTS = 101`)
- Converts normalized moments to **Nm**
- Converts GRF to **N**
- Computes group mean and 95% CI
- Adds directional annotations on each panel
- Adds COM-based stance shading and marker
- Saves high-resolution PNG figures

---

## Expected input

This script expects CSV files exported from your Qualisys processing pipeline.

### Supported CSV layouts

#### 1. Single-trial format
A standard CSV with:

- metadata rows at the top
- a row beginning with `time_s`
- one data table below it

#### 2. Multi-trial format
A CSV where the time-series section has:

- first row beginning with `time_s`
- second row containing variable names
- columns named internally by the script as:

```text
TrialName|VariableName
```

The script auto-detects whether the file is single-trial or multi-trial.

---

## Current outputs

The script currently saves:

- `dvj_angles_contra.png`
- `dvj_moments_contra.png`

These correspond to:

### Angle figure panels
- Hip Angle (Sagittal)
- Hip Angle (Frontal)
- Hip Angle (Transverse)
- Knee Angle (Sagittal)
- Knee Angle (Frontal)
- Knee Angle (Transverse)
- Ankle Angle (Sagittal)
- Ankle Angle (Frontal)
- ACL Strain

### Moment / force figure panels
- Hip Moment (Sagittal)
- Hip Moment (Frontal)
- Hip Moment (Transverse)
- Knee Moment (Sagittal)
- Knee Moment (Frontal)
- Knee Moment (Transverse)
- Ankle Moment (Sagittal)
- Ankle Moment (Frontal)
- GRF (Vertical)

---

## Current configuration

### Groups

```python
GROUP_KEYS = ["RET", "CTRL"]
```

Display names:

```python
GROUP_NAME_MAP = {
    "RET": "Contralateral Re-Tear UNV Limb (6m)",
    "CTRL": "ACLR Control UNV Limb (6m)",
}
```

Colors:

```python
COLOR_MAP = {
    "RET": "#d7191c",
    "CTRL": "#2c7bb6",
}
```

### Limb selection

The script currently uses:

```python
GROUP_LIMB_MODE = {
    "RET": "uninjured",
    "CTRL": "uninjured",
}
```

That means it will plot the **contralateral / uninvolved limb** for both groups.

Available modes:

- `"injured"` → injured / ACLR limb
- `"uninjured"` → contralateral limb
- `"left"` → always left
- `"right"` → always right
- `"both_avg"` → average left and right

### Trial selection preference

When a multi-trial CSV contains several trials, the script tries:

```python
TRIAL_PREFERENCE = [
    "Drop jump/DJ_B 2",
    "Drop jump/DJ_B 1",
    "Drop jump/DJ_B 3",
]
```

If none of those exist, it picks the trial with the most usable data.

### Normalized stance length

```python
N_POINTS = 101
```

All series are resampled to 101 points across stance.

---

## Required variables

The script expects these variables when building panels.

### Angle variables
- Left Hip Angles_X / Right Hip Angles_X
- Left Hip Angles_Y / Right Hip Angles_Y
- Left Hip Angles_Z / Right Hip Angles_Z
- Left Knee Angles_X / Right Knee Angles_X
- Left Knee Angles_Y / Right Knee Angles_Y
- Left Knee Angles_Z / Right Knee Angles_Z
- Left Ankle Angles_X / Right Ankle Angles_X
- Left Ankle Angles_Y / Right Ankle Angles_Y
- Left Knee ACLam / Right Knee ACLam

### Moment variables
- Left Hip Moment_X / Right Hip Moment_X
- Left Hip Moment_Y / Right Hip Moment_Y
- Left Hip Moment_Z / Right Hip Moment_Z
- Left Knee Moment_X / Right Knee Moment_X
- Left Knee Moment_Y / Right Knee Moment_Y
- Left Knee Moment_Z / Right Knee Moment_Z
- Left Ankle Moment_X / Right Ankle Moment_X
- Left Ankle Moment_Y / Right Ankle Moment_Y

### GRF / COM variables
- Left GRF_Z
- Right GRF_Z
- Pelvis_COM_Z

---

## Metadata used

The script looks for metadata fields in the CSV header section.

### Used directly
- `Weight (kg)`

### Used for injured side inference
The script searches metadata keys and values for likely limb information, including fields related to:

- injured side
- ACLR side
- operated side
- affected limb
- involved limb

If injured side cannot be inferred automatically, you can hardcode it with:

```python
MANUAL_INJURED_LIMB = {
    # "ACLREG_0045": "L",
}
```

Subject ID is derived from the filename using `parse_id_from_filename()`.

---

## Unit handling

### Moments
Moment series are assumed to be normalized and are converted to **Nm** using:

```python
moment * body_mass_kg
```

### GRF
GRF series are assumed to be in body-weight units and are converted to **N** using:

```python
grf * body_mass_kg * 9.81
```

If `Weight (kg)` is missing or invalid, the script leaves the original values unchanged.

---

## Lowest COM shading

The script uses `Pelvis_COM_Z` to find the timing of the lowest COM for each subject after normalization.

It then computes the average lowest-COM timing across all included subjects and adds:

- a grey shaded region from 0% stance to the average COM minimum timing
- a green tick mark at the average timing
- a label such as `49% (avg)`

This shading is applied to every panel.

---

## Statistical summary

For each group and panel, the script computes:

- mean
- standard deviation
- standard error of the mean
- 95% confidence interval using:

```python
mean ± 1.96 * SEM
```

The plotted band is the 95% CI, not standard deviation.

---

## Dependencies

- Python 3.9+
- NumPy
- pandas
- matplotlib

Tkinter is also used for folder selection and is part of most standard Python installs.

Install dependencies:

```bash
pip install numpy pandas matplotlib
```

---

## Repository structure

Example repo layout:

```text
your-repo/
├── plot_generator.py
├── README.md
├── examples/
│   ├── dvj_angles_contralateral.png
│   └── dvj_moments_contralateral.png
└── sample_csvs/
```

---

## How to run

Run the script with Python:

```bash
python plot_generator.py
```

### Workflow
1. Select the folder containing CSVs for the first group.
2. Select the folder containing CSVs for the second group.
3. Select the output folder for the plots.
4. The script scans all CSVs recursively in each group folder.
5. Two PNG files are written to the output directory.

---

## Console output

Typical console output looks like:

```text
[OK] RET: 12 files scanned, used 12 | limb_mode=uninjured
[OK] CTRL: 12 files scanned, used 12 | limb_mode=uninjured
[DONE] Saved:
  C:\...\dvj_angles_contra.png
  C:\...\dvj_moments_contra.png
```

Individual failed files are reported as:

```text
[FAILED] path\to\file.csv -> <error message>
```

---

## How the script works

### 1. Folder selection
The script prompts the user to select:

- one folder per group in `GROUP_KEYS`
- one output folder

### 2. File collection
All CSVs are collected recursively with:

```python
folder.rglob("*.csv")
```

### 3. CSV parsing
`read_qualisys_csv_anyformat()` reads:
- metadata
- numeric table
- whether the file is multi-trial

### 4. Trial selection
If the file contains multiple trials:
- it first checks `TRIAL_PREFERENCE`
- if none match, it picks the trial with the most usable data

### 5. Subject parsing
For each file, the script:
- extracts weight
- infers injured limb
- resamples all available series to 101 points
- computes lowest COM timing

### 6. Group matrix construction
For each panel and group, the script builds a subject-by-time matrix.

### 7. Summary statistics
The script computes mean and 95% CI for each panel.

### 8. Plot generation
`plot_panels()` draws the final 3×3 grids and saves the figures.

---

## Configuration guide

### Change groups
Edit:

```python
GROUP_KEYS = ["RET", "CTRL"]
GROUP_NAME_MAP = {...}
COLOR_MAP = {...}
```

### Change output filenames
Edit:

```python
OUT_ANGLES_PNG = "dvj_angles_contra.png"
OUT_MOMENTS_PNG = "dvj_moments_contra.png"
```

### Change limb selection
Edit:

```python
GROUP_LIMB_MODE = {
    "RET": "uninjured",
    "CTRL": "uninjured",
}
```

### Change panel layout
Edit:

```python
ANGLES_PANELS = [...]
MOMENTS_PANELS = [...]
```

### Change variable mapping
Edit:

```python
ANGLE_VARS = {...}
MOMENT_VARS = {...}
GRF_VARS_LR = [...]
COM_VAR = "Pelvis_COM_Z"
```

### Change directional labels
Edit:

```python
DIR_ANNOT = {...}
MANUAL_DIR_POS = {...}
```

### Change plot aesthetics
Edit:

```python
BAND_ALPHA = 0.18
LINE_WIDTH = 2.4
COM_TICK_COLOR = "#0a7d0a"
COM_GREY_ALPHA = 0.25
```

---

## Assumptions and limitations

- Input CSVs must follow the expected exported structure.
- Variable names must match the mappings exactly.
- The script currently expects left/right paired variables for most panels.
- The current trial preference list is task-specific for DVJ.
- The current panel set is not a complete biomechanics report; it is a configured subset.
- Confidence intervals are descriptive only; no inferential statistics are performed.
- Files that fail parsing are skipped with a console message.
- If weight is missing, moments and GRF are not converted to Nm / N.
- If injured side cannot be inferred, limb selection may fall back to averaging both sides depending on the mode and available data.

---

## Common failure points

### No CSVs found
Cause:
- wrong folder selected
- files not saved as `.csv`

### Wrong trial gets selected
Cause:
- trial names do not match `TRIAL_PREFERENCE`

Fix:
- update `TRIAL_PREFERENCE` for your task naming

### Limb selection looks wrong
Cause:
- injured side metadata missing or ambiguous

Fix:
- populate `MANUAL_INJURED_LIMB`

### Panel is blank
Cause:
- expected variable missing from CSV
- variable name mismatch
- all values are NaN

### Units look wrong
Cause:
- `Weight (kg)` missing or nonnumeric
- source moments / GRFs are not in the assumed normalized units

### COM shading seems off
Cause:
- `Pelvis_COM_Z` missing
- COM signal quality is poor
- timing is being averaged across heterogeneous trials

---

## Suggested improvements

Good next upgrades for this script:

- command-line arguments instead of Tkinter dialogs
- save summary CSVs alongside figures
- add inferential stats or SPM overlays
- create per-panel export options
- support more task templates
- support separate left/right plotting without code edits
- log failed files to a text report
- save metadata about included subjects and sample sizes
- make unit conversions explicit with config flags
- package the plotting pipeline into reusable functions or a module

---

## Example use cases

- ACLR vs control limb comparison figures
- contralateral limb biomechanics reporting
- re-tear cohort summary plotting
- manuscript or abstract figure generation
- fast QC of exported Qualisys time-series data
- standardized figure generation across repeated analyses

---

## Notes

This script is currently tuned to a **drop vertical jump contralateral comparison workflow**. Before reusing it for another task or cohort, verify:

- group definitions
- limb-selection logic
- trial names
- variable mappings
- metadata fields
- unit assumptions
- panel definitions
