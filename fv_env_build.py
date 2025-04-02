import os
import shutil
import json
import argparse
import re
import subprocess
from pathlib import Path
import vhdl_to_sv
import parse_sv

###############################################################################
# extract_module_blocks
#
# Reads a SystemVerilog file to find the top module parameters and ports.
# - top_name: The name of the top module we're looking for
# - returns: (parameters, ports) as strings
###############################################################################
def extract_module_blocks(top_file_path, top_name):
    ext = Path(top_file_path).suffix.lower()

    with open(top_file_path, "r") as f:
        content = f.read()

    # If VHDL file, convert to SystemVerilog-equivalent content first
    if ext == ".vhd":
        content = vhdl_to_sv.generate_sv_module(content, top_name)  # modifies content
        # print(f"VHDL converted into:\n\n{content}")

    print(content)
    # Now treat the content as SystemVerilog-style
    param_match = re.search(rf"module\s+{top_name}\s*#\((.*?)\)\s*\(", content, re.DOTALL)
    parameters = param_match.group(1).strip() if param_match else ""

    port_match = re.search(rf"module\s+{top_name}(?:\s*#\(.*?\))?\s*\((.*?)\);", content, re.DOTALL)
    # ports = port_match.group(1).strip() if port_match else ""
    ports = port_match.group(1) if port_match else ""


    # print("PARAMETERS AS A LIST -> \n")
    # print(parameters.splitlines())
    # print(type(content))
    # print(type(parameters))
    # print(type(ports))
    # for line in ports.splitlines():
    #     name, rng = parse_sv.extract_sv_signal_info(line)
    #     print(f"Signal: {name}, Range: {rng}")

    # print("PORTS AS A LIST -> \n")
    # print(ports.splitlines())


    return parameters, ports, content.splitlines()

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
def generate_interfaces(params, ports, interfaces_path):

    interfaces = parse_sv.parse_sv_interface_info(ports)

    # For each interface block found, create a <name>_port_intf.sv file
    for intf in interfaces:
        filename = interfaces_path / f"{intf['if_name']}_port_intf.sv"

        clean_signals = []
        # We'll define a macro like apb_port_intf_fields with each signal name
        macro_name = f"{intf['if_name']}_port_intf_fields"
        macro_line = f"    `define {macro_name} \\\n        "
        for i, (sig, rng) in enumerate(intf['content']):
            clean_signals.append(f"    logic {rng} {sig};\n")
            if i < len(intf['content']) - 1:
                macro_line += f"{sig}, "
            else:
                macro_line += f"{sig}\n"


        body = [f"interface {intf['if_name']}_port_intf;\n"]
        body.append(f"#(\n")
        for line in params:
            body.append(f"    {line.strip()}\n")
        body.append(f");\n")
        body.extend(clean_signals)

        # Format the macro on a single line with commas between signals
        # macro_line = f"    `define {macro_name} \\\n        " + ", ".join(signal_names) + "\n"
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
        
    return interfaces

###############################################################################
# generate_fv_adapter
#
# Reads the generated fv_env.sv to:
#   - Capture any parameters and port block
#   - Append interface declarations (.driver modports)
#   - Insert 'assign' lines that connect top-level signals to each interface
#   - Finally writes out fv_adapter.sv
###############################################################################
def generate_fv_adapter(parameters, ports, interfaces, fv_env_path, interfaces_path, fv_adapter_path):
    idented_parameters = ""
    for line in parameters.splitlines():
        idented_parameters += (f"  {line}\n")

    idented_ports = ""
    for line in ports.splitlines():
        idented_ports += (f"  {line}\n")

    fv_env_adapter = [
        "import fv_pkg::*;\n\n",
        "module fv_env\n",
        "  #(\n",
        f"  {idented_parameters}\n" if parameters else "",
        "  )\n",
        "  (\n",
        f"  {idented_ports}\n" if ports else "",
    ]

    for i, intf in enumerate(interfaces):
        if i < len(interfaces) - 1:
            intf_decl = f"  {intf['if_name']}_port_intf.driver {intf['if_name']}_port,\n"
        else:
            intf_decl = f"  {intf['if_name']}_port_intf.driver {intf['if_name']}_port\n"

        fv_env_adapter.append(f"  {intf_decl}")
    fv_env_adapter.append("  );\n\n")

    for intf in interfaces:
        # We'll add an assign line for each signal in the interface
        for sig, rng in intf['content']:
            # Format: assign apb_port.i_paddr = i_paddr;
            assign_line = f"  assign {intf['if_name']}_port.{sig} = {sig};\n"
            fv_env_adapter.append(assign_line)
    

    fv_env_adapter.append("endmodule\n")


    with open(fv_adapter_path, "w") as f:
        f.writelines(fv_env_adapter)

