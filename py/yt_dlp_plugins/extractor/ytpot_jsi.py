from __future__ import annotations

__version__ = '0.1.0'

from yt_dlp.networking.common import Request
from yt_dlp.extractor.youtube.pot.provider import (
    PoTokenContext,
    PoTokenProvider,
    PoTokenProviderError,
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
    # PhantomJS wrapper instance
    _JSI_INSTANCE = None

    def is_available(self):
        if self._JSI_INSTANCE is False:
            return False
        elif self._JSI_INSTANCE is None:
            try:
                self._JSI_INSTANCE = construct_jsi(self.ie)
            except Exception as e:
                # Don't try to construct it next time
                self._JSI_INSTANCE = False
                self.logger.warning(f'Failed to construct phantomjs interpreter: {e}')
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
                            phantom_jsi=self._JSI_INSTANCE, pot_logger=self.logger)
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
