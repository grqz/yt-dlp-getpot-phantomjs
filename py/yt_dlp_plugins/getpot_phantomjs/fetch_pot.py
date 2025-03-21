import functools
import json
import typing
from yt_dlp import YoutubeDL
from yt_dlp.utils.traversal import traverse_obj
from yt_dlp.extractor.common import InfoExtractor

from .script import SCRIPT, SCRIPT_PHANOTOM_MINVER
from .phantom_jsi import PhantomJSWrapperWithCustomArgs


def construct_jsi(ie, *args, **kwargs):
    return PhantomJSWrapperWithCustomArgs(
        ie, required_version=SCRIPT_PHANOTOM_MINVER)


def fetch_pots(ie, content_bindings, extra_args=None, phantom_jsi=None, *args, **kwargs):
    # TODO: proxy
    if not phantom_jsi:
        phantom_jsi = construct_jsi(
            ie, content_bindings, extra_args=extra_args, phantom_jsi=phantom_jsi, *args, **kwargs)
    execute = functools.partial(
        phantom_jsi.execute,
        phantom_args=[
            # '--ssl-protocol=any'
            # '--ignore-ssl-errors=true',
            '--web-security=false',
            # '--proxy=https://127.0.0.1:8080',
            *(extra_args or [])
        ],
        script_args=content_bindings)
    return traverse_obj(
        SCRIPT, ({execute}, {lambda x: ie.write_debug(f'phantomjs stdout: {x}') or x},
                 {str.splitlines}, -1, {str.strip}, {json.loads}))


@typing.overload
def fetch_pot(ie, content_binding, extra_args=None, phantom_jsi=None): ...


def fetch_pot(ie, content_binding, *args, **kwargs):
    return traverse_obj(fetch_pots(ie, [content_binding], *args, **kwargs), 0)


def main():
    ydl = YoutubeDL({'verbose': True})
    ie = InfoExtractor(ydl)
    print(fetch_pot(ie, 'dQw4w9WgXcQ'))
