#!/usr/bin/env python3

import os
import argparse
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, unquote

from . import blade_silences
from . import parse_markers
from . import fcpxml_io

def clean_filepath(line):
    output = os.path.abspath(line.strip())
    return output

def parse_fcpxml_filepath(xf):
    fcpxml_filename = 'Info.fcpxml'
    fcpxml_filepath = os.path.join(xf, fcpxml_filename)
    tree = ET.parse(fcpxml_filepath)
    root = tree.getroot()
    media_rep = root.find(".//media-rep[@kind='original-media']")
    output = media_rep.get('src')
    output = urlparse(output)
    output = unquote(output.path)
    return output

def main():

    # Define possible arguments
    # ex)
    # fcp-remove-silence --skey=Silence -pkey=Protection --affix='silence_removed_' <file_path>
    parser = argparse.ArgumentParser(description="Remove marked silent regions from FCP Project. Can set protected regions in the timeline to avoid the deletion.")
    parser.add_argument("fcpxml_filepath", help="Absolute filepath to fcpxml (required)")
    # Silence keyword
    parser.add_argument("--skey", type=str, default='Silence', help="A keyword to be used in recognizing Markers meant to mark silent regions in the Project Timeline")
    # Protected region keyword
    parser.add_argument("--pkey", type=str, default='Protection', help="A keyword to be used in recognizing Markers meant to mark protected regions from deleting silence in the Project Timeline")
    # output
    parser.add_argument("--affix", type=str, default='silence_removed_', help="affix to modify the output filename")
    # debug
    parser.add_argument("--debug", type=str, default=0, help="DEBUG output")

    args = parser.parse_args()

    xf = clean_filepath(args.fcpxml_filepath)
    vf = clean_filepath(parse_fcpxml_filepath(xf))
    print(f"fcpxml file: {xf}")
    print(f"video file: {vf}")

    DEBUG = True if (args.debug == 1) else False

    # parse silences
    # parse protected regions
    # prepare for regions to be removed from the Project Timeline
    # remove silent regions (cell-division.)
    #blade_silences.blade_silence(xf, args.skey, args.pkey, args.affix)

    # <fcpxml>
    tree, root = fcpxml_io.get_fcpxml(xf)
    spine = fcpxml_io.get_spine(root)
    asset_clip = spine.find('asset-clip')
    # 100/6000s
    fps = fcpxml_io.get_fps(root)

    silences = parse_markers.get_silences(clip=asset_clip, key=args.skey)
    protected = parse_markers.get_protected(clip=asset_clip, key=args.pkey)

    silences = blade_silences.get_unprotected_silences(silences, protected)
    blade_silences.blade_silence(root=root, silences=silences, fps=fps, debug=DEBUG)

    fcpxml_io.save(tree=tree, filepath=xf, affix=args.affix)

if __name__ == "__main__":
    main()
