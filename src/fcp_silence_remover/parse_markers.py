from fcp_math import arithmetic

def get_markers(clip, key='keyword'):
    """
    <marker start="129/10s" duration="1500/90000s" value="Silence start 1"/>
    <marker start="189/10s" duration="1500/90000s" value="Silence end 1"/>
    silences: [{'start': 'xxxx/yyys', 'end': 'aaaa/bbs'}, {...}, ...]
    Note that the timestamps are local to the source media, not necessarilly matching to the global timeline in the Project Spine.
    """
    markers = [e for e in clip if e.tag == 'marker' and (key in e.get('value'))]
    return markers

def merge_pair_markers(markers):
    """
    markers: [
        <marker start="129/10s" duration="1500/90000s" value="Silence start 1"/>,
        <marker start="189/10s" duration="1500/90000s" value="Silence end 1"/>,
        ...]

    output: [{'start': 'xxxx/yyys', 'end': 'aaaa/bbs'}, ...]

    Note that the timestamps are local to the source media, not necessarilly matching to the global timeline in the Project Spine.
    """
    output = []
    for i in range(0, len(markers), 2):
        start = markers[i].get('start')
        end = markers[i+1].get('start')
        marked_duration = arithmetic.fcpsec2frac(end) - arithmetic.fcpsec2frac(start)
        assert marked_duration > 0
        output.append({'start': start, 'end': end})
    return output

def get_silences(clip, key='Silence'):
    """
    <marker start="129/10s" duration="1500/90000s" value="Silence start 1"/>
    <marker start="189/10s" duration="1500/90000s" value="Silence end 1"/>

    output: [{'start': 'xxxx/yyys', 'end': 'aaaa/bbs'}, ...]

    Note that the timestamps are local to the source media, not necessarilly matching to the global timeline in the Project Spine.
    """
    return merge_pair_markers(get_markers(clip, key))

def get_protected(clip, key='Protection'):
    """
    <marker start="129/10s" duration="1500/90000s" value="Protection start"/>
    <marker start="229/10s" duration="1500/90000s" value="Protection end"/>

    output: [{'start': 'xxxx/yyys', 'end': 'aaaa/bbs'}, ...]

    Note that the timestamps are local to the source media, not necessarilly matching to the global timeline in the Project Spine.
    """
    return merge_pair_markers(get_markers(clip, key))
