import xml.etree.ElementTree as ET
from tqdm import tqdm
import copy
from fractions import Fraction

from fcp_io import fcpxml_io
from . import parse_markers
from fcp_math import arithmetic
from fcp_marker_trimmer import trim
import intervalop

def get_unprotected_silences(silences: list[dict], protected: list[dict], cut_silence: bool=False) -> list[dict]:
    """
    silences: [{'start': 'xxxx/yyys', 'end': 'aaaa/bbs'}, ...]
    protected: [{'start': 'xxxx/yyys', 'end': 'aaaa/bbs'}, ...]

    output: [{'start': 'xxxx/yyys', 'end': 'aaaa/bbs'}, ...]

    Note that the timestamps are local to the source media, not necessarilly matching to the global timeline in the Project Spine.
    """
    if not protected:
        return silences

    # Here the use of ditc2list and list2dict is okay because it's not meant to be used in precise final result but rough approximated comparison of intervals
    silences_list = arithmetic.dict2list(silences)
    protected_list = arithmetic.dict2list(protected)
    output_list = []
    if cut_silence:
        output_list = intervalop.set_differences(silences_list, protected_list)
    else:
        output_list = intervalop.excluding(silences_list, protected_list)

    # proof
    for o in output_list:
        assert o[0] < o[1], f"Is this silence interval okay? {o}"

    output = arithmetic.list2dict(output_list)

    return output

def cell_division(asset_clip, spine, silence, fps='100/6000s', debug=False):
    """
    spine: XML ET spine element
    silence: {'start': 'xxx.yys', 'end': 'aaa.bbs'}
    fps: fps of the project clip (not necesarily the source clip)
    Note that silence is in the local source media (asset-clip) time, not in the global spine time.

    Returns the remaining asset_clip to further work on cell_division in the parent loop.

    FCPXML language:
    start of asset-clip: local start time of the asset-clip to be played in the global timeline, not the start position of the clip in the global spine timeline.
    offset of asset-clip: the start position of the clip in the global spine timeline.
    duration: determines the length of the clip to be placed in the global spine timeline.

    IMPORTANT:
    the start and end time of silence should be understood as the intrinsic timeline of the asset-clip, not the project timeline. the project timeline will constantly change each time cell-division is done, but all silences were measured before this cell-division-driven timeline messed up.
    """
    # take asset_clip as the object
    # add a duplicate of the asset_clip
    # update the end of the first asset_clip
    # update the start of the second asset_clip
    # update the markers belonging to each clip
    # return the second asset_clip if exists, otherwise the first asset_clip

    # take asset_clip as the object
    old_asset_clip = asset_clip

    if debug:
        start = arithmetic.fcpsec2frac(old_asset_clip.get('start')) if old_asset_clip.get('start') else Fraction(0, 1)
        duration = arithmetic.fcpsec2frac(old_asset_clip.get('duration'))
        end = start + duration
        print("cell_divion START")
        print(f"orignal asset_clip | start: {start}, end: {end}, duration: {duration}")
        start = arithmetic.fcpsec2frac(silence['start'])
        end = arithmetic.fcpsec2frac(silence['end'])
        duration = end - start
        print(f"silence | start: {start}, end: {end}, duration: {duration}")

    # add a duplicate of the asset_clip
    index = list(spine).index(old_asset_clip)
    new_asset_clip = copy.deepcopy(old_asset_clip)
    spine.insert(index + 1, new_asset_clip)

    # update the end of the first (old) asset_clip
    start = arithmetic.fcpsec2frac(old_asset_clip.get("start")) if old_asset_clip.get('start') else Fraction(0, 1)
    end = arithmetic.fcpsec2frac(silence['start'])
    duration = end - start

    if debug:
        print(f"fps: {fps}")
        # original asset_clip
        start = arithmetic.fcpsec2frac(old_asset_clip.get('start')) if old_asset_clip.get('start') else Fraction(0, 1)
        duration = arithmetic.fcpsec2frac(old_asset_clip.get('duration'))
        end = start + duration
        print(f"original asset_clip | start: {start}, end: {end}, duration: {duration}")
        # new old_asset_clip
        end = arithmetic.fcpsec2frac(silence['start'])
        duration = end - start
        print(f"old_asset_clip | start: {start}, end: {end}, duration: {duration}")
    old_asset_clip.set('duration', f"{arithmetic.frac2fcpsec(duration, fps)}")
    if debug:
        print(f"old_asset_clip's new duration: {arithmetic.frac2fcpsec(duration, fps)}, fps: {fps}")

    # update the start of the second (new) asset_clip
    new_asset_clip.set('start', silence['end'])
    old_offset = arithmetic.fcpsec2frac(old_asset_clip.get('offset'))
    old_duration = arithmetic.fcpsec2frac(old_asset_clip.get('duration'))
    new_offset = old_offset + old_duration
    new_asset_clip.set('offset', f"{arithmetic.frac2fcpsec(new_offset, fps)}")
    if debug:
        print(f"new_asset_clip's new offset: {arithmetic.frac2fcpsec(new_offset, fps)}, fps: {fps}")

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
        print("new second asset_clip's duration = original_asset_clip duration - old_asset_clip_duration - silence_duration")
        #print(f"new_asset_clip duration before: {new_asset_clip.get('duration')}, after: {new_duration}s, silence_duration {silence_duration}s, old_duration: {old_duration}s")
        print(f"original_asset_clip_duration: {new_asset_clip.get('duration')}, old_duration: {old_duration}s, silence_duration {silence_duration}s, new second asset_clip duration: {new_duration}s")
    new_asset_clip.set('duration', f"{arithmetic.frac2fcpsec(new_duration, fps)}")
    if debug:
        print(f"new_asset_clip's new duration: {arithmetic.frac2fcpsec(new_duration, fps)}, fps: {fps}")
        # checksum
        print(f"new_asset_clip start as silence['end']: {new_asset_clip.get('start')} == {silence['end']}")
        print(f"new_asset_clip duration: {new_asset_clip.get('duration')}")

    # update the markers belonging to each clip
    trim.trim_markers(clip=old_asset_clip, fps=fps, debug=debug)
    trim.trim_markers(clip=new_asset_clip, fps=fps, debug=debug)

    if debug:
        print("asset_clip cell_division done")

