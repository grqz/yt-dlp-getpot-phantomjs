import json
import typing
from yt_dlp.utils.traversal import traverse_obj

from .script import SCRIPT, SCRIPT_PHANOTOM_MINVER
from .phantom_jsi import PhantomJSWrapperWithCustomArgs
from .server import POTHTTPServer


def construct_jsi(ie, *args, **kwargs):
    return PhantomJSWrapperWithCustomArgs(
        ie, required_version=SCRIPT_PHANOTOM_MINVER, *args, **kwargs)


def fetch_pots(ie, content_bindings, Request, urlopen, phantom_jsi=None, *args, **kwargs):
    if phantom_jsi is None:
        phantom_jsi = construct_jsi(
            ie, content_bindings, *args, **kwargs)
    with POTHTTPServer(Request, urlopen) as pot_server:
        script = r'var embeddedInputData = {data};'.format(data=json.dumps({
            'port': pot_server.port,
            'content_bindings': content_bindings,
        })) + SCRIPT
        return traverse_obj(
            script, ({phantom_jsi.execute}, {lambda x: ie.write_debug(f'phantomjs stdout: {x}') or x},
                     {str.splitlines}, -1, {str.strip}, {json.loads}))


@typing.overload
def fetch_pot(ie, content_binding, Request, urlopen, extra_args=None, phantom_jsi=None): ...


def fetch_pot(ie, content_binding, *args, **kwargs):
    return traverse_obj(fetch_pots(ie, [content_binding], *args, **kwargs), 0)
