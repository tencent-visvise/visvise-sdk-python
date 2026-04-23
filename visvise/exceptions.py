"""
VISVISE Weaver SDK - 异常类定义

所有 SDK 异常均继承自 WeaverError。
"""


class WeaverError(Exception):
    """SDK 基础异常"""

    def __init__(self, message: str, code: int = -1, req_id: str = ""):
        super().__init__(message)
        self.code = code
        self.req_id = req_id
        self.message = message

    def __str__(self) -> str:
        parts = [f"[{self.code}] {self.message}"]
        if self.req_id:
            parts.append(f"(req_id={self.req_id})")
        return " ".join(parts)


# ──────────────────────────────────────────────
# HTTP / 网络层异常
# ──────────────────────────────────────────────

class NetworkError(WeaverError):
    """网络请求失败（连接超时、DNS 解析失败等）"""


class SignatureError(WeaverError):
    """签名错误（HTTP 400）"""


# ──────────────────────────────────────────────
# 平台通用错误码
# ──────────────────────────────────────────────

class InvalidParamsError(WeaverError):
    """请求参数错误 (120008)"""


class UserNotFoundError(WeaverError):
    """用户未找到 (120017)"""


class PermissionDeniedError(WeaverError):
    """用户无权限 (120018)"""


class QuotaExceededError(WeaverError):
    """每日生成次数超出上限 (120020)"""


class ProjectPermissionError(WeaverError):
    """项目权限未授权 (120027)"""


class ServerNetworkError(WeaverError):
    """服务器网络错误 (120028)"""


class ServerTimeoutError(WeaverError):
    """服务器处理超时 (120032)"""


class RateLimitError(WeaverError):
    """请求过于频繁 (120040)"""


# ──────────────────────────────────────────────
# 模型生成失败异常（异步任务 status=4）
# ──────────────────────────────────────────────

class ModelGenerationError(WeaverError):
    """模型生成失败（异步任务 status=4）"""

    def __init__(self, message: str, code: int = -1, model_id: str = "", req_id: str = ""):
        super().__init__(message, code=code, req_id=req_id)
        self.model_id = model_id

    def __str__(self) -> str:
        parts = [f"[{self.code}] {self.message}"]
        if self.model_id:
            parts.append(f"(model_id={self.model_id})")
        return " ".join(parts)


# ──────────────────────────────────────────────
# 轮询超时异常
# ──────────────────────────────────────────────

class PollingTimeoutError(WeaverError):
    """等待模型完成超时"""

    def __init__(self, model_id: str, timeout: int):
        super().__init__(
            f"等待模型 {model_id} 完成超时（{timeout}s）",
            code=-2,
        )
        self.model_id = model_id
        self.timeout = timeout


# ──────────────────────────────────────────────
# 错误码 → 异常 映射表
# ──────────────────────────────────────────────

_CODE_TO_EXCEPTION: dict[int, type[WeaverError]] = {
    400:    SignatureError,
    120008: InvalidParamsError,
    120017: UserNotFoundError,
    120018: PermissionDeniedError,
    120020: QuotaExceededError,
    120027: ProjectPermissionError,
    120028: ServerNetworkError,
    120032: ServerTimeoutError,
    120040: RateLimitError,
}


def raise_for_code(code: int, msg: str, req_id: str = "") -> None:
    """根据错误码抛出对应异常；未知错误码抛出通用 WeaverError。"""
    exc_cls = _CODE_TO_EXCEPTION.get(code, WeaverError)
    raise exc_cls(msg, code=code, req_id=req_id)
