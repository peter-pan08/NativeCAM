#!/usr/bin/env python3
# coding: utf-8
#
# Copyright (c) 2012 Nick Drobchenko aka Nick from cnc-club.ru
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

################## USAGE #################
#
# make sure this file is executable
# args are :
#    -r, to replace all icons
##########################################

import argparse
import subprocess
import shutil
from pathlib import Path

from lxml import etree

SVG_NS = "http://www.w3.org/2000/svg"
DEFAULT_ICON_SIZE = 80


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate icon PNGs from icons.svg")
    parser.add_argument("-r", "--renew", action="store_true", help="replace all icons")
    parser.add_argument(
        "--size",
        type=int,
        default=DEFAULT_ICON_SIZE,
        help="maximum size for icon (default: 80)",
    )
    parser.add_argument(
        "--svg",
        type=Path,
        default=Path("icons.svg"),
        help="path to icons.svg",
    )
    return parser.parse_args()


def run_cmd(cmd: list[str]) -> str:
    result = subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Command failed: %s" % " ".join(cmd))
    return result.stdout.strip()


def query_dimension(svg_path: Path, element_id: str, dimension: str) -> float:
    cmd = [
        "inkscape",
        str(svg_path),
        f"--query-id={element_id}",
        f"--query-{dimension}",
    ]
    return float(run_cmd(cmd))


def export_icon(svg_path: Path, element_id: str, width: float, height: float, output_path: Path) -> None:
    cmd = [
        "inkscape",
        str(svg_path),
        f"--export-id={element_id}",
        "--export-id-only",
        "--export-area-snap",
        f"--export-width={width}px",
        f"--export-height={height}px",
        f"--export-filename={output_path}",
    ]
    run_cmd(cmd)


def main() -> int:
    args = parse_args()

    if shutil.which("inkscape") is None:
        raise SystemExit("inkscape is required to render icons.svg")

    svg_path = args.svg
    if not svg_path.is_file():
        raise SystemExit("icons.svg not found: %s" % svg_path)

    output_dir = svg_path.parent.parent
    xml = etree.parse(str(svg_path))

    for title in xml.findall(f".//{{{SVG_NS}}}title"):
        icon_name = (title.text or "").strip()
        parent = title.getparent()
        element_id = parent.get("id") if parent is not None else None
        if not icon_name or not element_id:
            continue

        output_path = output_dir / f"{icon_name}.png"
        if output_path.exists() and not args.renew:
            print("Skipping %s" % icon_name)
            print()
            continue

        try:
            width = query_dimension(svg_path, element_id, "width")
            height = query_dimension(svg_path, element_id, "height")
            if width > height:
                width, height = args.size, args.size * height / width
            else:
                height, width = args.size, args.size * width / height
            export_icon(svg_path, element_id, width, height, output_path)
            print("Created %s" % icon_name)
        except Exception as exc:
            print()
            print("Error with the file %s.png!" % icon_name)
            print(exc)
            print()
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
