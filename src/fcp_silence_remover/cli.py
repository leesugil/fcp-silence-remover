#!/usr/bin/env python3

import argparse
import xml.etree.ElementTree as ET

from . import blade_silences
from . import parse_markers
from fcp_io import fcpxml_io

def main():
    # Define possible arguments
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
    parser.add_argument("--debug", action='store_true', help="(experimental) display debug messages.")

    args = parser.parse_args()

    xf = fcpxml_io.clean_filepath(args.fcpxml_filepath)
    vf = fcpxml_io.clean_filepath(fcpxml_io.parse_fcpxml_filepath(xf))
    print(f"fcpxml file: {xf}")
    print(f"video file: {vf}")

    # <fcpxml>
    tree, root = fcpxml_io.get_fcpxml(xf)
    spine = fcpxml_io.get_spine(root)
    asset_clip = spine.find('asset-clip')
    # '100/6000s'
    fps = fcpxml_io.get_fps(root)
    if args.debug:
        print(f"fps: {fps}")

    silences = parse_markers.get_silences(clip=asset_clip, key=args.skey)
    protected = parse_markers.get_protected(clip=asset_clip, key=args.pkey)

    silences = blade_silences.get_unprotected_silences(silences, protected)
    blade_silences.blade_silence(root=root, silences=silences, fps=fps, debug=args.debug)

    fcpxml_io.save_with_affix(tree=tree, src_filepath=xf, affix=args.affix)

if __name__ == "__main__":
    main()
