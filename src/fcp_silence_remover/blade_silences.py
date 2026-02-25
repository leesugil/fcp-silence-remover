import xml.etree.ElementTree as ET
from tqdm import tqdm
import copy

from . import fcpxml_io
from . import parse_markers
from . import fcp_math
import intervalop

def get_unprotected_silences(silences: list[dict], protected: list[dict]) -> list[dict]:
    """
    silences: [{'start': 'xxxx/yyys', 'end': 'aaaa/bbs'}, ...]
    protected: [{'start': 'xxxx/yyys', 'end': 'aaaa/bbs'}, ...]

    output: [{'start': 'xxxx/yyys', 'end': 'aaaa/bbs'}, ...]
    """
    if not protected:
        return silences

    silences_list = fcp_math.dict2list(silences)
    protected_list = fcp_math.dict2list(protected)
    output_list = intervalop.excluding(silences_list, protected_list)
    output = fcp_math.list2dict(output_list)

    return output

def trim_markers(clip, fps='100/6000s'):
    """
    clip: fcpxml clip or asset-clip as an ET element.
    fps: fps of the Project clip (not necessarily the source clip)

    remove all markers, chapter-markers, and keywords placed outside the start and end (start+duration) range.
    helps optimization fcpxml files when there are tons of clip blading on marker-heavy clips

    keep all geq 'start' and less than 'end'
    """
    start = clip.get('start')
    if not start:
        num, denom = fcp_math.unfrac(fps) 
        start = f'0/{denom}s'
    #print(f"trim_markers start: {start}, duration: {clip.get('duration')}")
    end = fcp_math.fcpsec_add(a=start, b=clip.get('duration'), fps=fps)
    markers = clip.findall('marker')
    markers += clip.findall('chapter-marker')
    markers += clip.findall('keyword')
    for m in markers:
        marker_start = m.get('start')
        if fcp_math.fcpsec_gt(start, marker_start) or fcp_math.fcpsec_geq(marker_start, end):
            # marker_start < start, or
            # end <= marker_start
            clip.remove(m)

def cell_division(root, silence, fps='100/6000s'):
    """
    root: an XML ET tree
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
    old_asset_clip = fcpxml_io.get_asset_clip(root)

    # add a duplicate of the asset_clip
    new_asset_clip = copy.deepcopy(old_asset_clip)
    root.append(new_asset_clip)

    # update the end of the first asset_clip
    start = old_asset_clip.get("start")
    if not start:
        num, denom = fcp_math.unfrac(fps) 
        start = f'0/{denom}s'
    end = silence['start']
    duration = fcp_math.fcpsec_subtract(end, start, fps)
    old_asset_clip.set('duration', duration)

    # update the start of the second asset_clip
    # first deduct the silence length from the current duration here
    new_asset_clip.set('start', silence['end'])
    old_offset = old_asset_clip.get('offset')
    old_duration = old_asset_clip.get('duration')
    offset = fcp_math.fcpsec_add(old_offset, old_duration, fps)
    # now deduct old_duration from the current duration here
    new_asset_clip.set('offset', offset)

    # first deduct the silence length from the current duration here
    # now deduct old_duration from the current duration here
    new_duration = new_asset_clip.get('duration')
    silence_duration = fcp_math.fcpsec_subtract(silence['end'], silence['start'], fps)
    reduced_duration = fcp_math.fcpsec_add(old_duration, silence_duration, fps)
    new_duration = fcp_math.fcpsec_subtract(new_duration, reduced_duration, fps)
    new_asset_clip.set('duration', new_duration)

    # update the markers belonging to each clip
    trim_markers(old_asset_clip, fps)
    trim_markers(new_asset_clip, fps)

def blade_silence(root, silences, fps='100/6000s'):
    """
    silences: [{'start': 'xxxx/yyys', 'end': 'aaaa/bbs'}, ...]
    protected: [{'start': 'xxxx/yyys', 'end': 'aaaa/bbs'}, ...]
    """
    spine = fcpxml_io.get_spine(root)

    sequence = root.find('.//sequence')
    original_timeline_duration = sequence.get('duration')

    # Divide the spine asset_clip into multiple asset_clips
    num, denom = fcp_math.unfrac(fps)
    total_duration_reduced = f"0/{denom}s"
    for s in tqdm(silences):
        # for each silence,
        # pick up the last spine asset_clip
        # divide_cell it (does all the magic like dividing markers as well)
        cell_division(root=spine, silence=s, fps=fps)

    new_spine_duration = '0/6000s'
    for c in spine:
        new_spine_duration = fcp_math.fcpsec_add(new_spine_duration, c.get('duration'))
    sequence.set('duration', new_spine_duration)
