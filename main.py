#!/usr/bin/env python3
"""Entrypoint: copy the finished entry.png into the output directory.

The image itself is drawn ahead of time by draw.py (Pillow, dev only) and
shipped in this repository as entry.png. At grading time the program runs
with no network and only the standard library, so all it does is copy
that file to $MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png).
A plain file copy is deterministic: both grading runs write identical
bytes.
"""

import os
import shutil


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "entry.png")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, "entry.png")
    shutil.copyfile(src, dst)
    print("wrote", dst, os.path.getsize(dst), "bytes")


if __name__ == "__main__":
    main()
