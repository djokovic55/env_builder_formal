import os
import shutil
import json
import argparse
import re
import subprocess
from pathlib import Path

def extract_module_blocks(top_file_path, top_name):
    with open(top_file_path, "r") as f:
        content = f.read()

    param_match = re.search(rf"module\s+{top_name}\s*#\((.*?)\)\s*\(", content, re.DOTALL)
    parameters = param_match.group(1).strip() if param_match else ""

    port_match = re.search(rf"module\s+{top_name}(?:\s*#\(.*?\))?\s*\((.*?)\);", content, re.DOTALL)
    ports = port_match.group(1).strip() if port_match else ""

    return parameters, ports

def generate_interfaces_from_top(top_file_path, interfaces_path):
    with open(top_file_path, "r") as f:
        lines = f.readlines()

    current_block = []
    interface_name = ""
    interfaces = {}
    inside_interface = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("//") and "INTERFACE" in stripped.upper():
            if inside_interface and interface_name and current_block:
                interfaces[interface_name] = current_block
            match = re.match(r"//\s*(.*?)\s+INTERFACE", stripped, re.IGNORECASE)
            if match:
                interface_name = match.group(1).strip().lower().replace(" ", "_")
                current_block = []
                inside_interface = True
            continue

        if inside_interface:
            if stripped.startswith("//") or stripped == "" or stripped == ");":
                if interface_name and current_block:
                    interfaces[interface_name] = current_block
                inside_interface = False
                interface_name = ""
                current_block = []
            elif re.match(r"^(input|output|inout|logic|wire|reg)", stripped):
                current_block.append(stripped)

    if inside_interface and interface_name and current_block:
        interfaces[interface_name] = current_block

    for name, signals in interfaces.items():
        filename = interfaces_path / f"{name}_port_intf.sv"

        clean_signals = []
        signal_names = []
        for s in signals:
            code = s.split("//")[0].strip().rstrip(",;")
            code = re.sub(r"^(input|output|inout)\s+", "", code)
            clean_signals.append(f"    {code};\n")
            tokens = code.split()
            if tokens:
                signal_names.append(tokens[-1])

        macro_name = f"{name}_port_intf_fields"

        body = [f"interface {name}_port_intf;\n"]
        body.extend(clean_signals)

        macro_line = f"    `define {macro_name} \\\n        " + ", ".join(signal_names) + "\n"
        body.append(macro_line)

        body += [
            f"    modport driver  (output `{macro_name});\n",
            f"    modport monitor (input `{macro_name});\n",
            "endinterface\n"
        ]

        with open(filename, "w") as f:
            f.writelines(body)

def generate_fv_adapter(fv_env_path, interfaces_path, fv_adapter_path):
    # Read parameters and ports from fv_env.sv
    with open(fv_env_path, "r") as f:
        lines = f.readlines()

    param_block = []
    port_block = []
    inside_params = inside_ports = False

    for line in lines:
        if "#(" in line:
            inside_params = True
        if inside_params:
            param_block.append(line)
            if ")" in line and not line.strip().endswith(","):
                inside_params = False
            continue

        if "(" in line and not port_block:
            inside_ports = True
        if inside_ports:
            port_block.append(line)
            if ");" in line:
                inside_ports = False
            continue

    # Parse interfaces and their signals from macros
    interface_decls = []
    assigns = []

    interface_files = sorted(interfaces_path.glob("*_port_intf.sv"))
    for file in interface_files:
        name = file.stem  # e.g. apb_port_intf
        instance = name.replace("_intf", "")  # e.g. apb_port
        macro = f"{name}_fields"

        # Extract macro signals
        with open(file, "r") as f:
            content = f.read()

        macro_match = re.search(rf"`define {macro}\s+\\\n\s+(.*?)\n", content, re.DOTALL)
        if not macro_match:
            continue

        raw_line = macro_match.group(1)
        signal_names = [s.strip() for s in raw_line.split(",") if s.strip()]

        # Interface port declaration
        interface_decls.append(f"    {name}.driver {instance}")

        # Assignments
        for sig in signal_names:
            assigns.append(f"  assign {instance}.{sig} = {sig};\n")

    # Fix comma in last top-level port line (if not present)
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



        # Remove closing );
        port_block = port_block[:-1]

        # Add interface ports with commas (except last)
        for i, decl in enumerate(interface_decls):
            comma = "," if i < len(interface_decls) - 1 else ""
            port_block.append(f"  {decl}{comma}\n")

        # Normalize indent to 2 spaces
        port_block = ["  " + line.lstrip() for line in port_block]

        # Re-add final closing );
        port_block.append("  );\n")

    # Write fv_adapter.sv
    with open(fv_adapter_path, "w") as f:
        f.write("module fv_adapter\n")
        if param_block:
            f.writelines(param_block)
        if port_block:
            f.writelines(port_block)
        f.write("\n")
        f.writelines(assigns)
        f.write("endmodule\n")


