# Formal Verification Environment Setup Tool

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Usage](#usage)
  - [Setting Up the Formal Verification Environment](#setting-up-the-formal-verification-environment)
  - [Reverting the Environment](#reverting-the-environment)
- [Script Workflow Summary](#script-workflow-summary)
- [Troubleshooting](#troubleshooting)
---

## Overview

This tool automates the setup of a formal verification environment for RTL designs. It organizes RTL files, generates necessary interface and adapter files, and creates the environment required for formal verification. Additionally, it provides a mechanism to revert all changes and restore the project to its original state.

---

## Features

### RTL File Organization
- Snapshots the original RTL files.
- Moves files into a dedicated `rtl` directory.
- Generates a file list (`rtl.f`) for RTL compilation.

### Verification Environment Generation
- Extracts top module parameters and ports (with optional VHDL-to-SystemVerilog conversion).
- Generates interface files using parsed port information.
- Creates essential verification files:
  - `fv_env.sv`: Sets up the formal verification environment.
  - `fv_adapter.sv`: Connects top-level signals to interface blocks.
  - `fv_pkg.sv`: Contains parameter macros.
  - `fv_bind.sv`: Binds the verification environment to the top module.
  - `verif.f`: Lists all verification files.
  - `fv_run.tcl`: TCL script to run the formal verification flow.

### Reversion Capability
- Restores the original file structure by moving RTL files back to the root.
- Cleans up all generated directories and files (e.g., `rtl`, `verif`, `scripts`, `Makefile`, etc.).

---

## Prerequisites

- **Python 3:** Ensure Python 3 is installed on your system.
- **Dependencies:**  
  The script uses standard Python libraries (`os`, `shutil`, `json`, `argparse`, `re`, `subprocess`, `pathlib`) and requires the custom modules:
  - `vhdl_to_sv` – for converting VHDL to SystemVerilog.
  - `parse_sv` – for parsing SystemVerilog parameters and interface signals.

  Ensure these custom modules are available in your project’s PYTHONPATH or in the same directory as the script.

---

## Usage

### Setting Up the Formal Verification Environment

Run the script with the following required arguments:

- `--top`: Name of the top module in your RTL design.
- `--clks`: Comma-separated list of clock signal names.
- `--rst`: Reset signal name.
- `--rst_active_low`: (Optional) Include this flag if the reset signal is active low.
- `--target_dir`: (Optional) The target directory containing your RTL files (default is the current directory).

#### Example Command

```bash
python setup_formal_env.py --top my_top_module --clks clk,rst_clk --rst reset --rst_active_low --target_dir /path/to/project
```

#### Script Workflow
1. **Snapshot your initial RTL file set.**
2. **Move RTL files** (with extensions `.sv`, `.v`, or `.vhd`) into the `rtl` directory.
3. **Create the file list** `rtl.f` and a `Makefile`.
4. **Generate verification directories** (`verif` with subdirectories `checkers` and `interfaces`, and `scripts`).
5. **Locate the top module file** and extract its parameters and ports.
6. **Generate interface files**, the formal environment (`fv_env.sv`), adapter (`fv_adapter.sv`), package (`fv_pkg.sv`), and binding (`fv_bind.sv`) files.
7. **Create a TCL script** (`fv_run.tcl`) for running the formal verification flow.

### Reverting the Environment

To revert all changes and restore the original project structure, run the script with the appropriate reversion flag. This will:
- Move RTL files back to their original locations.
- Delete all generated directories and files (e.g., `rtl`, `verif`, `scripts`, `Makefile`, etc.).

---

## Script Workflow Summary

1. **Snapshot & Organization:**  
   - Record original RTL files.
   - Move files into `rtl/` and generate `rtl.f`.
   
2. **Environment Generation:**  
   - Extract module blocks (parameters and ports) from the top module.
   - Generate interface files, formal environment, adapter, and package files.
   - Create the binding and verification file list.
   - Build the TCL script (`fv_run.tcl`) for running verification.
   
3. **Reversion:**  
   - Clean up generated files/directories.
   - Restore original RTL file structure.

---

## Troubleshooting

- **Module Not Found Errors:**  
  Ensure that the custom modules `vhdl_to_sv` and `parse_sv` are correctly installed or placed in the same directory as the script.

- **Incorrect Top Module Name:**  
  Verify that the top module name provided via `--top` exactly matches the module name in your RTL files.

- **File/Directory Issues:**  
  Make sure that the `--target_dir` exists and contains the RTL files to be processed.
