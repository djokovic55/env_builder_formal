#!/usr/bin/env python3

import argparse
import subprocess
import sys
# import argcomplete

# Define test rules
RULES = {
    "build_vhdl_top": {
        # Command to revert the environment for VHDL top module
        "revert_cmd": [
            "python3", "fv_env_build.py", "--revert",
            "--target_dir", "./test/vhdl/"
        ],
        # Command to build the environment for VHDL top module
        "build_cmd": [
            "python3", "fv_env_build.py",
            "--top", "top",
            "--clks", "clk",
            "--rst", "reset",
            "--target_dir", "./test/vhdl/"
        ]
    },
    "revert_vhdl": {
        # Command to only revert the environment for VHDL
        "revert_cmd": [
            "python3", "fv_env_build.py", "--revert",
            "--target_dir", "./test/vhdl/"
        ]
    },
    "build_sv_pixel": {
        # Command to revert the environment for SystemVerilog pixel module
        "revert_cmd": [
            "python3", "fv_env_build.py", "--revert",
            "--target_dir", "./test/sv/"
            ],
        # Command to build the environment for SystemVerilog pixel module
        "build_cmd": [
            "python3", "fv_env_build.py",
            "--top", "pixel_transmitter",
            "--clks", "i_f_clk_ao,i_txclkhs",
            "--rst", "i_reset_fclk_n",
            "--target_dir", "./test/sv/"
        ]
    },
    "revert_sv": {
        # Command to only revert the environment for SystemVerilog
        "revert_cmd": [
            "python3", "fv_env_build.py", "--revert",
            "--target_dir", "./test/sv/"
        ]
    }
}

def run_command(cmd, label):
    """
    Executes a shell command and prints the result.
    - cmd: List of command arguments to execute.
    - label: Description of the command being executed.
    """
    print(f"\n🔧 Running {label}: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=True,  # Raise an exception if the command fails
            stdout=subprocess.PIPE,  # Capture standard output
            stderr=subprocess.PIPE,  # Capture standard error
            universal_newlines=True  # Ensure output is treated as text
        )
        print("✅ Success")
        print(result.stdout)  # Print the command's standard output
    except subprocess.CalledProcessError as e:
        print("❌ Failed")
        print(e.stderr)  # Print the command's standard error
        sys.exit(1)  # Exit with an error code

def run_rule(rule_name):
    """
    Executes a test rule based on the provided rule name.
    - rule_name: Name of the rule to execute.
    """
    if rule_name not in RULES:
        print(f"❌ Unknown rule: {rule_name}")
        print(f"Available rules: {', '.join(RULES.keys())}")
        sys.exit(1)

    rule = RULES[rule_name]
    if "revert" in rule_name:
        # If the rule is a revert rule, only run the revert command
        run_command(rule["revert_cmd"], f"{rule_name} revert")
    else:
        # For build rules, run both revert and build commands
        run_command(rule["revert_cmd"], f"{rule_name} revert")
        run_command(rule["build_cmd"], f"{rule_name} build")

def main():
    """
    Main function to parse command-line arguments and execute the specified rule.
    """
    parser = argparse.ArgumentParser(description="Run environment builder tests.")
    parser.add_argument("rule", help=f"Test rule to run. Options: {', '.join(RULES.keys())}")
    # argcomplete.autocomplete(parser)  # Enable tab completion (commented out)
    args = parser.parse_args()

    # Execute the specified rule
    run_rule(args.rule)

if __name__ == "__main__":
    main()