def remove_zero_durations(spine, debug=False):
    clips = spine.findall('asset-clip')
    for c in clips:
        duration = arithmetic.fcpsec2frac(c.get('duration'))
        if duration <= 0:
            spine.remove(c)

def chop_asset_clip(asset_clip, spine, silence, fps='100/6000s', debug=False):
    """
    asset_clip: XML ET asset-clip element
    silence: {'start': 'xxx.yys', 'end': 'aaa.bbs'}
    fps: fps of the project clip (not necesarily the source clip)
    Note that silence is in the local source media (asset-clip) time, not in the global spine time.

    Returns the remaining asset_clip to further work on cell_division in the parent loop.

    FCPXML language:
    start of asset-clip: local start time of the asset-clip to be played in the global timeline, not the start position of the clip in the global spine timeline.
    offset of asset-clip: the start position of the clip in the global spine timeline.
    duration: determines the length of the clip to be placed in the global spine timeline.

    IMPORTANT:
    the start and end time of silence should be understood as the intrinsic timeline of the asset-clip, not the project timeline. the project timeline will constantly change each time cell-division is done, but all silences were measured before this cell-division-driven timeline messed up.
    """
    # take asset_clip as the object
    # add a duplicate of the asset_clip
    # update the end of the first asset_clip
    # update the start of the second asset_clip
    # update the markers belonging to each clip
    # return the second asset_clip (it should always exist even if the duration is zero)

    # take asset_clip as the object
    old_asset_clip = asset_clip

    if debug:
        pass

    # add a duplicate of the asset_clip
    # there's something going on with the last element
    # like the new duration is never updated
    index = list(spine).index(old_asset_clip)
    new_asset_clip = copy.deepcopy(old_asset_clip)
    spine.insert(index + 1, new_asset_clip)

    # update the end of the first (old) asset_clip
    start = arithmetic.fcpsec2frac(old_asset_clip.get("start")) if old_asset_clip.get('start') else Fraction(0, 1)
    end = arithmetic.fcpsec2frac(silence['start'])
    duration = end - start

    if debug:
        print(f"fps: {fps}")
        # original asset_clip
        start = arithmetic.fcpsec2frac(old_asset_clip.get('start')) if old_asset_clip.get('start') else Fraction(0, 1)
        duration = arithmetic.fcpsec2frac(old_asset_clip.get('duration'))
        end = start + duration
        print(f"original asset_clip | start: {start}, end: {end}, duration: {duration}")
        # new old_asset_clip
        end = arithmetic.fcpsec2frac(silence['start'])
        duration = end - start
        print(f"old_asset_clip | start: {start}, end: {end}, duration: {duration}")
    old_asset_clip.set('duration', f"{arithmetic.frac2fcpsec(duration, fps)}")
    if debug:
        print(f"old_asset_clip's new duration: {arithmetic.frac2fcpsec(duration, fps)}, fps: {fps}")

    # update the start of the second (new) asset_clip
    original_start_timestamp = new_asset_clip.get('start')
    if not original_start_timestamp:
        num, denom = arithmetic.unfrac(fps)
        original_start_timestamp = f'0/{denom}s'
    new_asset_clip.set('start', silence['end'])

    # now adjust the duration of the new (second) asset_clip
    original_duration = new_asset_clip.get('duration')
    new_start_timestamp = new_asset_clip.get('start')
    difference = arithmetic.fcpsec_subtract(new_start_timestamp, original_start_timestamp, fps=fps)
    new_duration = arithmetic.fcpsec_subtract(original_duration, difference, fps=fps)
    new_asset_clip.set('duration', new_duration)
    if debug:
        print(f"original_duration: {original_duration}")
        print(f"new_start_timestamp: {new_start_timestamp}")
        print(f"original_start_timestamp: {original_start_timestamp}")
        print(f"difference: {difference}")
        print(f"new_asset_clip's new duration: {new_duration}, fps: {fps}")
        # checksum
        print(f"new_asset_clip start as silence['end']: {new_asset_clip.get('start')} == {silence['end']}")
        print(f"new_asset_clip duration: {new_asset_clip.get('duration')}")

    # update the markers belonging to each clip
    trim.trim_markers(clip=old_asset_clip, fps=fps, debug=debug)
    trim.trim_markers(clip=new_asset_clip, fps=fps, debug=debug)

    if debug:
        print("asset_clip chop_asset_clip done")

    return new_asset_clip