# The rest of the script remains unchanged.

def setup_formal_env(prd_path, top_name, clocks, reset_name, reset_active_low):
    prd_path = Path(prd_path).resolve()
    snapshot_file = prd_path / ".formal_env_snapshot.json"

    initial_rtl_files = [str(f.name) for f in prd_path.glob("*.*") if f.suffix in [".sv", ".v", ".vhd"] and f.is_file()]
    with open(snapshot_file, "w") as snap:
        json.dump(initial_rtl_files, snap)

    rtl_path = prd_path / "rtl"
    os.makedirs(rtl_path, exist_ok=True)
    for file in prd_path.glob("*.*"):
        if file.suffix in [".sv", ".v", ".vhd"] and file.name != snapshot_file.name:
            shutil.move(str(file), rtl_path / file.name)

    with open(rtl_path / "rtl.f", "w") as f:
        for rtl_file in sorted(rtl_path.glob("*.*")):
            if rtl_file.name == "rtl.f":
                continue
            f.write(f"rtl/{rtl_file.name}\n")

    makefile_content = """main:
\tjg ./scripts/fv_run.tcl &
.PHONY: clean
clean:
\trm -rf jgproject
"""
    with open(prd_path / "Makefile", "w") as f:
        f.write(makefile_content)

    verif_path = prd_path / "verif"
    checkers_path = verif_path / "checkers"
    interfaces_path = verif_path / "interfaces"
    os.makedirs(checkers_path, exist_ok=True)
    os.makedirs(interfaces_path, exist_ok=True)

    for fname in ["fv_adapter.sv", "fv_pkg.sv"]:
        (verif_path / fname).touch()

    top_file_path = None
    for f in rtl_path.glob("*.*"):
        with open(f, "r") as f_in:
            if re.search(rf"module\s+{top_name}\b", f_in.read()):
                top_file_path = f
                break

    if top_file_path:
        parameters, ports = extract_module_blocks(top_file_path, top_name)
        generate_interfaces_from_top(top_file_path, interfaces_path)
    else:
        parameters, ports = "", ""

    clk_name = clocks[0] if clocks else "clk"
    disable_reset = f"!{reset_name}" if reset_active_low else reset_name

    # Force all ports to 'input' direction
    clean_ports = []
    for line in ports.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("//") or re.match(r"^(input|output|inout)\s*,?\s*//", line):
            # Keep pure comment lines untouched (including 'input, // INTERFACE NAME')
            clean_ports.append(f"  {line}\n")
            continue

        code = line.split("//")[0].strip().rstrip(",;")
        comment = "//" + line.split("//")[1].strip() if "//" in line else ""
        code = re.sub(r"^(input|output|inout)\s+", "", code)
        code = f"input {code}".strip()
        if code.startswith("//") or not code:
            clean_ports.append(f"  {code} {comment}".rstrip() + "\n")
        else:
            clean_ports.append(f"  {code}, {comment}".rstrip() + "\n")



    # Format signal and comment lines with proper commas and indentation
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

        # Skip comment-only lines
        if original.startswith("//") or re.match(r"^\s*input\s*,?\s*//", original):
            clean_ports[i] = f"    {original}\n"
            continue

        # Split code and comment
        if "//" in original:
            code, comment = original.split("//", 1)
            code = code.rstrip().rstrip(",")
            comment = "//" + comment.strip()
        else:
            code = original.rstrip().rstrip(",")
            comment = ""

        # Add comma only if it's not the last signal
        if i != last_signal_idx:
            code += ","

        # Format with 4-space indent
        line = f"    {code}"
        if comment:
            line += f" {comment}"
        clean_ports[i] = line + "\n"





    # Generate fv_env.sv
    fv_env_content = [
        "module fv_env\n",
        "  #(\n",
        f"{parameters}\n" if parameters else "",
        "  )\n",
        "  (\n",
    ]
    fv_env_content.extend(clean_ports)
    fv_env_content.append("  );\n\n")
    fv_env_content.append(f"  default\n    clocking @(posedge {clk_name});\n  endclocking\n\n")
    fv_env_content.append(f"  default disable iff ({disable_reset});\n\n")
    # Add interface instances
    for file in sorted(interfaces_path.glob("*_port_intf.sv")):
        intf_type = file.stem  # e.g., apb_port_intf
        inst_name = intf_type.replace("_intf", "")
        fv_env_content.append(f"  {intf_type} {inst_name}();\n")

    # Add adapter instance
    fv_env_content.append("\n")
    fv_env_content.append("  fv_adapter fv_adapter(.*);\n")
    fv_env_content.append("endmodule\n")

    with open(verif_path / "fv_env.sv", "w") as f:
        f.writelines(fv_env_content)

    with open(verif_path / "fv_bind.sv", "w") as f:
        f.write(f"bind {top_name} fv_env fv_env(.*);\n")

    (checkers_path / "checker.sv").touch()
    (interfaces_path / "interface.sv").touch()

    with open(verif_path / "verif.f", "w") as f:
        for path in sorted(verif_path.rglob("*.sv")):
            f.write(f"{path.relative_to(prd_path)}\n")

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

    generate_fv_adapter(
    fv_env_path=verif_path / "fv_env.sv",
    interfaces_path=verif_path / "interfaces",
    fv_adapter_path=verif_path / "fv_adapter.sv"
    )


    print(f"Formal environment setup completed in: {prd_path}")

