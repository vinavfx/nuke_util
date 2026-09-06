import os
import subprocess


def load_bash_environment(script_path):
    script_path = os.path.expanduser(script_path)
    output = subprocess.check_output(
        ["bash", "-c", 'source "$1" && env -0', "bash", script_path],
        text=True,
    )

    for entry in output.split("\0"):
        name, separator, value = entry.partition("=")
        if separator:
            os.environ[name] = value
