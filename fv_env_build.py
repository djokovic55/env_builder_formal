import os
import shutil
import json
import argparse
import re
import subprocess
from pathlib import Path

###############################################################################
# extract_module_blocks
#
# Reads a SystemVerilog file to find the top module parameters and ports.
# - top_name: The name of the top module we're looking for
# - returns: (parameters, ports) as strings
###############################################################################
def extract_module_blocks(top_file_path, top_name):
    with open(top_file_path, "r") as f:
        content = f.read()

    # Use regex to capture the parameter block: module <top_name> #( ... ) (
    # This is optional, so we handle the case when there's no #(...)
    param_match = re.search(rf"module\s+{top_name}\s*#\((.*?)\)\s*\(", content, re.DOTALL)
    parameters = param_match.group(1).strip() if param_match else ""

    # Use regex to capture the port block: module <top_name> #( ... )? ( ... );
    port_match = re.search(rf"module\s+{top_name}(?:\s*#\(.*?\))?\s*\((.*?)\);", content, re.DOTALL)
    ports = port_match.group(1).strip() if port_match else ""

    return parameters, ports

###############################################################################
# generate_interfaces_from_top
#
# Scans the top module file for sections marked by "// XXX INTERFACE" lines.
# Each section defines signals relevant to an interface (e.g., APB, MEM).
# Generates a file <interface_name>_port_intf.sv for each interface, with:
#   - logic declarations
#   - a macro listing signals
#   - driver/monitor modports
###############################################################################
def generate_interfaces_from_top(top_file_path, interfaces_path):
    with open(top_file_path, "r") as f:
        lines = f.readlines()

    current_block = []
    interface_name = ""
    interfaces = {}
    inside_interface = False

    for line in lines:
        stripped = line.strip()

        # Detect lines like: "// APB INTERFACE"
        if stripped.startswith("//") and "INTERFACE" in stripped.upper():
            # If we were already collecting signals, store them first
            if inside_interface and interface_name and current_block:
                interfaces[interface_name] = current_block

            # Extract the name from the comment, e.g. "APB" -> "apb"
            match = re.match(r"//\s*(.*?)\s+INTERFACE", stripped, re.IGNORECASE)
            if match:
                interface_name = match.group(1).strip().lower().replace(" ", "_")
                current_block = []
                inside_interface = True
            continue

        # If we're inside a recognized interface block, collect signals until
        # we see another "//", a blank line, or a ");" that indicates the end.
        if inside_interface:
            if stripped.startswith("//") or stripped == "" or stripped == ");":
                if interface_name and current_block:
                    interfaces[interface_name] = current_block
                inside_interface = False
                interface_name = ""
                current_block = []
            elif re.match(r"^(input|output|inout|logic|wire|reg)", stripped):
                current_block.append(stripped)

    # If we ended on an interface block at EOF, store that last one
    if inside_interface and interface_name and current_block:
        interfaces[interface_name] = current_block

    # For each interface block found, create a <name>_port_intf.sv file
    for name, signals in interfaces.items():
        filename = interfaces_path / f"{name}_port_intf.sv"

        clean_signals = []
        signal_names = []
        for s in signals:
            # Remove trailing commas or semicolons, plus direction keywords
            code = s.split("//")[0].strip().rstrip(",;")
            code = re.sub(r"^(input|output|inout)\s+", "", code)

            # Example: "logic [31:0] data_i;" => "    logic [31:0] data_i;"
            clean_signals.append(f"    {code};\n")

            # Extract final token as the signal name for the macro
            tokens = code.split()
            if tokens:
                signal_names.append(tokens[-1])

        # We'll define a macro like apb_port_intf_fields with each signal name
        macro_name = f"{name}_port_intf_fields"

        body = [f"interface {name}_port_intf;\n"]
        body.extend(clean_signals)

        # Format the macro on a single line with commas between signals
        macro_line = f"    `define {macro_name} \\\n        " + ", ".join(signal_names) + "\n"
        body.append(macro_line)

        # Provide driver/monitor modports using the macro
        body += [
            f"    modport driver  (output `{macro_name});\n",
            f"    modport monitor (input `{macro_name});\n",
            "endinterface\n"
        ]

        # Write the interface file
        with open(filename, "w") as f:
            f.writelines(body)

