# -----------------------------------------------------------
# AUTHOR --------> Francisco Contreras
# OFFICE --------> Senior VFX Compositor, Software Developer
# WEBSITE -------> https://vinavfx.com
# -----------------------------------------------------------
import colorsys


def pack_rgb_color(red, green, blue):
    return int("%02x%02x%02x%02x" % (red, green, blue, 1), 16)


def pack_hsv_color(hsv):
    rgb = colorsys.hsv_to_rgb(*hsv)
    return pack_rgb_color(*(int(channel * 255) for channel in rgb))


def set_tile_color_hsv(node, hsv):
    node["tile_color"].setValue(pack_hsv_color(hsv))


def get_tile_color_hsv(node):
    value = node["tile_color"].value()
    if not value:
        return [0, 0, 0]

    red = ((value >> 24) & 0xFF) / 255.0
    green = ((value >> 16) & 0xFF) / 255.0
    blue = ((value >> 8) & 0xFF) / 255.0
    return list(colorsys.rgb_to_hsv(red, green, blue))


def set_note_font_color_hsv(node, hsv):
    node["note_font_color"].setValue(pack_hsv_color(hsv))


def set_tile_color_hex(node, hx, intensity=1.0, sat=1.0):
    if not hx:
        node["tile_color"].setValue(0)
        return

    hx = hx[1:]
    if len(hx) == 3:
        hx = "".join(character * 2 for character in hx)

    pairs = (hx[0:2], hx[2:4], hx[4:6])
    channels = [int(pair, 16) * intensity for pair in pairs]
    average = sum(channels) / 3.0
    channels = [int((channel - average) * sat + average) for channel in channels]
    node["tile_color"].setValue(pack_rgb_color(*channels))
