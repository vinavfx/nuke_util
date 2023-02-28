# Author: Francisco Jose Contreras Cuevas
# Office: VFX Artist - Senior Compositor
# Website: vinavfx.com

import re
import os


def is_absolute(filename):
    if '../' in filename:
        return False

    return True


def get_padding(filename):
    padding = re.search('(#+)|(%\d\d?d)|(%d)', filename)
    padding = padding.group(0) if padding else ""

    return padding


def get_extension(filename):
    if not '.' in filename:
        return ''

    return filename.split('.')[-1]


def get_version(filename):
    basename = os.path.basename(filename)
    current_version = basename.split('v')[-1].split('.')[0]

    if current_version.isnumeric():
        return int(current_version)

    return -1


def get_version_string(filename):
    basename = os.path.basename(filename)
    current_version = basename.split('v')[-1].split('.')[0].split('_')[0]

    if current_version.isnumeric():
        return 'v' + current_version

    return ''


def get_name(filename, version=False, padding=False, extension=False):
    basename = os.path.basename(filename)

    if version and padding and extension:
        return basename
    elif version and padding:
        return basename.rsplit('.', 1)[0]

    ext = get_extension(basename)
    padd = get_padding(basename)
    vers = get_version_string(basename)

    if not vers and not padd and not ext:
        return basename

    if vers:
        base = basename.split(vers)[0][:-1]
    elif padd:
        base = basename.split(padd)[0][:-1]
    else:
        base = basename.rsplit('.', 1)[0]

    str_version = '_' + vers if vers and version else ''
    str_padding = '_' + padd if padd and padding else ''
    str_extension = '.' + ext if ext and extension else ''

    return '{}{}{}{}'.format(base, str_version, str_padding, str_extension)


def get_basename(filename):
    return get_name(filename, version=True, padding=True)


def get_name_no_extension(filename):
    return get_name(filename, version=True, padding=True)


def get_name_no_padding(filename):
    return get_name(filename, version=True)


def get_fullname(filename):
    return get_basename(filename)


def get_padding_ext(filename):
    return get_padding(filename) + '.' + get_extension(filename)


def is_sequence(filename):
    if get_padding(filename):
        return True

    return False


def get_sequence(filename, frange=None):
    padding = get_padding(filename)
    basename = os.path.basename(filename)

    if not padding:
        return [filename]

    prefix, suffix = basename.rsplit(padding, 1)
    no_padding = prefix + suffix
    no_number = ''.join([i for i in no_padding if not i.isdigit()])

    dirname = os.path.dirname(filename)
    if not os.path.isdir(dirname):
        return []

    sequence_list = []

    for f in os.listdir(dirname):
        if not prefix in f or not suffix in f:
            continue

        _no_number = ''.join([i for i in f if not i.isdigit()])

        if not len(_no_number) == len(no_number):
            continue

        if not frange == None:
            pre = f[:len(prefix)]
            number = int(f.split(pre, 1)[1][:-len(suffix)])
            if not number in range(frange[0], frange[1] + 1):
                continue

        sequence_list.append(os.path.join(dirname, f))

    return sequence_list
