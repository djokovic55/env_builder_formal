import os
import shutil
import json
import argparse
import re
import subprocess
from pathlib import Path

def read_vhdl_generics(vhdl_content):
    # current_dir = Path(__file__).parent.resolve()

    # with open(current_dir / "top.vhd", "r") as f:
    #     vhdl_content = f.read()

    inside_generic = False
    vhdl_generic_lines = []

    for line in vhdl_content.splitlines():
        stripped = line.strip()

        if re.match(r"generic\s*\(", stripped, re.IGNORECASE):
            inside_generic = True
            continue

        if inside_generic and re.match(r"\)\s*;", stripped):
            inside_generic = False
            break

        if inside_generic:
            vhdl_generic_lines.append(stripped)

    return vhdl_generic_lines


def extract_param_name(line):
    if not line or line.strip().startswith("--"):
        return ""
    line = line.strip().rstrip(";")
    if ":" in line:
        return line.split(":")[0].strip()
    return ""


def extract_param_default_value(line):
    if not line or line.strip().startswith("--"):
        return ""
    match = re.search(r":=\s*(.*?);?$", line)
    return match.group(1).strip() if match else ""


def classify_vhdl_generic_lines(lines):
    classified_lines = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        param_name = extract_param_name(line)
        default_value = extract_param_default_value(line)

        if not stripped:
            classified_lines.append({
                "type": "empty",
                "name": "", "default": "", "value": ""
            })
        elif stripped.startswith("--"):
            classified_lines.append({
                "type": "comment",
                "name": "", "default": "", "value": stripped
            })
        elif ";" in stripped and i < len(lines) - 1:
            classified_lines.append({
                "type": "parameter",
                "name": param_name,
                "default": default_value,
                "value": stripped
            })
        else:
            classified_lines.append({
                "type": "last_parameter",
                "name": param_name,
                "default": default_value,
                "value": stripped
            })

    return classified_lines

def format_sv_parameters(classified_params):
    sv_param_lines = []
    for entry in classified_params:
        param_type = entry["type"]

        if param_type == "parameter":
            sv_param_lines.append(f"  parameter {entry['name']} = {entry['default']},")
        elif param_type == "last_parameter":
            sv_param_lines.append(f"  parameter {entry['name']} = {entry['default']}")
        elif param_type == "comment":
            sv_param_lines.append(f"  // {entry['value'].lstrip('--').strip()}")
        elif param_type == "empty":
            sv_param_lines.append("")

    return "\n".join(sv_param_lines)



def read_vhdl_port(vhdl_content):
    # # Current directory is considered the project root
    # current_dir = Path(__file__).parent.resolve()

    # with open(current_dir / "top.vhd", "r") as f:
    #     vhdl_content = f.read()

    # print(vhdl_content)

    inside_port = False
    vhdl_port_lines = []

    for line in vhdl_content.splitlines():
        stripped = line.strip()

        # Detect start of the port block
        if re.match(r"port\s*\(", stripped, re.IGNORECASE):
            inside_port = True
            continue

        # Detect end of port block
        if inside_port and re.match(r"\)\s*;", stripped):
            inside_port = False
            break

        # While inside the port block, store lines
        if inside_port:
            vhdl_port_lines.append(stripped)
        
    return vhdl_port_lines

# print("PORT LINES DETECTED:\n\n")
# for pl in read_vhdl_port():
#     print(pl)

def extract_signal_name(vhdl_port_line):
    signal_name = ""

    # Skip empty lines or comment-only lines
    if not vhdl_port_line or vhdl_port_line.strip().startswith("--"):
        return ""

    # Strip trailing semicolon if present
    vhdl_port_line = vhdl_port_line.strip().rstrip(";")

    # Split before the colon to extract the signal name
    if ":" in vhdl_port_line:
        name = vhdl_port_line.split(":")[0].strip()
        signal_name = name

    return signal_name

def extract_range(line):
    # Skip comments
    if line.strip().startswith("--"):
        return ""

    # Search for (...) with downto inside
    match = re.search(r"\((.*?)\)", line)
    if match:
        inside = match.group(1)
        if "downto" in inside:
            left, right = map(str.strip, inside.split("downto"))
            return f"[{left}:{right}]"
    return ""


def classify_vhdl_port_lines(lines):
    classified_lines = []
    # lines = port_block_raw.strip().split("\n")

    for line in lines:
        stripped = line.strip()
        signal_name = extract_signal_name(line)
        signal_range = extract_range(line)
        if not stripped:
            classified_lines.append({"type": "empty", "name": "", "range": "", "value": ""})
        elif stripped.startswith("--"):
            classified_lines.append({"type": "comment", "name": "", "range": "", "value": stripped})
        elif ";" in stripped:
            classified_lines.append({"type": "line", "name": signal_name, "range": signal_range, "value": stripped})
        else:
            classified_lines.append({"type": "last_line", "name": signal_name, "range": signal_range, "value": stripped})

    return classified_lines

def format_sv_ports(classified_ports):
    sv_port_list = []

    for entry in classified_ports:
        typ = entry["type"]
        name = entry["name"]
        rng = entry["range"]
        value = entry["value"]

        if typ == "line":
            # line = f"  input {rng + ' ' if rng else ''}{name:>25},"
            line = f"  input {rng} {name},"
        elif typ == "last_line":
            # line = f"  input {rng + ' ' if rng else ''}{name:>25};"
            line = f"  input {rng} {name}"
        elif typ == "comment":
            line = f"  //{value.lstrip('-')}"  # convert -- to //
        elif typ == "empty":
            line = ""
        else:
            line = value  # fallback

        sv_port_list.append(line)
    return sv_port_list

def generate_sv_module(vhdl_content, top_name="top"):

    vhdl_port_lines = read_vhdl_port(vhdl_content)
    vhdl_generic_lines = read_vhdl_generics(vhdl_content)
    classified_ports = classify_vhdl_port_lines(vhdl_port_lines)
    classified_params = classify_vhdl_generic_lines(vhdl_generic_lines)

    sv_module = []

    # Module header
    sv_module.append(f"module {top_name}")

    # Parameter block
    sv_module.append("  #(")
    sv_module.append(format_sv_parameters(classified_params))
    sv_module.append("  )")

    # Port block
    sv_module.append("  (")
    sv_module.extend(format_sv_ports(classified_ports))
    sv_module.append("  );")

    sv_module.append("endmodule")

    return "\n".join(sv_module)



# MAIN

if __name__ == "__main__":
    # Read VHDL port lines from the file
    vhdl_port_lines = read_vhdl_port()
    vhdl_generic_lines = read_vhdl_generics()

    # # Debug print
    # print("Extracted signal names:")
    # for line in vhdl_port_lines:
    #     print(extract_signal_name(line))

    # for line in vhdl_port_lines:
    #     range_str = extract_range(line)
    #     print(f"{line.strip()} -> {extract_range(line)}")

    classified_ports = classify_vhdl_port_lines(vhdl_port_lines)
    classified_params = classify_vhdl_generic_lines(vhdl_generic_lines)

    # for entry in classified_lines:
    #     print( f"Type: {entry['type']:>10} | Name: {entry['name']:>25} | Range: {entry['range']:>20}  Value: {entry['value']}")


    # Example usage:
    module_output = generate_sv_module(top_name="top")
    print("\nGenerated SystemVerilog Module:\n")
    print(module_output)