def blade_silence(asset_clip, root, silences, fps='100/6000s', debug=False):
    """
    silences: [{'start': 'xxxx/yyys', 'end': 'aaaa/bbs'}, ...]

    The main purpose of this wrapper function is to loop over silences.
    """
    sequence = fcpxml_io.get_sequence(root)
    if debug:
        print(f"blade_silence sequence: {sequence}, {sequence.tag}")
    spine = fcpxml_io.get_spine(root)
    if debug:
        print(f"blade_silence spine: {spine}, {spine.tag}")

    # Cut-out silent regions from asset_clip
    for s in tqdm(silences):
        # for each silence,
        # pick up the asset_clip to split,
        # divide_cell it (does all the magic like dividing markers as well)
        if asset_clip:
            asset_clip = chop_asset_clip(asset_clip=asset_clip, spine=spine, silence=s, fps=fps, debug=debug)

def collapse_gaps(root, fps='100/6000s', debug=False):
    sequence = fcpxml_io.get_sequence(root)
    spine = fcpxml_io.get_spine(root)

    num, denom = arithmetic.unfrac(fps) 

    #new_spine_duration = f'0/{denom}s'
    new_clip_offset = f'0/{denom}s'
    for asset_clip in spine:
        asset_clip.set('offset', new_clip_offset)
        new_clip_offset = arithmetic.fcpsec_add(new_clip_offset, asset_clip.get('duration'), fps)
    sequence.set('duration', new_clip_offset)

    # Remove asset-clips with duration=0.0s (should only be possible for the first and the last one)
    remove_zero_durations(spine=spine, debug=debug)
