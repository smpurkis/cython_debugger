#!/usr/bin/env python

"""
Run with `python -m example`
"""
import os
import subprocess
import sys
from distutils.spawn import find_executable

from pygdbmi.gdbcontroller import GdbController


def main(verbose=True):

    gdbmi = GdbController()

    gdbmi.exit()


if __name__ == "__main__":
    main()
