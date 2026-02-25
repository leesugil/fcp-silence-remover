import xml.etree.ElementTree as ET
from tqdm import tqdm
import copy
from fractions import Fraction

from fcp_io import fcpxml_io
from . import parse_markers
from fcp_math import arithmetic
from fcp-marker-trimmer import trim
import intervalop

def get_unprotected_silences(silences: list[dict], protected: list[dict]) -> list[dict]:
    """
    silences: [{'start': 'xxxx/yyys', 'end': 'aaaa/bbs'}, ...]
    protected: [{'start': 'xxxx/yyys', 'end': 'aaaa/bbs'}, ...]

    output: [{'start': 'xxxx/yyys', 'end': 'aaaa/bbs'}, ...]
    """
    if not protected:
        return silences

    # Here the use of ditc2list and list2dict is okay because it's not meant to be used in precise final result but rough approximated comparison of intervals
    silences_list = arithmetic.dict2list(silences)
    protected_list = arithmetic.dict2list(protected)
    output_list = intervalop.excluding(silences_list, protected_list)
    output = arithmetic.list2dict(output_list)

    return output

def cell_division(spine, silence, fps='100/6000s', debug=False):
    """
    spine: XML ET spine element
    silence: {'start': 'xxx.yys', 'end': 'aaa.bbs'}
    fps: fps of the project clip (not necesarily the source clip)

    FCPXML language:
    start of asset-clip: start time of the asset-clip to be played in the timeline, not the start position of the clip in the spine timeline.
    offset of asset-clip: the start position of the clip in the spine timeline.
    duration: determines the length of the clip to be placed in the spine timeline.

    IMPORTANT:
    the start and end time of silence should be understood as the intrinsic timeline of the asset-clip, not the project timeline. the project timeline will constantly change each time cell-division is done, but all silences were measured before this cell-division-driven timeline messed up.
    """
    # pick up the last spine asset_clip
    # add a duplicate of the asset_clip
    # update the end of the first asset_clip
    # update the start of the second asset_clip
    # update the markers belonging to each clip
    # return nothing (input objects are mutable and passed by object reference

    # pick up the last spine asset_clip
    old_asset_clip = fcpxml_io.get_last_asset_clip(spine)

    # add a duplicate of the asset_clip
    new_asset_clip = copy.deepcopy(old_asset_clip)
    spine.append(new_asset_clip)

    # update the end of the first (old) asset_clip
    start = arithmetic.fcpsec2frac(old_asset_clip.get("start")) if old_asset_clip.get('start') else Fraction(0, 1)
    end = arithmetic.fcpsec2frac(silence['start'])
    duration = end - start
    if debug:
        print(f"old_asset_clip fps: {fps}, start: {old_asset_clip.get('start')}, start_frac: {start}, end: {silence['start']}, end_frac: {end}, duration: {duration}")
        print(f"old_asset_clip duration before: {old_asset_clip.get('duration')}, after: {duration}s")
    old_asset_clip.set('duration', f"{arithmetic.frac2fcpsec(duration, fps)}")

    # update the start of the second (new) asset_clip
    new_asset_clip.set('start', silence['end'])
    old_offset = arithmetic.fcpsec2frac(old_asset_clip.get('offset'))
    old_duration = arithmetic.fcpsec2frac(old_asset_clip.get('duration'))
    new_offset = old_offset + old_duration
    new_asset_clip.set('offset', f"{arithmetic.frac2fcpsec(new_offset, fps)}")

    # now adjust the duration of the new (second) asset_clip
    # first deduct the silence length from the current second duration here
    # now deduct old_duration from the current second duration here
    new_duration = arithmetic.fcpsec2frac(new_asset_clip.get('duration'))
    silence_start = arithmetic.fcpsec2frac(silence['start'])
    silence_end = arithmetic.fcpsec2frac(silence['end'])
    silence_duration = silence_end - silence_start
    reduced_duration = old_duration + silence_duration
    new_duration -= reduced_duration
    if debug:
        print(f"new_asset_clip duration before: {new_asset_clip.get('duration')}, after: {new_duration}s, silence_duration {silence_duration}s, old_duration: {old_duration}s")
    new_asset_clip.set('duration', f"{arithmetic.frac2fcpsec(new_duration, fps)}")

    # update the markers belonging to each clip
    trim.trim_markers(clip=old_asset_clip, fps=fps, debug=debug)
    trim.trim_markers(clip=new_asset_clip, fps=fps, debug=debug)

def blade_silence(root, silences, fps='100/6000s', debug=False):
    """
    silences: [{'start': 'xxxx/yyys', 'end': 'aaaa/bbs'}, ...]
    """
    spine = fcpxml_io.get_spine(root)

    sequence = root.find('.//sequence')
    original_timeline_duration = sequence.get('duration')
    original_timeline_duration = arithmetic.fcpsec2float(original_timeline_duration, fps)

    # Divide the spine asset_clip into multiple asset_clips
    for s in tqdm(silences):
        # for each silence,
        # pick up the last spine asset_clip
        # divide_cell it (does all the magic like dividing markers as well)
        cell_division(root=spine, silence=s, fps=fps, debug=debug)

    new_spine_duration = 0.0
    for c in spine:
        new_spine_duration += arithmetic.fcpsec2float(c.get('duration'))
    sequence.set('duration', f"{new_spine_duration}s")
