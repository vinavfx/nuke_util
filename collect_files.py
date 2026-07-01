# -----------------------------------------------------------
# AUTHOR --------> Francisco Contreras
# OFFICE --------> Senior VFX Compositor, Software Developer
# WEBSITE -------> https://vinavfx.com
# -----------------------------------------------------------
import os
import nuke  # type: ignore
import shutil

from .media_util import is_sequence, get_sequence, get_name_no_padding, get_extension
from .nuke_util import get_project_path

exclude_nodes = ["Write"]


def collect(relative_output=None):
    collected_files = ""
    count = 0

    nkfile = get_project_path()
    if not nkfile:
        nuke.message('Unsaved nk project!')
        return

    def file_inside_the_shot(filename):
        filename = filename.replace("//", "/")
        project_dir = os.path.dirname(nkfile)
        return project_dir in filename

    for node in get_nodes_with_files():
        for knob in node["knobs"]:
            filename = node["node"][knob].value()
            if file_inside_the_shot(filename):
                continue

            if is_sequence(filename):
                count += len(get_sequence(filename))
            else:
                count += 1

    progress = nuke.ProgressTask("Collect Files")
    section = 100.0 / count if count else 0
    percent = 0

    for n in get_nodes_with_files():
        node = n["node"]

        for file_knob_name in n["knobs"]:
            file_knob = node[file_knob_name]
            filename = file_knob.value()

            inside = file_inside_the_shot(filename)
            if inside:
                continue

            _is_sequence = is_sequence(filename)
            basename = os.path.basename(filename)
            dirname = os.path.basename(os.path.dirname(filename))

            if relative_output:
                assets_dir = os.path.join(os.path.dirname(nkfile), relative_output)
            else:
                asset_type = get_asset_type(filename, _is_sequence)
                assets_dir = os.path.join(
                    os.path.dirname(nkfile), 'assets', asset_type)

            if not os.path.isdir(assets_dir):
                os.makedirs(assets_dir)

            if _is_sequence:
                sequence = get_sequence(filename)
                sequence_dir = os.path.join(
                    assets_dir, dirname + "_" + get_name_no_padding(filename)
                )

                if not os.path.isdir(sequence_dir):
                    os.makedirs(sequence_dir)

                for frame in sequence:
                    dst = os.path.join(sequence_dir, os.path.basename(frame))
                    copy(frame, dst, as_link=True, force=True)

                    if progress.isCancelled():
                        break

                    percent += section
                    progress.setMessage("Copying: {0} ...".format(frame))
                    progress.setProgress(int(percent))

                new_filename = os.path.join(sequence_dir, basename)

            else:
                new_filename = "{}/{}_{}".format(assets_dir, dirname, basename)
                copy(filename, new_filename, as_link=True)

                percent += section
                progress.setMessage("Copying: {0} ...".format(filename))
                progress.setProgress(int(percent))

            file_knob.setValue(new_filename)
            collected_files += "{} - {}\n".format(node.name(), basename)

            if progress.isCancelled():
                break

        if progress.isCancelled():
            break

    del progress
    if not collected_files:
        nuke.message("No files to collect !")
        return

    collected_files = "Collected files:\n\n{}".format(collected_files)
    nuke.message(collected_files)


def get_nodes_with_files():
    knobs_files = ["file", "proxy", "vfield_file", "font"]
    nodes = []
    node_paths = []

    for node in nuke.allNodes(recurseGroups=True):
        if node.Class() in exclude_nodes:
            continue

        knobs = []
        for knob in knobs_files:
            if not knob in node.knobs():
                continue

            filename = node[knob].value()

            if not filename:
                continue

            if not type(filename) == str:
                continue

            if filename[0] == "[":
                continue

            knobs.append(knob)

        if not knobs:
            continue

        if node.fullName() in node_paths:
            continue

        node_paths.append(node.fullName())
        nodes.append({"node": node, "knobs": knobs})

    return nodes


def get_asset_type(filename, sequence):
    ext = get_extension(filename).lower()

    if sequence:
        type_name = "sequences"
    elif ext in ["jpg", "png", "exr", "jpeg", "tif", "tiff"]:
        type_name = "images"
    elif ext in ["mov", "mp4"]:
        if "stock" in filename.lower():
            type_name = "stocks"
        else:
            type_name = "videos"
    elif ext in ["obj", "abc", "fbx"]:
        type_name = "geo"
    elif ext in ["cube", "3dl", "cdl", "cc"]:
        type_name = "lut"
    else:
        type_name = "misc"

    return type_name


def copy(src, dst, as_link=False, force=False):
    if not os.path.isfile(src):
        return

    if os.path.isfile(dst) and not force:
        return

    if as_link:
        if os.path.isfile(dst):
            os.remove(dst)

        try:
            os.link(src, dst)
        except:
            shutil.copy(src, dst)
    else:
        shutil.copy(src, dst)

    return True
