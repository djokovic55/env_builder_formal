#!/usr/bin/env python3

import argparse
import subprocess
import sys
# import argcomplete

# Define test rules
RULES = {
    "build_vhdl_top": {
        "revert_cmd": [
            "python3", "fv_env_build.py", "--revert",
            "--target_dir", "./test/vhdl/"
        ],
        "build_cmd": [
            "python3", "fv_env_build.py",
            "--top", "top",
            "--clks", "clk",
            "--rst", "reset",
            "--target_dir", "./test/vhdl/"
        ]
    },
    "revert_vhdl": {
        "revert_cmd": [
            "python3", "fv_env_build.py", "--revert",
            "--target_dir", "./test/vhdl/"
        ]
    },
    "build_sv_pixel": {
        "revert_cmd": [
            "python3", "fv_env_build.py", "--revert",
            "--target_dir", "./test/sv/"
            ],
        "build_cmd": [
            "python3", "fv_env_build.py",
            "--top", "pixel_transmitter",
            "--clks", "i_f_clk_ao,i_txclkhs",
            "--rst", "i_reset_fclk_n",
            "--target_dir", "./test/sv/"
        ]
    },
    "revert_sv": {
        "revert_cmd": [
            "python3", "fv_env_build.py", "--revert",
            "--target_dir", "./test/sv/"
        ]
    }
}


def run_command(cmd, label):
    print(f"\n🔧 Running {label}: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True  # instead of text=True
        )
        print("✅ Success")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("❌ Failed")
        print(e.stderr)
        sys.exit(1)



def run_rule(rule_name):
    if rule_name not in RULES:
        print(f"❌ Unknown rule: {rule_name}")
        print(f"Available rules: {', '.join(RULES.keys())}")
        sys.exit(1)

    rule = RULES[rule_name]
    if "revert" in rule_name:
        run_command(rule["revert_cmd"], f"{rule_name} revert")
    else:
        run_command(rule["revert_cmd"], f"{rule_name} revert")
        run_command(rule["build_cmd"], f"{rule_name} build")


def main():
    parser = argparse.ArgumentParser(description="Run environment builder tests.")
    parser.add_argument("rule", help=f"Test rule to run. Options: {', '.join(RULES.keys())}")
    # argcomplete.autocomplete(parser)  # Enable tab completion
    args = parser.parse_args()

    run_rule(args.rule)


if __name__ == "__main__":
    main()
