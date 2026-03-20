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

The script is currently configured for a bilateral task using:

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

---

## License

MIT License

