from __future__ import annotations

__version__ = '0.0.1'

import typing

if typing.TYPE_CHECKING:
    from yt_dlp import YoutubeDL
# NOTE: this is internal only and may be moved in the future
from yt_dlp.networking._helper import select_proxy
from yt_dlp.networking import Request
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
    # TODO: proxy
    _SUPPORTED_PROXY_SCHEMES = ()
    _SUPPORTED_FEATURES = ()
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

    def _get_yt_proxy(self):
        if ((proxy := select_proxy('https://jnn-pa.googleapis.com', self.proxies))
                != select_proxy('https://youtube.com', self.proxies)):
            self._logger.warning(
                'Proxies for https://youtube.com and https://jnn-pa.googleapis.com are different. '
                'This is likely to cause subsequent errors.')
        return proxy

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
    return 201
