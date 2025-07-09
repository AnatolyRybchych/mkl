#!/usr/bin/env python3

import shutil
import shlex
import subprocess
import json
import sys
import os
import re

from mklang.syntax import Syntax
from mklang.layout import Layout
import xml.etree.ElementTree as ET

layout_file_path = 'layout.xml'
layout_file_path = os.path.abspath(layout_file_path)
with open(layout_file_path) as layout_file:
    layout_xml = ET.parse(layout_file)

layout_dict = Syntax.parse_xml(layout_xml.getroot())
print(json.dumps(layout_dict, indent=2))


layout_syntax = Syntax(os.path.dirname(layout_file_path), **layout_dict)
layout = Layout(layout_syntax)

files: dict[str, str] = layout.generate()

for path, data in list(files.items()):
    new_path = path
    if re.match(r'.*\.h$', path):
        new_path = f'{layout.settings['output_header_dir.*']}/{path}'
    elif re.match(r'.*\.c$', path):
        new_path = f'{layout.settings['output_source_dir.*']}/{path}'

    del files[path]
    files[new_path] = data

for path, data in files.items():
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'w') as file:
        file.write(data)

if shutil.which('clang-format'):
    style={
        'BasedOnStyle': 'Google',
        'IndentWidth': 4,
    }

    for path in files.keys():
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
