from __future__ import annotations

__version__ = '0.1.0'

import typing

if typing.TYPE_CHECKING:
    from yt_dlp import YoutubeDL
from yt_dlp.networking.common import Request, Features
from yt_dlp.networking.exceptions import UnsupportedRequest, RequestError
from yt_dlp.utils import classproperty, remove_end

try:
    import yt_dlp_plugins.extractor.getpot as getpot
except ImportError as e:
    e.msg += '\nyt-dlp-get-pot is missing! See https://github.com/coletdjnz/yt-dlp-get-pot?tab=readme-ov-file#installing.'
    raise e

from yt_dlp_plugins.getpot_phantomjs.fetch_pot import construct_jsi, fetch_pot


@getpot.register_provider
class PhantomJSGetPOTRH(getpot.GetPOTProvider):
    _SUPPORTED_CLIENTS = ('web', 'web_safari', 'web_embedded',
                          'web_music', 'web_creator', 'mweb', 'tv_embedded', 'tv')
    VERSION = __version__
    # TODO: cache
    _SUPPORTED_PROXY_SCHEMES = (
        'http', 'https', 'socks4', 'socks4a', 'socks5', 'socks5h')
    _SUPPORTED_FEATURES = (Features.ALL_PROXY, Features.NO_PROXY)
    _SUPPORTED_CONTEXTS = ('gvs', 'player')

    @classproperty
    def RH_NAME(cls):
        return cls._PROVIDER_NAME or remove_end(cls.RH_KEY, 'GetPOT')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._jsi = None
        self._yt_ie = None

    def _warn_and_raise(self, msg, once=True, raise_from=None):
        self._logger.warning(msg, once=once)
        raise UnsupportedRequest(msg) from raise_from

    @staticmethod
    def _get_content_binding(client, context, data_sync_id=None, visitor_data=None, video_id=None):
        # https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide#po-tokens-for-player
        if context == 'gvs' or client == 'web_music':
            # web_music player or gvs is bound to data_sync_id or visitor_data
            return data_sync_id or visitor_data
        return video_id

    def _validate_get_pot(
        self,
        client: str,
        ydl: YoutubeDL,
        visitor_data=None,
        data_sync_id=None,
        context=None,
        video_id=None,
        **kwargs,
    ):
        if not self._yt_ie:
            self._yt_ie = ydl.get_info_extractor('Youtube')
        if not self._jsi:
            try:
                self._jsi = construct_jsi(self._yt_ie)
            except Exception as e:
                raise UnsupportedRequest(e) from e

    def _get_pot(
        self,
        client: str,
        ydl: YoutubeDL,
        visitor_data=None,
        data_sync_id=None,
        session_index=None,
        player_url=None,
        context=None,
        video_id=None,
        ytcfg=None,
        **kwargs,
    ) -> str:
        try:
            content_binding = self._get_content_binding(client, context, data_sync_id, visitor_data, video_id)
            self._logger.debug(f'Generating POT for content binding: {content_binding}')
            pot = fetch_pot(self._yt_ie, content_binding, Request, ydl.urlopen, phantom_jsi=self._jsi)
            self._logger.debug(f'Generated POT: {pot}')
            return pot
        except Exception as e:
            raise RequestError(e) from e


@getpot.register_preference(PhantomJSGetPOTRH)
def phantomjs_getpot_preference(rh, req):
    return 210
