# -----------------------------------------------------------
# AUTHOR --------> Francisco Contreras
# OFFICE --------> Senior VFX Compositor, Software Developer
# WEBSITE -------> https://vinavfx.com
# -----------------------------------------------------------
import os
import re


def get_frame_padding(filename):
    padding = re.search(r"(#+)|(%\d\d?d)|(%d)", filename)
    return padding.group(0) if padding else ""


def has_frame_padding(filename):
    return bool(get_frame_padding(filename))


def list_sequence_files(filename, frange=None):
    padding = get_frame_padding(filename)
    basename = os.path.basename(filename)
    if not padding:
        return [filename]

    prefix, suffix = basename.rsplit(padding, 1)
    no_padding = prefix + suffix
    no_number = "".join(
        character for character in no_padding if not character.isdigit()
    )
    dirname = os.path.dirname(filename)
    if not os.path.isdir(dirname):
        return []

    files = []
    for name in os.listdir(dirname):
        if prefix not in name or suffix not in name:
            continue
        candidate_no_number = "".join(
            character for character in name if not character.isdigit()
        )
        if len(candidate_no_number) != len(no_number):
            continue

        if frange is not None:
            pre = name[: len(prefix)]
            number = int(name.split(pre, 1)[1][: -len(suffix)])
            if number not in range(frange[0], frange[1] + 1):
                continue
        files.append(os.path.join(dirname, name))
    return files
