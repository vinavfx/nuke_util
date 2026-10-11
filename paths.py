# -----------------------------------------------------------
# AUTHOR --------> Francisco Contreras
# OFFICE --------> Senior VFX Compositor, Software Developer
# WEBSITE -------> https://vinavfx.com
# -----------------------------------------------------------
import os
import platform

import nuke  # type: ignore

if platform.system() in ("Linux", "Darwin"):
    user_path = os.path.expanduser("~")
else:
    user_path = os.environ["USERPROFILE"].replace("\\", "/")

nuke_path = user_path + "/.nuke"
vina_path = nuke_path + "/nuke_tools"


def get_user_home_path():
    return user_path


def get_nuke_tools_path():
    return vina_path


def get_nuke_user_path():
    return nuke_path


def get_nuke_executable_path():
    executable = "/opt/Nuke{}/nuke".format(nuke.NUKE_VERSION_STRING)
    if os.path.isfile(executable):
        return executable

    executable = "/usr/local/Nuke{}/Nuke{}.{}".format(
        nuke.NUKE_VERSION_STRING, nuke.NUKE_VERSION_MAJOR, nuke.NUKE_VERSION_MINOR
    )
    if os.path.isfile(executable):
        return executable

    return "C:/Program Files/Nuke{}/Nuke{}.{}.exe".format(
        nuke.NUKE_VERSION_STRING, nuke.NUKE_VERSION_MAJOR, nuke.NUKE_VERSION_MINOR
    )


def get_nuke_plugins_path():
    return os.path.dirname(get_nuke_executable_path()) + "/plugins"


def get_project_path():
    project_path = nuke.root().name()
    if project_path == "Root":
        return
    return project_path


def get_project_name(version=True):
    basename = os.path.basename(nuke.root().name())
    if basename == "Root":
        return "Untitled"
    if not version:
        return basename[::-1].split("v", 1)[-1][::-1][:-1]
    return basename[:-3]
