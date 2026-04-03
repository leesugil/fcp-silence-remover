#!/usr/bin/env python3

import argparse
import xml.etree.ElementTree as ET
from tqdm import tqdm

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
    # cut_silence
    parser.add_argument("--cut-silence", action='store_true', help="(experimental) cut silences out by protected intervals.")
    # debug
    parser.add_argument("--debug", action='store_true', help="(experimental) display debug messages.")

    args = parser.parse_args()

    xf = fcpxml_io.clean_filepath(args.fcpxml_filepath)
    print(f"fcpxml file: {xf}")

    # <fcpxml>
    tree, root = fcpxml_io.get_fcpxml(xf)
    asset_clips = fcpxml_io.get_all_spine_asset_clips(root=root)
    # '100/6000s'
    fps = fcpxml_io.get_fps(root)
    if args.debug:
        print(f"fps: {fps}")

    for asset_clip in tqdm(asset_clips):
        silences = parse_markers.get_silences(clip=asset_clip, key=args.skey)
        protected = parse_markers.get_protected(clip=asset_clip, key=args.pkey)

        silences = blade_silences.get_unprotected_silences(silences=silences, protected=protected, cut_silence=args.cut_silence)
        blade_silences.blade_silence(asset_clip=asset_clip, root=root, silences=silences, fps=fps, debug=args.debug)

    blade_silences.collapse_gaps(root=root, fps=fps, debug=args.debug)

    fcpxml_io.save_with_affix(tree=tree, src_filepath=xf, affix=args.affix)

if __name__ == "__main__":
    main()