################################################################################
def generate_fv_package(parameters, fv_pkg_path):
    parameters_touple = parse_sv.parse_sv_parameters_info(parameters.splitlines())
    parameters_line = ""
    for i, (name, _) in enumerate(parameters_touple):
        if i < len(parameters_touple) - 1:
            parameters_line += f".{name}({name}), "
        else:
            parameters_line += f".{name}({name})"
    
    macro_line = f"    `define param_fields {parameters_line}\n"

    with open(fv_pkg_path, "w") as f:
        pkg_content = "package fv_pkg;\n\n"
        pkg_content += macro_line
        pkg_content += "endpackage\n"
        f.write(pkg_content)

################################################################################
def generate_fv_env_content(parameters, ports, interfaces, main_clk, reset, verif_path):
    idented_params = ""
    for line in parameters.splitlines():
        idented_params += (f"  {line}\n")

    idented_ports = ""
    for line in ports.splitlines():
        idented_ports += (f"  {line}\n")

    print(f"Ports:\n{idented_ports}")

    fv_env_content = [
        "import fv_pkg::*;\n\n",
        "module fv_env\n",
        "  #(\n",
        f"  {idented_params}\n" if parameters else "",
        "  )\n",
        "  (\n",
    ]
    fv_env_content.extend(idented_ports)
    fv_env_content.append("  );\n\n")
    fv_env_content.append(f"  default\n    clocking @(posedge {main_clk});\n  endclocking\n\n")
    fv_env_content.append(f"  default disable iff ({reset});\n\n")

    parameters_touple = parse_sv.parse_sv_parameters_info(parameters.splitlines())
    parameters_line = ""
    for i, (name, _) in enumerate(parameters_touple):
        if i < len(parameters_touple) - 1:
            parameters_line += f".{name}({name}), "
        else:
            parameters_line += f".{name}({name})"

    # Instantiate each discovered interface
    for intf in interfaces:
        fv_env_content.append(f"  {intf['if_name']}_port_intf #(`param_fields) {intf['if_name']}_port();\n")

    # Finally, the adapter instance, if the interfaces are present
    if bool(interfaces):
        fv_env_content.append("\n")
        fv_env_content.append("  fv_adapter fv_adapter(.*);\n")
    fv_env_content.append("endmodule\n")

    # Write fv_env.sv
    with open(verif_path / "fv_env.sv", "w") as f:
        f.writelines(fv_env_content)
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

    makefile_content = ["main:\n",
                        "\tjg ./scripts/fv_run.tcl &\n",
                        ".PHONY: clean\n",
                        "clean:\n",
                        "\trm -rf jgproject\n"
                       ]

    with open(prd_path / "Makefile", "w") as f:
        f.writelines(makefile_content)

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
    for f in rtl_path.glob("*.*"):
        with open(f, "r") as f_in:
            content = f_in.read()
            if re.search(rf"\bmodule\s+{top_name}\b", content) or re.search(rf"\bentity\s+{top_name}\b", content, re.IGNORECASE):
                top_file_path = f
                break
    
    print(f"Found top file: {top_file_path}")

    if top_file_path:
        parameters, ports, content = extract_module_blocks(top_file_path, top_name)
        print(ports)
        # Generate interface files from top module
        # has_interfaces = generate_interfaces_from_top(parameters, content, interfaces_path)
        interfaces = generate_interfaces(parameters.splitlines(), ports.splitlines(), interfaces_path)
        has_interfaces = bool(interfaces)
    else:
        parameters, ports = "", ""

    clk_name = clocks[0] if clocks else "clk"
    disable_reset = f"!{reset_name}" if reset_active_low else reset_name

    ########################
    # Add content to fv_env.sv
    ########################
    generate_fv_env_content(parameters, ports, interfaces, clk_name, disable_reset, verif_path)

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
    ext = Path(top_file_path).suffix.lower()

    language_flag = "-vhdl" if ext == ".vhd" else "-sv09"

    scripts_path = prd_path / "scripts"
    os.makedirs(scripts_path, exist_ok=True)
    reset_prefix = "!" if reset_active_low else ""

    fv_run_content = [
        "clear -all\n",
        "# analyze rtl\n",
        f"analyze {language_flag} rtl/rtl.f\n",
        "# analyze verif\n",
        "analyze -sv09 -f verif/verif.f\n\n",
        f"elaborate {language_flag} -top {top_name}\n"
    ]
    for clk in clocks:
        fv_run_content.append(f"clock {clk}\n")
    fv_run_content.append(f"reset {reset_prefix}{reset_name}\n")

    with open(scripts_path / "fv_run.tcl", "w") as f:
        f.writelines(fv_run_content)

    # Generate fv_adapter after fv_env is finalized
    generate_fv_adapter(
        parameters,
        ports,
        interfaces,
        fv_env_path=verif_path / "fv_env.sv",
        interfaces_path=interfaces_path,
        fv_adapter_path=verif_path / "fv_adapter.sv"
    )

    generate_fv_package(parameters, fv_pkg_path=verif_path / "fv_pkg.sv")

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
