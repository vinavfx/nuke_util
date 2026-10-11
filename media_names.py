# -----------------------------------------------------------
# AUTHOR --------> Francisco Contreras
# OFFICE --------> Senior VFX Compositor, Software Developer
# WEBSITE -------> https://vinavfx.com
# -----------------------------------------------------------
import os

from .sequences import get_frame_padding


def get_extension(filename):
    if "." not in filename:
        return ""
    return filename.split(".")[-1]


def get_version_tag(filename):
    basename = os.path.basename(filename)
    if "v" not in basename:
        return ""
    version = basename.split("v")[-1].split(".")[0].split("_")[0]
    if version.isdigit():
        return "v" + version
    return ""


def format_media_name(
    filename, version=False, padding=False, extension=False, fullpath=False
):
    basename = os.path.basename(filename)
    if version and padding and extension:
        return basename
    if version and padding:
        return basename.rsplit(".", 1)[0]

    ext = get_extension(basename)
    frame_padding = get_frame_padding(basename)
    version_tag = get_version_tag(basename)
    if not version_tag and not frame_padding and not ext:
        return basename

    if version_tag:
        base = basename.split(version_tag)[0][:-1]
    elif frame_padding:
        base = basename.split(frame_padding)[0][:-1]
    else:
        base = basename.rsplit(".", 1)[0]

    version_part = "_" + version_tag if version_tag and version else ""
    padding_part = "_" + frame_padding if frame_padding and padding else ""
    extension_part = "." + ext if ext and extension else ""
    name = "{}{}{}{}".format(base, version_part, padding_part, extension_part)
    if not fullpath:
        return name
    return os.path.join(os.path.dirname(filename), name)


def get_sequence_stem(filename, fullpath=False):
    return format_media_name(filename, version=True, fullpath=fullpath)
