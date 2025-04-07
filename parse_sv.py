import re

def parse_sv_signal_info(line):
    # Remove inline comments
    line = line.split("//")[0].strip()

    # Remove trailing comma/semicolon and extra spaces
    line = line.rstrip(",;").strip()

    # Check if line starts with 'input' (possibly with 'logic' or 'wire' etc.)
    if not line.startswith("input"):
        return None, None

    # Remove "input" and possibly "logic" or "wire" keywords
    tokens = line.split()
    tokens = [tok for tok in tokens if tok not in {"input", "logic", "wire", "reg"}]

    # If there's a range in brackets (e.g., [31:0])
    if tokens and tokens[0].startswith("["):
        range_str = tokens[0]  # Keep brackets included
        name = tokens[1] if len(tokens) > 1 else None  # Signal name follows the range
    else:
        range_str = ""  # No range specified
        name = tokens[0] if tokens else None  # Signal name is the first token

    return name, range_str

def parse_sv_parameters_info(param_block):
    """
    Given a SystemVerilog parameter block string,
    extract (name, default_value) pairs.
    """
    param_list = []

    for line in param_block:
        # Remove trailing commas and comments
        line = line.split('//')[0].strip().rstrip(',')

        # Remove the "parameter" keyword if present
        if line.startswith("parameter"):
            line = line[len("parameter"):].strip()

        # Split the line into name and default value if "=" is present
        if "=" in line:
            name, default = line.split("=", 1)
            param_list.append((name.strip(), default.strip()))

    return param_list

def parse_sv_interface_info(port_lines):
    """
    Parse SystemVerilog interface information from a list of port lines.
    Extract interface names and their associated signals.
    """
    interfaces = []  # List to store parsed interfaces
    current_if = None  # Current interface being processed
    inside_interface = False  # Flag to indicate if inside an interface block

    for line in port_lines:
        stripped = line.strip()

        # Detect interface comment lines (e.g., "// <name> INTERFACE")
        if stripped.startswith("//") and "INTERFACE" in stripped.upper():
            # Close the previous interface if one exists
            if current_if:
                interfaces.append(current_if)
            # Start a new interface
            match = re.match(r"//\s*(.*?)\s+INTERFACE", stripped, re.IGNORECASE)
            if match:
                if_name = match.group(1).strip().lower().replace(" ", "_")  # Normalize interface name
                current_if = {
                    "if_name": if_name,
                    "content": []  # List to store signals in the interface
                }
                inside_interface = True
            continue

        # End of interface block (detected by empty lines, comments, or closing parenthesis)
        if inside_interface and (stripped.startswith("//") or stripped == "" or stripped == ");"):
            if current_if:
                interfaces.append(current_if)  # Add the current interface to the list
                current_if = None  # Reset current interface
            inside_interface = False
            continue

        # If inside an interface block and the line is a signal declaration
        if inside_interface and stripped.startswith("input"):
            # Extract signal name and range using the helper function
            sig_name, sig_range = parse_sv_signal_info(line)

            # Add the signal to the current interface's content
            current_if["content"].append((sig_name, sig_range))

    # In case the last interface wasn't closed, add it to the list
    if current_if:
        interfaces.append(current_if)

    return interfaces

if __name__ == "__main__":
    # Example port lines to parse
    port_lines = [
        "  input  clk,",
        "  input  reset,",
        "",
        "  // ex_reg INTERFACE",
        "  input  pb_irq_i,",
        "  input [ADDR_WIDTH-1:0] pb_addr_in_i,",
        "  input [3:0] pb_byte_cnt_i,",
        "  input [3:0] pb_pkt_type_i,",
        "  input  pb_ecc_en_i,",
        "  input  pb_crc_en_i,",
        "  input [1:0] pb_ins_ecc_err_i,",
        "  input  pb_ins_crc_err_i,",
        "  input [3:0] pb_ecc_val_i,",
        "  input [7:0] pb_crc_val_i,",
        "  input [2:0] pb_sop_val_i,",
        "  input [3:0] pb_data_sel_i,",
        "  input [DATA_WIDTH-1:0] pb_addr_out_i,",
        "",
        "  input  pp_irq_i,",
        "  input [ADDR_WIDTH-1:0] pp_addr_hdr_i,",
        "  input  pp_ignore_ecc_err_i,",
        "",
        "  // inmem port B top interface, used for memory configuration",
        "  input  inmem_en_b_i,",
        "  input [31:0] inmem_data_b_i,",
        "  input [13:0] inmem_addr_b_i,",
        "  input [3:0] inmem_we_b_i,",
        "  input [31:0] inmem_data_b_o",
        "  );",
        "endmodule"
    ]

    # Parse the interfaces from the port lines
    interfaces = parse_sv_interface_info(port_lines)
    for intf in interfaces:
        print(f"Interface: {intf['if_name']}")
        for sig, rng in intf['content']:
            print(f"  {sig} {rng}")
