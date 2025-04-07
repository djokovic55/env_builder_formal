import os
import shutil
import json
import argparse
import re
import subprocess
from pathlib import Path

def read_vhdl_generics(vhdl_content):
    """
    Extract the generic block from the VHDL content.
    """
    inside_generic = False
    vhdl_generic_lines = []

    for line in vhdl_content.splitlines():
        stripped = line.strip()

        # Detect the start of the generic block
        if re.match(r"generic\s*\(", stripped, re.IGNORECASE):
            inside_generic = True
            continue

        # Detect the end of the generic block
        if inside_generic and re.match(r"\)\s*;", stripped):
            inside_generic = False
            break

        # Collect lines inside the generic block
        if inside_generic:
            vhdl_generic_lines.append(stripped)

    return vhdl_generic_lines

def extract_param_name(line):
    """
    Extract the parameter name from a VHDL generic line.
    """
    if not line or line.strip().startswith("--"):  # Skip empty or comment lines
        return ""
    line = line.strip().rstrip(";")  # Remove trailing semicolon
    if ":" in line:  # Split before the colon to get the name
        return line.split(":")[0].strip()
    return ""

def extract_param_default_value(line):
    """
    Extract the default value of a parameter from a VHDL generic line.
    """
    if not line or line.strip().startswith("--"):  # Skip empty or comment lines
        return ""
    match = re.search(r":=\s*(.*?);?$", line)  # Match the default value after :=
    return match.group(1).strip() if match else ""

def classify_vhdl_generic_lines(lines):
    """
    Classify VHDL generic lines into categories: parameter, last_parameter, comment, or empty.
    """
    classified_lines = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        param_name = extract_param_name(line)
        default_value = extract_param_default_value(line)

        if not stripped:  # Empty line
            classified_lines.append({
                "type": "empty",
                "name": "", "default": "", "value": ""
            })
        elif stripped.startswith("--"):  # Comment line
            classified_lines.append({
                "type": "comment",
                "name": "", "default": "", "value": stripped
            })
        elif ";" in stripped and i < len(lines) - 1:  # Parameter line
            classified_lines.append({
                "type": "parameter",
                "name": param_name,
                "default": default_value,
                "value": stripped
            })
        else:  # Last parameter line
            classified_lines.append({
                "type": "last_parameter",
                "name": param_name,
                "default": default_value,
                "value": stripped
            })

    return classified_lines

def format_sv_parameters(classified_params):
    """
    Format classified VHDL generic lines into SystemVerilog parameter declarations.
    """
    sv_param_lines = []
    for entry in classified_params:
        param_type = entry["type"]

        if param_type == "parameter":  # Regular parameter
            sv_param_lines.append(f"  parameter {entry['name']} = {entry['default']},")
        elif param_type == "last_parameter":  # Last parameter without a trailing comma
            sv_param_lines.append(f"  parameter {entry['name']} = {entry['default']}")
        elif param_type == "comment":  # Comment line
            sv_param_lines.append(f"  // {entry['value'].lstrip('--').strip()}")
        elif param_type == "empty":  # Empty line
            sv_param_lines.append("")

    return "\n".join(sv_param_lines)

def read_vhdl_port(vhdl_content):
    """
    Extract the port block from the VHDL content.
    """
    inside_port = False
    vhdl_port_lines = []

    for line in vhdl_content.splitlines():
        stripped = line.strip()

        # Detect the start of the port block
        if re.match(r"port\s*\(", stripped, re.IGNORECASE):
            inside_port = True
            continue

        # Detect the end of the port block
        if inside_port and re.match(r"\)\s*;", stripped):
            inside_port = False
            break

        # Collect lines inside the port block
        if inside_port:
            vhdl_port_lines.append(stripped)
        
    return vhdl_port_lines

def extract_signal_name(vhdl_port_line):
    """
    Extract the signal name from a VHDL port line.
    """
    if not vhdl_port_line or vhdl_port_line.strip().startswith("--"):  # Skip empty or comment lines
        return ""
    vhdl_port_line = vhdl_port_line.strip().rstrip(";")  # Remove trailing semicolon
    if ":" in vhdl_port_line:  # Split before the colon to get the signal name
        return vhdl_port_line.split(":")[0].strip()
    return ""

def extract_range(line):
    """
    Extract the range (e.g., downto) from a VHDL port line.
    """
    if line.strip().startswith("--"):  # Skip comments
        return ""
    match = re.search(r"\((.*?)\)", line)  # Match content inside parentheses
    if match:
        inside = match.group(1)
        if "downto" in inside:  # Check for downto keyword
            left, right = map(str.strip, inside.split("downto"))
            return f"[{left}:{right}]"
    return ""

def classify_vhdl_port_lines(lines):
    """
    Classify VHDL port lines into categories: line, last_line, comment, or empty.
    """
    classified_lines = []

    for line in lines:
        stripped = line.strip()
        signal_name = extract_signal_name(line)
        signal_range = extract_range(line)
        if not stripped:  # Empty line
            classified_lines.append({"type": "empty", "name": "", "range": "", "value": ""})
        elif stripped.startswith("--"):  # Comment line
            classified_lines.append({"type": "comment", "name": "", "range": "", "value": stripped})
        elif ";" in stripped:  # Regular port line
            classified_lines.append({"type": "line", "name": signal_name, "range": signal_range, "value": stripped})
        else:  # Last port line without a trailing semicolon
            classified_lines.append({"type": "last_line", "name": signal_name, "range": signal_range, "value": stripped})

    return classified_lines

def format_sv_ports(classified_ports):
    """
    Format classified VHDL port lines into SystemVerilog port declarations.
    """
    sv_port_list = []

    for entry in classified_ports:
        typ = entry["type"]
        name = entry["name"]
        rng = entry["range"]
        value = entry["value"]

        if typ == "line":  # Regular port line
            line = f"  input {rng} {name},"
        elif typ == "last_line":  # Last port line without a trailing comma
            line = f"  input {rng} {name}"
        elif typ == "comment":  # Comment line
            line = f"  //{value.lstrip('-')}"  # Convert -- to //
        elif typ == "empty":  # Empty line
            line = ""
        else:
            line = value  # Fallback for unexpected cases

        sv_port_list.append(line)
    return sv_port_list

def generate_sv_module(vhdl_content, top_name="top"):
    """
    Generate a SystemVerilog module from VHDL content.
    """
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

    # End of module
    sv_module.append("endmodule")

    return "\n".join(sv_module)

if __name__ == "__main__":
    # Example usage
    # Replace with actual VHDL content as needed
    vhdl_content = """
    generic (
        WIDTH : integer := 8;
        DEPTH : integer := 16
    );
    port (
        clk : in std_logic;
        rst : in std_logic;
        data_in : in std_logic_vector(WIDTH-1 downto 0);
        data_out : out std_logic_vector(WIDTH-1 downto 0)
    );
    """
    module_output = generate_sv_module(vhdl_content, top_name="top")
    print("\nGenerated SystemVerilog Module:\n")
    print(module_output)
