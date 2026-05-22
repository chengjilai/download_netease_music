"""Minimal NCM API wrapper — 3 methods only."""

import ctypes, json

from core import (
    _Engine, _NcmProcessEnv, load_ncm, _NcmContextManager, engine,
)
from common import to_bytes, Response

_Engine()


class NCM:
    def __init__(self):
        self._ncm = load_ncm()
        self._env = _NcmProcessEnv()
        self._cookie = {}

    def _request(self, path, **params):
        path = to_bytes(path)
        query = to_bytes(json.dumps({k: v for k, v in params.items() if v is not None}))
        cookie = to_bytes(json.dumps(self._cookie))
        ctx = _NcmContextManager.init(self._env)
        ptr = self._ncm.ncm_request(ctx, path, cookie, query, ctypes.byref(self._env))
        if ptr:
            result = ctypes.cast(ptr, ctypes.c_char_p).value
            engine.response_free(ptr)
            return Response(result.decode("utf-8"))
        return Response('{"status":500,"body":{}}')

    def set_cookie(self, d):
        self._cookie.update(d)

    def login_cellphone(self, phone, captcha):
        return self._request("/login/cellphone",
                             phone=phone, captcha=captcha)

    def song_url_v1(self, id, level="standard"):
        return self._request("/song/url/v1", id=id, level=level)
