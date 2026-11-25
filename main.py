#!/usr/bin/env python3
"""Entrypoint for the make.fun news-image-20261125 bounty."""

import os
import shutil


def main() -> None:
    source_dir = os.path.dirname(os.path.abspath(__file__))
    source_path = os.path.join(source_dir, "entry.png")
    output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(output_dir, exist_ok=True)
    dest_path = os.path.join(output_dir, "entry.png")
    shutil.copyfile(source_path, dest_path)


if __name__ == "__main__":
    main()
