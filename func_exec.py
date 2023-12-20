# -----------------------------------------------------------
# AUTHOR --------> Francisco Jose Contreras Cuevas
# OFFICE --------> Senior VFX Compositor, Software Developer
# WEBSITE -------> https://vinavfx.com
# -----------------------------------------------------------
import base64
import os
import random
import base64
import json
import subprocess

from .nuke_util import get_nuke_executable


def exec_function(function, data):

    tmp_script_file = '/tmp/submit_function_{}.py'.format(
        int(random.random() * 1000000))

    data_encoded = base64.b64encode(json.dumps(data).encode()).decode()

    tmp_script = (
        'import json',
        'import base64',
        'data = "{}"'.format(data_encoded),
        'data = json.loads(base64.b64decode(data.encode()).decode())',
        'print("__output__")',
        'ret = {}(data)'.format(function),
        'try:',
        '   encoded = base64.b64encode(json.dumps(ret).encode()).decode()',
        "   print('__return__{}'.format(encoded))",
        'except: pass'
    )

    tmp_script = '\n'.join(tmp_script)

    f = open(tmp_script_file, 'w')
    f.write(tmp_script)
    f.close()

    executable = get_nuke_executable()

    cmd = '"{}" -t {}'.format(executable, tmp_script_file)

    p = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    output, _ = p.communicate()
    os.remove(tmp_script_file)

    try:
        output_print = output.decode().split(
            '__output__')[-1].strip().split('__return__')[0]
        print(output_print)
    except:
        pass

    try:
        ret = output.decode().split('__return__')[-1]
        return json.loads(base64.b64decode(ret.encode()).decode())
    except:
        pass

    return {}
