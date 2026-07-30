# -----------------------------------------------------------
# AUTHOR --------> Francisco Contreras
# OFFICE --------> Senior VFX Compositor, Software Developer
# WEBSITE -------> https://vinavfx.com
# -----------------------------------------------------------
import json
import os
import random
import string
import subprocess
import shutil
import base64
from collections import OrderedDict


def sh(cmd):
    p = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    out, err = p.communicate()

    try:
        out = out.decode()
    except UnicodeDecodeError:
        out = ""

    try:
        err = err.decode()
    except UnicodeDecodeError:
        err = ""

    return out, err


def fwrite(file, date):
    f = open(file, "w")
    f.write(date)
    f.close()


def fread(file):
    f = open(file, "r")
    readed = str(f.read().strip())
    f.close()

    return readed


def jread(file):
    return json.loads(fread(file), object_pairs_hook=OrderedDict)


def jprint(data):
    formatted = json.dumps(data, indent=4)
    print(formatted)


def encode(data):
    return base64.b64encode(json.dumps(data).encode()).decode()


def decode(data):
    return json.loads(base64.b64decode(data.encode()).decode())


def jwrite(file, data):
    info = json.dumps(
        data,
        indent=4,
    )

    fwrite(file, info)


def hash_generator(keyLen):
    def base_str():
        return string.ascii_letters + string.digits

    keylist = [random.choice(base_str()) for _ in range(keyLen)]
    return "".join(keylist)


def makedirs(directory):
    if not os.path.isdir(directory):
        os.makedirs(directory)


def makedir(directory):
    if not os.path.isdir(directory):
        os.mkdir(directory)


def recursive_rename(directory, src_name, dst_name):
    for root, dirs, files in os.walk(directory, topdown=False):
        for f in files:
            if src_name not in f:
                continue

            name = f.replace(src_name, dst_name)

            src = os.path.join(root, f)
            dst = os.path.join(root, name)

            shutil.move(src, dst)

        for d in dirs:
            if src_name not in d:
                continue

            name = d.replace(src_name, dst_name)

            src = os.path.join(root, d)
            dst = os.path.join(root, name)

            shutil.move(src, dst)


def get_folder_size(folder_path):
    total_size = 0
    for dirpath, _, filenames in os.walk(folder_path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            total_size += os.path.getsize(filepath)

    return round(float(total_size) / float(1024**3), 1)  # GB


def ln_tree(src, dst):
    os.makedirs(dst)

    for name in os.listdir(src):
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)

        if os.path.isdir(srcname):
            ln_tree(srcname, dstname)
        else:
            os.link(srcname, dstname)
