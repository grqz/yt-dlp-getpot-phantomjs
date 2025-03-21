# old code used to fetch and descramble challenge
import json
from urllib.request import Request, urlopen
from yt_dlp.utils.traversal import traverse_obj, value

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36(KHTML, like Gecko)'
GOOG_API_KEY = 'AIzaSyDyT5W0Jh49F30Pqqtyfdf7pDLFKLJoAnw'
REQUEST_KEY = 'O43z0dpjhgX20SCx4KAo'
YT_BASE_URL = 'https://www.youtube.com'
GOOG_BASE_URL = 'https://jnn-pa.googleapis.com'


def get_headers():
    return {
        'Content-Type': 'application/json+protobuf',
        'X-Goog-Api-Key': GOOG_API_KEY,
        'X-User-Agent': 'grpc-web-javascript/0.1',
        'User-Agent': USER_AGENT
    }


def build_url(endpoint_name, use_yt=False):
    base = YT_BASE_URL if use_yt else GOOG_BASE_URL
    path_mid = 'api/jnn/v1' if use_yt else '$rpc/google.internal.waa.v1.Waa'
    return f'{base}/{path_mid}/{endpoint_name}'


def bytes_to_b64(bytes_, url):
    import base64
    if url:
        return base64.urlsafe_b64encode(bytes_).decode('ascii').rstrip('=')
    else:
        return base64.b64encode(bytes_).decode('ascii')


def decode_b64(b64):
    import base64
    base64_str = b64.replace('-', '+').replace('_', '/').replace('.', '=')

    padding = len(base64_str) % 4
    if padding:
        base64_str += '=' * (4 - padding)

    return base64.b64decode(b64)


def descramble_challenge(scrambled_challenge):
    buffer = decode_b64(scrambled_challenge)
    return bytes((b + 97) % 256 for b in buffer).decode() if buffer else ''


def parse_challenge(raw_challenge):
    challenge_data = []
    if len(raw_challenge) > 1 and isinstance(raw_challenge[1], str):
        descrambled = descramble_challenge(raw_challenge[1])
        challenge_data = json.loads(descrambled or '[]')
    elif len(raw_challenge) and isinstance(raw_challenge[0], dict):
        challenge_data = raw_challenge[0]
    wrapped_script = traverse_obj(challenge_data, 1)
    safe_script = (
        next((value for value in wrapped_script if value and isinstance(value, str)), None)
    ) if isinstance(wrapped_script, list) else None
    wrapped_url = traverse_obj(challenge_data, 2)
    trusted_rsrc_url = (
        next((value for value in wrapped_url if value and isinstance(value, str)), None)
    ) if isinstance(wrapped_url, list) else None
    return traverse_obj(challenge_data, {
        'messageId': 0,
        'interpreterJavascript': {value({
            'privateDoNotAccessOrElseSafeScriptWrappedValue': safe_script,
            'privateDoNotAccessOrElseTrustedResourceUrlWrappedValue': trusted_rsrc_url,
        })},
        'interpreterHash': 3,
        'program': 4,
        'globalName': 5,
        'clientExperimentsStateBlob': 7,
    })


def fetch_challenge():
    payload = [REQUEST_KEY]
    req = Request(
        build_url('Create', False),
        data=json.dumps(payload).encode(),
        headers=get_headers())
    raw_data = None
    with urlopen(req) as resp:
        raw_data = json.loads(resp.read())
    return parse_challenge(raw_data)
