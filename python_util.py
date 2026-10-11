# -----------------------------------------------------------
# AUTHOR --------> Francisco Contreras
# OFFICE --------> Senior VFX Compositor, Software Developer
# WEBSITE -------> https://vinavfx.com
# -----------------------------------------------------------
import base64
import json
import subprocess
from collections import OrderedDict


def run_shell_command(cmd):
    process = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    out, err = process.communicate()

    try:
        out = out.decode()
    except UnicodeDecodeError:
        out = ""

    try:
        err = err.decode()
    except UnicodeDecodeError:
        err = ""

    return out, err


def write_text_file(file, text):
    with open(file, "w") as stream:
        stream.write(text)


def read_text_file(file):
    with open(file, "r") as stream:
        return stream.read().strip()


def read_json_file(file):
    return json.loads(read_text_file(file), object_pairs_hook=OrderedDict)


def encode_json_base64(data):
    return base64.b64encode(json.dumps(data).encode()).decode()


def decode_json_base64(data):
    return json.loads(base64.b64decode(data.encode()).decode())


def write_json_file(file, data):
    write_text_file(file, json.dumps(data, indent=4))