def revert_formal_env(prd_path):
    prd_path = Path(prd_path).resolve()

    # try:
    #     subprocess.run(["make", "clean"], cwd=prd_path, check=True)
    #     print("Executed: make clean")
    # except subprocess.CalledProcessError as e:
    #     print(f"Warning: make clean failed or not defined. {e}")
    jgproject_path = prd_path / "jgproject"
    if jgproject_path.exists() and jgproject_path.is_dir():
        shutil.rmtree(jgproject_path, ignore_errors=True)
        print("Deleted: jgproject directory")
    else:
        print("No jgproject directory to clean.")


    snapshot_file = prd_path / ".formal_env_snapshot.json"
    if not snapshot_file.exists():
        print("No snapshot found. Cannot revert.")
        return

    with open(snapshot_file, "r") as snap:
        initial_rtl_files = json.load(snap)

    rtl_path = prd_path / "rtl"
    for file_name in initial_rtl_files:
        src = rtl_path / file_name
        dst = prd_path / file_name
        if src.exists():
            shutil.move(str(src), dst)

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Formal environment setup or revert.")
    parser.add_argument("--revert", action="store_true", help="Revert the environment to the initial state")
    parser.add_argument("--top", type=str, help="Top module name")
    parser.add_argument("--clks", type=str, help="Comma-separated clock names")
    parser.add_argument("--rst", type=str, help="Reset signal name")
    parser.add_argument("--rst_active_low", action="store_true", help="Set if reset is active low")
    args = parser.parse_args()

    current_dir = Path(__file__).parent.resolve()
    if args.revert:
        revert_formal_env(current_dir)
    else:
        if not args.top or not args.clks or not args.rst:
            print("Error: --top, --clks, and --rst are required unless --revert is used.")
        else:
            clocks = [clk.strip() for clk in args.clks.split(",") if clk.strip()]
            setup_formal_env(current_dir, args.top, clocks, args.rst, args.rst_active_low)
