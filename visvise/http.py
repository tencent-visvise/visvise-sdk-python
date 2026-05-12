"""
VISVISE Weaver SDK - HTTP 客户端（签名、请求、错误处理）
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from enum import Enum
from typing import Any

import requests
from requests import Response

from .exceptions import NetworkError, raise_for_code

logger = logging.getLogger("visvise.http")


class Environment(str, Enum):
    """预置环境枚举，对应不同的 API 域名。

    传给 :class:`VisviseClient` 的 ``env`` 参数，也可直接传自定义 URL 字符串。

    Examples::

        from visvise import VisviseClient, Environment

        # 使用测试环境
        client = VisviseClient("app_id", "key", env=Environment.TEST)

        # 使用自定义域名
        client = VisviseClient("app_id", "key", env="https://my-proxy.example.com")
    """

    PROD = "https://ws.visvise.com.cn"         # 线上生产环境（默认）
    TEST = "https://qa-ws.visvise.com.cn"    # 测试环境
    DEV  = "https://dev-ws.visvise.com.cn"     # 开发环境


# 向后兼容：直接引用默认域名
BASE_URL: str = Environment.PROD.value


class WeaverHTTPClient:
    """底层 HTTP 客户端，封装签名计算和统一错误处理。"""

    def __init__(
        self,
        app_id: str,
        secret_key: str,
        uid: str,
        base_url: str | Environment = Environment.PROD,
        timeout: int = 30,
    ):
        # 兼容 Environment 枚举和自定义字符串
        self.app_id = app_id
        self.secret_key = secret_key
        self.uid = uid
        self.base_url = (base_url.value if isinstance(base_url, Environment) else base_url).rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()
        logger.debug("WeaverHTTPClient initialized: base_url=%s", self.base_url)

    # ──────────────────────────────────────────
    # 签名
    # ──────────────────────────────────────────

    def _sign(self, body_str: str, ts: str) -> str:
        """POST 签名：body_json_str + timestamp"""
        sign_str = body_str + ts
        return hmac.new(
            self.secret_key.encode("utf-8"),
            sign_str.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _headers_with_body_str(self, body_str: str) -> dict:
        ts = str(int(time.time()))
        sign = self._sign(body_str, ts)
        headers = {
            "Content-Type": "application/json",
            "app_id": self.app_id,
            "uid": self.uid,
            "ts": ts,
            "sign": sign,
        }
        return headers

    # ──────────────────────────────────────────
    # 请求
    # ──────────────────────────────────────────

    def post(self, path: str, body: dict | None = None) -> Any:
        """发送 POST 请求，自动签名，统一处理错误码。

        Returns:
            响应 data 字段（已解包），如无 data 则返回 None。

        Raises:
            NetworkError: 网络层异常
            WeaverError / 子类: 业务错误码异常
        """
        if body is None:
            body = {}
        url = f"{self.base_url}/{path.lstrip('/')}"

        # 序列化一次，签名和发送共用同一份字符串，确保一致
        body_str = json.dumps(body, ensure_ascii=False, separators=(",", ":"))
        headers = self._headers_with_body_str(body_str)

        logger.debug("POST %s body=%s", url, body_str[:200])

        try:
            resp: Response = self._session.post(
                url,
                headers=headers,
                data=body_str.encode("utf-8"),  # 直接发序列化好的字符串
                timeout=self.timeout,
            )
            resp.raise_for_status()
        except requests.exceptions.ConnectionError as e:
            raise NetworkError(f"连接失败: {e}") from e
        except requests.exceptions.Timeout as e:
            raise NetworkError(f"请求超时: {e}") from e
        except requests.exceptions.HTTPError as e:
            # 透出服务端响应体，便于定位（如 {"error":"invalid app_id"} 之类的非标准错误）
            body_excerpt = (resp.text or "").strip()
            if len(body_excerpt) > 500:
                body_excerpt = body_excerpt[:500] + "...(truncated)"
            extra = f" body={body_excerpt!r}" if body_excerpt else ""
            raise NetworkError(f"HTTP 错误 [{resp.status_code}]: {e}{extra}") from e
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"请求异常: {e}") from e

        try:
            result = resp.json()
        except ValueError as e:
            raise NetworkError(
                f"响应解析失败 [{resp.status_code}]: body={(resp.text or '')[:500]!r}"
            ) from e

        code = result.get("code", -1)
        req_id = result.get("req_id", "")
        msg = result.get("msg", "unknown error")

        logger.debug("Response code=%s req_id=%s", code, req_id)

        if code != 0:
            raise_for_code(code, msg, req_id)

        return result.get("data")

    # ──────────────────────────────────────────
    # SSE 请求（用于 init_segment 等流式接口）
    # ──────────────────────────────────────────

    def post_sse(self, path: str, body: dict | None = None, *, read_timeout: int | None = 1200):
        """发送 POST 请求并以 SSE 流方式返回事件帧。

        每帧 yield 一个 dict：``{"event": str, "data": Any}``，``data`` 在可解析为 JSON
        时返回 dict/list，否则返回原始字符串。

        Args:
            path: 接口路径。
            body: 请求体。
            read_timeout: SSE 读超时（秒），默认 1200s（20 分钟）。SSE 流式接口可能持续较久
                （如 2D 拆分需要逐个部件分割），单独设置较长超时；连接超时仍使用 client 的 timeout。

        Raises:
            NetworkError: 网络异常 / 非 SSE 响应
        """
        if body is None:
            body = {}
        url = f"{self.base_url}/{path.lstrip('/')}"

        body_str = json.dumps(body, ensure_ascii=False, separators=(",", ":"))
        headers = self._headers_with_body_str(body_str)
        headers["Accept"] = "text/event-stream"

        logger.debug("POST(SSE) %s body=%s", url, body_str[:200])

        try:
            resp = self._session.post(
                url,
                headers=headers,
                data=body_str.encode("utf-8"),
                # 元组形式：(连接超时, 读超时)。SSE 流较长，读超时单独放大
                timeout=(self.timeout, read_timeout) if read_timeout else self.timeout,
                stream=True,
            )
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            # 透出服务端响应体，便于定位（如 {"error":"invalid app_id"} 等非标准错误）
            try:
                body_excerpt = (resp.text or "").strip()
            except Exception:
                body_excerpt = ""
            if len(body_excerpt) > 500:
                body_excerpt = body_excerpt[:500] + "...(truncated)"
            extra = f" body={body_excerpt!r}" if body_excerpt else ""
            raise NetworkError(f"SSE HTTP 错误 [{resp.status_code}]: {e}{extra}") from e
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"SSE 请求异常: {e}") from e

        # 强制使用 UTF-8 解码，避免服务端响应头 charset 缺失或错误时出现乱码
        resp.encoding = "utf-8"

        event = None
        data_lines: list[str] = []
        for raw_line in resp.iter_lines(decode_unicode=True):
            if raw_line is None:
                continue
            if raw_line == "":
                # 空行表示一帧结束
                if event is not None or data_lines:
                    data_str = "\n".join(data_lines)
                    try:
                        data_val: Any = json.loads(data_str) if data_str else None
                    except ValueError:
                        data_val = data_str
                    yield {"event": event or "message", "data": data_val}
                event = None
                data_lines = []
                continue
            if raw_line.startswith(":"):
                continue  # 注释
            if raw_line.startswith("event:"):
                event = raw_line[len("event:"):].strip()
            elif raw_line.startswith("data:"):
                data_lines.append(raw_line[len("data:"):].lstrip())

        # 收尾：可能最后一帧没有结尾空行
        if event is not None or data_lines:
            data_str = "\n".join(data_lines)
            try:
                data_val = json.loads(data_str) if data_str else None
            except ValueError:
                data_val = data_str
            yield {"event": event or "message", "data": data_val}