###############################################################################
# generate_fv_adapter
#
# Reads the generated fv_env.sv to:
#   - Capture any parameters and port block
#   - Append interface declarations (.driver modports)
#   - Insert 'assign' lines that connect top-level signals to each interface
#   - Finally writes out fv_adapter.sv
###############################################################################
def generate_fv_adapter(fv_env_path, interfaces_path, fv_adapter_path):
    with open(fv_env_path, "r") as f:
        lines = f.readlines()

    param_block = []
    port_block = []
    inside_params = False
    inside_ports = False

    # Collect param and port blocks from fv_env.sv
    for line in lines:
        if "#(" in line:  # Start of parameter block
            inside_params = True
        if inside_params:
            param_block.append(line)
            # End param block if we see ")"
            if ")" in line and not line.strip().endswith(","):
                inside_params = False
            continue

        if "(" in line and not port_block:  # Start of port block
            inside_ports = True
        if inside_ports:
            port_block.append(line)
            if ");" in line:
                inside_ports = False
            continue

    # We'll parse previously generated interface files to see what signals they contain
    interface_decls = []
    assigns = []

    interface_files = sorted(interfaces_path.glob("*_port_intf.sv"))
    for file in interface_files:
        name = file.stem  # e.g. apb_port_intf
        instance = name.replace("_intf", "")  # e.g. apb_port
        macro = f"{name}_fields"

        # Read the macro line from the interface file to get signal names
        with open(file, "r") as f:
            content = f.read()

        # Look for something like: `define apb_port_fields \ i_paddr, i_psel ...
        macro_match = re.search(rf"`define {macro}\s+\\\n\s+(.*?)\n", content, re.DOTALL)
        if not macro_match:
            continue

        raw_line = macro_match.group(1)
        # Remove whitespace and split on comma
        signal_names = [s.strip() for s in raw_line.split(",") if s.strip()]

        # We'll declare the interface in the port list as:
        #   apb_port_intf.driver apb_port
        interface_decls.append(f"    {name}.driver {instance}")

        # For each signal, generate an assign line: assign apb_port.i_paddr = i_paddr;
        for sig in signal_names:
            assigns.append(f"  assign {instance}.{sig} = {sig};\n")

    # This step ensures that if the last line before ');' didn't have a comma,
    # we add one so that we can safely append interface ports
    if port_block and port_block[-1].strip() == ");":
        if len(port_block) >= 2:
            line = port_block[-2].rstrip()
            if '//' in line:
                code, comment = line.split('//', 1)
                code = code.rstrip()
                if not code.endswith(','):
                    code += ','
                port_block[-2] = f"{code} //{comment.strip()}\n"
            else:
                if not line.endswith(','):
                    line += ','
                port_block[-2] = line + "\n"

        # Remove the closing ');' temporarily
        port_block = port_block[:-1]

        # Add each interface port with a comma, except the last
        for i, decl in enumerate(interface_decls):
            comma = "," if i < len(interface_decls) - 1 else ""
            port_block.append(f"  {decl}{comma}\n")

        # Apply a small indent
        port_block = ["  " + line.lstrip() for line in port_block]

        # Re-add the final ');'
        port_block.append("  );\n")

    # Write out fv_adapter.sv
    with open(fv_adapter_path, "w") as f:
        f.write("module fv_adapter\n")
        if param_block:
            f.writelines(param_block)
        if port_block:
            f.writelines(port_block)
        f.write("\n")
        # Add the assign lines
        f.writelines(assigns)
        f.write("endmodule\n")

