
def get_markers(clip, key='keyword'):
    """
    <marker start="129/10s" duration="1500/90000s" value="Silence start 1"/>
    <marker start="189/10s" duration="1500/90000s" value="Silence end 1"/>
    silences: [{'start': 'xxxx/yyys', 'end': 'aaaa/bbs'}, {...}, ...]
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
    """
    output = []
    for i in range(0, len(markers), 2):
        start = markers[i].get('start')
        end = markers[i+1].get('start')
        output.append({'start': start, 'end': end})
    return output

def get_silences(clip, key='Silence'):
    """
    <marker start="129/10s" duration="1500/90000s" value="Silence start 1"/>
    <marker start="189/10s" duration="1500/90000s" value="Silence end 1"/>

    output: [{'start': 'xxxx/yyys', 'end': 'aaaa/bbs'}, ...]
    """
    return merge_pair_markers(get_markers(clip, key))

def get_protected(clip, key='Protection'):
    """
    <marker start="129/10s" duration="1500/90000s" value="Protection start"/>
    <marker start="229/10s" duration="1500/90000s" value="Protection end"/>

    output: [{'start': 'xxxx/yyys', 'end': 'aaaa/bbs'}, ...]
    """
    return merge_pair_markers(get_markers(clip, key))
