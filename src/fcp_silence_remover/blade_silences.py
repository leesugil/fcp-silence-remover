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
    new_asset_clip = copy.deepcopy(old_asset_clip)
    spine.append(new_asset_clip)

    # update the end of the first (old) asset_clip
    start = arithmetic.fcpsec2frac(old_asset_clip.get("start")) if old_asset_clip.get('start') else Fraction(0, 1)
    end = arithmetic.fcpsec2frac(silence['start'])
    duration = end - start

    # proof
    #assert duration > 0, f"start: {start} from {old_asset_clip.get('start')}, end: {end} from {silence['start']}"

    if debug:
        print(f"fps: {fps}")
        #print(f"old_asset_clip fps: {fps}, start: {old_asset_clip.get('start')}, start_frac: {start}, end: {silence['start']}, end_frac: {end}, duration: {duration}")
        # original asset_clip
        start = arithmetic.fcpsec2frac(old_asset_clip.get('start')) if old_asset_clip.get('start') else Fraction(0, 1)
        duration = arithmetic.fcpsec2frac(old_asset_clip.get('duration'))
        end = start + duration
        print(f"original asset_clip | start: {start}, end: {end}, duration: {duration}")
        # new old_asset_clip
        end = arithmetic.fcpsec2frac(silence['start'])
        duration = end - start
        print(f"old_asset_clip | start: {start}, end: {end}, duration: {duration}")
        #print(f"old_asset_clip fps: {fps}, start: {old_asset_clip.get('start')}, start_frac: {start}, end: {silence['start']}, end_frac: {end}, duration: {duration}")
        #print(f"old_asset_clip duration before: {old_asset_clip.get('duration')}, after: {duration}s")
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
        cell_division(spine=spine, silence=s, fps=fps, debug=debug)

        # wait, instead of the current workflow,
        # whay don't i also Blade silences in the protected region
        # without cutting out?
        # because i do manually and potentially cut out some parts inside protected regions,
        # and such action still causes minor performance issue,
        # so wouldn't it be better to pre-cut at silence Markers and trim out Markers
        # so that i wouldn't have any repetition?
        #
        # let's say, instead of main() picking 'silences' only,
        # let's pick 'silences' and 'protected', and process differently.
        # for example, unlike playing Bannerlord, if I play other games like KCD2 or W4K Space Marine 2,
        # i'll have different preferences on how much to protect from removal and how much to skip screen events and keep the pace to me talking in the video.
        # it's like a spectrum
        #    |-------------------------------------|
        # Contents                              Contents
        # that the audio relies                 that the audio is
        # on me keep talking                    rich in in-game voice-over features
        # like Bannerlord                       like KCD2
        # 
        # my design choice will keep evolve around, but for now,
        # i'm thinking of these two examples because
        # KCD2 will be my next game, and i'm wondering if
        # marking 'protection' will be better or
        # marking 'remove silence' will be better.
        # (if there are frequent, short in-game voice-over dialogues, ...)
    
    new_spine_duration = 0.0
    for c in spine:
        new_spine_duration += arithmetic.fcpsec2float(c.get('duration'))
    sequence.set('duration', f"{new_spine_duration}s")

    # Remove asset-clips with duration=0.0s (should only be possible for the first and the last one)
    remove_zero_durations(spine, debug)