###############################################################################
# setup_formal_env
#
# The main entry point for building the environment:
#   - Creates a snapshot of which RTL files exist
#   - Moves them into rtl/
#   - Generates necessary directories (verif, interfaces, scripts...)
#   - Creates or fills fv_env.sv, fv_adapter.sv, Makefile, etc.
#   - Fully configures the formal environment based on top_name, clocks, reset
###############################################################################
def setup_formal_env(prd_path, top_name, clocks, reset_name, reset_active_low):
    prd_path = Path(prd_path).resolve()
    snapshot_file = prd_path / ".formal_env_snapshot.json"

    # Snapshot initial RTL file set
    initial_rtl_files = [
        str(f.name) for f in prd_path.glob("*.*")
        if f.suffix in [".sv", ".v", ".vhd"] and f.is_file()
    ]
    with open(snapshot_file, "w") as snap:
        json.dump(initial_rtl_files, snap)

    # Move all RTL files into prd_path/rtl
    rtl_path = prd_path / "rtl"
    os.makedirs(rtl_path, exist_ok=True)
    for file in prd_path.glob("*.*"):
        if file.suffix in [".sv", ".v", ".vhd"] and file.name != snapshot_file.name:
            shutil.move(str(file), rtl_path / file.name)

    # Create rtl.f which lists all moved RTL files
    with open(rtl_path / "rtl.f", "w") as f:
        for rtl_file in sorted(rtl_path.glob("*.*")):
            if rtl_file.name == "rtl.f":
                continue
            f.write(f"rtl/{rtl_file.name}\n")

    # Simple Makefile to run formal steps
    makefile_content = """main:
\tjg ./scripts/fv_run.tcl &
.PHONY: clean
clean:
\trm -rf jgproject
"""
    with open(prd_path / "Makefile", "w") as f:
        f.write(makefile_content)

    # Create verification directories (verif, checkers, interfaces)
    verif_path = prd_path / "verif"
    checkers_path = verif_path / "checkers"
    interfaces_path = verif_path / "interfaces"
    os.makedirs(checkers_path, exist_ok=True)
    os.makedirs(interfaces_path, exist_ok=True)

    # Touch some empty files
    for fname in ["fv_adapter.sv", "fv_pkg.sv"]:
        (verif_path / fname).touch()

    # Locate the top module file in rtl/
    top_file_path = None
    for f in rtl_path.glob("*.*"):
        with open(f, "r") as f_in:
            if re.search(rf"module\s+{top_name}\b", f_in.read()):
                top_file_path = f
                break

    if top_file_path:
        parameters, ports = extract_module_blocks(top_file_path, top_name)
        # Generate interface files from top module
        generate_interfaces_from_top(top_file_path, interfaces_path)
    else:
        parameters, ports = "", ""

    clk_name = clocks[0] if clocks else "clk"
    disable_reset = f"!{reset_name}" if reset_active_low else reset_name

    ########################
    # Convert all top ports to input, preserving comments
    ########################
    clean_ports = []
    for line in ports.splitlines():
        line = line.strip()
        if not line:
            continue

        # Keep pure comment lines or lines like 'input, //INTERFACE' untouched
        if line.startswith("//") or re.match(r"^(input|output|inout)\s*,?\s*//", line):
            clean_ports.append(f"  {line}\n")
            continue

        # Separate the code from an inline comment
        code = line.split("//")[0].strip().rstrip(",;")
        comment = "//" + line.split("//")[1].strip() if "//" in line else ""

        # Force direction to 'input'
        code = re.sub(r"^(input|output|inout)\s+", "", code)
        code = f"input {code}".strip()

        # If code becomes empty or comment only, just store it
        if code.startswith("//") or not code:
            clean_ports.append(f"  {code} {comment}".rstrip() + "\n")
        else:
            # Temporarily add comma at the end to unify our approach
            clean_ports.append(f"  {code}, {comment}".rstrip() + "\n")

    ########################
    # Format signal/comment lines properly:
    #   - No comma on the last signal
    #   - No comma for comment-only lines
    #   - 4-space indentation
    ########################
    last_signal_idx = None
    for i in range(len(clean_ports) - 1, -1, -1):
        line = clean_ports[i].strip()
        if not line or line.startswith("//") or re.match(r"^\s*input\s*,?\s*//", line):
            continue
        last_signal_idx = i
        break

    for i in range(len(clean_ports)):
        original = clean_ports[i].strip()

        if not original:
            clean_ports[i] = "\n"
            continue

        # Skip pure comment lines
        if original.startswith("//") or re.match(r"^\s*input\s*,?\s*//", original):
            clean_ports[i] = f"    {original}\n"
            continue

        # Split code from inline comment
        if "//" in original:
            code, comment = original.split("//", 1)
            code = code.rstrip().rstrip(",")
            comment = "//" + comment.strip()
        else:
            code = original.rstrip().rstrip(",")
            comment = ""

        # If this line is not the final signal, add a comma
        if i != last_signal_idx:
            code += ","

        # Rebuild line with 4-space indent
        line = f"    {code}"
        if comment:
            line += f" {comment}"
        clean_ports[i] = line + "\n"

    ########################
    # Build fv_env.sv
    ########################
    fv_env_content = [
        "module fv_env\n",
        "  #(\n",
        f"    {parameters}\n" if parameters else "",
        "  )\n",
        "  (\n",
    ]
    fv_env_content.extend(clean_ports)
    fv_env_content.append("  );\n\n")
    fv_env_content.append(f"  default\n    clocking @(posedge {clk_name});\n  endclocking\n\n")
    fv_env_content.append(f"  default disable iff ({disable_reset});\n\n")

    # Instantiate each discovered interface
    for file in sorted(interfaces_path.glob("*_port_intf.sv")):
        intf_type = file.stem
        inst_name = intf_type.replace("_intf", "")
        fv_env_content.append(f"  {intf_type} {inst_name}();\n")

    # Finally, the adapter instance
    fv_env_content.append("\n")
    fv_env_content.append("  fv_adapter fv_adapter(.*);\n")
    fv_env_content.append("endmodule\n")

    # Write fv_env.sv
    with open(verif_path / "fv_env.sv", "w") as f:
        f.writelines(fv_env_content)

    # Create fv_bind.sv binding fv_env to the top
    with open(verif_path / "fv_bind.sv", "w") as f:
        f.write(f"bind {top_name} fv_env fv_env(.*);\n")

    # Create checker.sv & dummy interface.sv
    (checkers_path / "checker.sv").touch()
    (interfaces_path / "interface.sv").touch()

    # verif.f includes all .sv in verif/ recursively
    with open(verif_path / "verif.f", "w") as f:
        for path in sorted(verif_path.rglob("*.sv")):
            f.write(f"{path.relative_to(prd_path)}\n")

    # Build scripts/fv_run.tcl
    scripts_path = prd_path / "scripts"
    os.makedirs(scripts_path, exist_ok=True)
    reset_prefix = "~" if reset_active_low else ""
    fv_run_content = [
        "clear -all\n",
        "# analyze rtl\n",
        "analyze -sv09 -f rtl/rtl.f\n",
        "# src\n\n",
        "# analyze verif\n",
        "analyze -sv09 -f verif/verif.f\n\n",
        f"elaborate -top {top_name}\n\n"
    ]
    for clk in clocks:
        fv_run_content.append(f"clock {clk}\n")
    fv_run_content.append(f"reset {reset_prefix}{reset_name}\n")

    with open(scripts_path / "fv_run.tcl", "w") as f:
        f.writelines(fv_run_content)

    # Generate fv_adapter after fv_env is finalized
    generate_fv_adapter(
        fv_env_path=verif_path / "fv_env.sv",
        interfaces_path=interfaces_path,
        fv_adapter_path=verif_path / "fv_adapter.sv"
    )

    print(f"Formal environment setup completed in: {prd_path}")

