#!/usr/bin/env python3
import pathlib

JS_PATH = r'pot_http.es5.cjs'
PY_DEST_PATH = r'getpot_phantomjs/script.py'
PHANOTOM_MINVER = '1.9.0'

TEMPLATE = r'''# {js_path}
SCRIPT = {script_quoted}
SCRIPT_PHANOTOM_MINVER = {minver}
'''


def main():
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    with open(repo_root / 'js/src' / JS_PATH) as js_file:
        with open(repo_root / 'py/yt_dlp_plugins' / PY_DEST_PATH, 'w') as py_file:
            py_file.write(TEMPLATE.format(
                script_quoted=repr(js_file.read()), minver=repr(PHANOTOM_MINVER),
                js_path=JS_PATH))


if __name__ == '__main__':
    main()
