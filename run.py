#!/usr/bin/env python3

import shutil
import shlex
import subprocess
import json
import sys
import os

from mklang.syntax import Syntax
from mklang.layout import Layout
import xml.etree.ElementTree as ET

with open('layout.xml') as layout_file:
    layout_xml = ET.parse(layout_file)

layout_dict = Syntax.parse_xml(layout_xml.getroot())
print(json.dumps(layout_dict, indent=2))


layout_syntax = Syntax(**layout_dict)
layout = Layout(layout_syntax)

layout.generate()

if shutil.which('clang-format'):
    style={
        'BasedOnStyle': 'Google',
        'IndentWidth': 4,
    }

    source_files = [src for obj in layout.code.object_files for src in obj.link_files]

    for path in source_files:
        cmd = [
            'clang-format',
            f'--style={json.dumps(style)}',
            '-i', path
        ]

        print(' '.join(shlex.quote(arg) for arg in cmd))
        if subprocess.call(cmd) != 0:
            print('Failed')
else:
    print(f'WARNING: could not find clang-format executable', file=sys.stderr)
