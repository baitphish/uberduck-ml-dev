__all__ = ["parse_args"]


import argparse
from collections import namedtuple
from dataclasses import dataclass
import json
import os
from pathlib import Path
from shutil import copyfile, copytree
import sys
from typing import List, Optional, Set

import sqlite3
from tqdm import tqdm

from ..data.cache import (
    CACHE_LOCATION,
    ensure_speaker_table,
)  # ensure_filelist_in_cache,
from ..data.parse import _generate_filelist
from ..utils.audio import convert_to_wav

# from uberduck_ml_dev.utils.utils import parse_vctk


def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="path to JSON config", required=True)
    parser.add_argument(
        "-d", "--database", help="Input database", default=CACHE_LOCATION
    )
    parser.add_argument("-o", "--out", help="path to save output", required=True)
    return parser.parse_args(args)


try:
    from nbdev.imports import IN_NOTEBOOK
except:
    IN_NOTEBOOK = False

if __name__ == "__main__" and not IN_NOTEBOOK:
    args = parse_args(sys.argv[1:])
    if args.config:
        conn = sqlite3.connect(args.database)
        _generate_filelist(args.config, conn, args.out)
    else:
        raise Exception("You must pass a config file!")
