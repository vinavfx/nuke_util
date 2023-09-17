# Author: Francisco Jose Contreras Cuevas
# Office: VFX Artist - Senior Compositor
# Website: vinavfx.com
import random
import os
import json
import subprocess
import platform

from .nuke_util import get_nuke_executable, get_user_path


def exec_function(function, args_data):

    if platform.system() == "Linux":
        tmp_dir = '/tmp'
    else:
        tmp_dir = '{}/AppData/Local/Temp'.format(get_user_path())

    tmp_script_file = '{}/submit_function_{}.py'.format(
        tmp_dir, int(random.random() * 1000000))

    tmp_script = '{}\n{}\n{}\n'.format(
        'import json',
        "data = json.loads('{}')".format(
            json.dumps(args_data).replace('\\', '\\\\')),
        '{}(data)'.format(function)
    )

    f = open(tmp_script_file, 'w')
    f.write(tmp_script)
    f.close()

    executable = get_nuke_executable()

    cmd = '"{}" -t {}'.format(executable, tmp_script_file)

    p = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _, _ = p.communicate()

    os.remove(tmp_script_file)
