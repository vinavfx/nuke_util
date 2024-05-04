# -----------------------------------------------------------
# AUTHOR --------> Francisco Contreras
# OFFICE --------> Senior VFX Compositor, Software Developer
# WEBSITE -------> https://vinavfx.com
# -----------------------------------------------------------
import nuke  # type: ignore


def set_channels(shuffle, channel_in='rgba', channel_out='rgba'):
    for n in [channel_in, channel_out]:
        if n in nuke.layers():
            continue

        nuke.Layer(n, ['{}.red'.format(n), '{}.green'.format(
            n), '{}.blue'.format(n), '{}.alpha'.format(n)])

    shuffle.knob('in').setValue(channel_in)
    shuffle.knob('in2').setValue('none')
    shuffle.knob('out').setValue(channel_out)

    for ch in ['red', 'green', 'blue', 'alpha']:
        if hasattr(shuffle, 'node'):
            shuffle.node[ch].setValue(ch)
        else:
            shuffle[ch].setValue(ch)