###############################################################################
# revert_formal_env
#
# Removes all generated files/folders and moves RTL files back to the root,
# effectively restoring the initial state (as per .formal_env_snapshot.json).
# Cross-platform safe: doesn't rely on 'make clean' on Windows.
###############################################################################
def revert_formal_env(prd_path):
    prd_path = Path(prd_path).resolve()

    # If a jgproject directory exists, remove it (instead of make clean)
    jgproject_path = prd_path / "jgproject"
    if jgproject_path.exists() and jgproject_path.is_dir():
        shutil.rmtree(jgproject_path, ignore_errors=True)
        print("Deleted: jgproject directory")
    else:
        print("No jgproject directory to clean.")

    # Check if we have a valid snapshot of initial files
    snapshot_file = prd_path / ".formal_env_snapshot.json"
    if not snapshot_file.exists():
        print("No snapshot found. Cannot revert.")
        return

    with open(snapshot_file, "r") as snap:
        initial_rtl_files = json.load(snap)

    # Move those RTL files from rtl/ back to the root
    rtl_path = prd_path / "rtl"
    for file_name in initial_rtl_files:
        src = rtl_path / file_name
        dst = prd_path / file_name
        if src.exists():
            shutil.move(str(src), dst)

    # Remove all environment directories and files
    paths_to_remove = [
        rtl_path / "rtl.f",
        prd_path / "rtl",
        prd_path / "verif",
        prd_path / "scripts",
        prd_path / "Makefile",
        snapshot_file
    ]

    for path in paths_to_remove:
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path, ignore_errors=True)

    print(f"Formal environment reverted in: {prd_path}")

###############################################################################
# Main - parse CLI arguments, call setup or revert
###############################################################################
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Formal environment setup or revert.")
    parser.add_argument("--revert", action="store_true", help="Revert the environment to the initial state")
    parser.add_argument("--top", type=str, help="Top module name")
    parser.add_argument("--clks", type=str, help="Comma-separated clock names")
    parser.add_argument("--rst", type=str, help="Reset signal name")
    parser.add_argument("--rst_active_low", action="store_true", help="Set if reset is active low")
    args = parser.parse_args()

    # Current directory is considered the project root
    current_dir = Path(__file__).parent.resolve()

    if args.revert:
        # Revert environment changes to the initial state
        revert_formal_env(current_dir)
    else:
        # On normal run, we need top, clks, and rst
        if not args.top or not args.clks or not args.rst:
            print("Error: --top, --clks, and --rst are required unless --revert is used.")
        else:
            # Convert comma-separated clocks into a list
            clocks = [clk.strip() for clk in args.clks.split(",") if clk.strip()]

            # Build the formal environment
            setup_formal_env(current_dir, args.top, clocks, args.rst, args.rst_active_low)
