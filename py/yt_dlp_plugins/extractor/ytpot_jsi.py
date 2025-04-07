from __future__ import annotations

__version__ = '0.1.0'

from yt_dlp.networking.common import Request
from yt_dlp.extractor.youtube.pot.provider import (
    PoTokenContext,
    PoTokenProvider,
    PoTokenProviderError,
    PoTokenProviderRejectedRequest,
    PoTokenRequest,
    PoTokenResponse,
    register_preference,
    register_provider,
)
from yt_dlp.extractor.youtube.pot.builtin.utils import WEBPO_CLIENTS, get_webpo_content_binding
from yt_dlp_plugins.getpot_phantomjs.fetch_pot import construct_jsi, fetch_pot


@register_provider
class PhantomJSWebPTP(PoTokenProvider):
    _SUPPORTED_CLIENTS = WEBPO_CLIENTS
    PROVIDER_VERSION = __version__
    PROVIDER_NAME = 'phantomjs-web'
    _SUPPORTED_PROXY_SCHEMES = (
        'http', 'https', 'socks4', 'socks4a', 'socks5', 'socks5h')
    _SUPPORTED_CONTEXTS = (PoTokenContext.GVS, PoTokenContext.PLAYER)
    BUG_REPORT_LOCATION = 'https://github.com/grqz/yt-dlp-getpot-jsi/issues'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._jsi = None

    def _warn_and_raise(self, msg, once=True, raise_from=None):
        self.logger.warning(msg, once=once)
        raise PoTokenProviderRejectedRequest(msg) from raise_from

    @staticmethod
    def _get_content_binding(client, context, data_sync_id=None, visitor_data=None, video_id=None):
        # https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide#po-tokens-for-player
        if context == 'gvs' or client == 'web_music':
            # web_music player or gvs is bound to data_sync_id or visitor_data
            return data_sync_id or visitor_data
        return video_id

    def is_available(self):
        if not self._jsi:
            try:
                self._jsi = construct_jsi(self.ie)
                return True
            except Exception as e:
                self._warn_and_raise(f'Failed to construct phantomjs interpreter: {e}', raise_from=e)
                return False
        return True

    def _real_request_pot(
        self,
        ctx: PoTokenRequest,
    ) -> PoTokenResponse:
        try:
            content_binding = get_webpo_content_binding(ctx)[0]
            self.logger.trace(f'Generating WebPO for content binding: {content_binding}')
            # The PhantomJS wrapper will log to info for us
            pot = fetch_pot(self.ie, content_binding, Request=Request,
                            urlopen=lambda req: self._urlopen(pot_request=ctx, http_request=req),
                            phantom_jsi=self._jsi, stdout_logger=self.logger)
            self.logger.trace(f'Generated POT: {pot}')
            if not pot:
                raise ValueError('Unexpected empty POT')
            return PoTokenResponse(po_token=pot)
        except Exception as e:
            raise PoTokenProviderError(e) from e


@register_preference(PhantomJSWebPTP)
def phantomjs_getpot_preference(provider: PoTokenProvider, request: PoTokenRequest, *_, **__) -> int:
    return 120


__all__ = [
    PhantomJSWebPTP.__name__,
    phantomjs_getpot_preference.__name__,
]
