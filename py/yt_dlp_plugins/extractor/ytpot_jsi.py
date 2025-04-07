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
from ..getpot_phantomjs.fetch_pot import construct_jsi, fetch_pot

__version__ = '0.1.0'


@register_provider
class PhantomJSWebPTP(PoTokenProvider):
    PROVIDER_NAME = 'phantomjs-web'
    PROVIDER_VERSION = __version__
    BUG_REPORT_LOCATION = 'https://github.com/grqz/yt-dlp-getpot-jsi/issues'
    _SUPPORTED_CLIENTS = WEBPO_CLIENTS
    _SUPPORTED_PROXY_SCHEMES = None
    _SUPPORTED_CONTEXTS = (PoTokenContext.GVS, PoTokenContext.PLAYER)
    # PhantomJS unavailable in the current environment
    _PJS_UNAVAILABLE = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._jsi = None

    def is_available(self):
        if self._PJS_UNAVAILABLE:
            return False
        elif self._jsi is None:
            try:
                self._jsi = construct_jsi(self.ie)
            except Exception as e:
                # Don't try to construct it next time
                self._PJS_UNAVAILABLE = True
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
                            phantom_jsi=self._jsi, log=self.logger.trace)
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
