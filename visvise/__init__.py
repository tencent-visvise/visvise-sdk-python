"""
VISVISE Weaver Python SDK

Usage::

    from visvise import VisviseClient

    client = VisviseClient(app_id="...", secret_key="...")
    model_id = client.gen_360("character.png", algorithm_model="hunyuan3D-MultiView-v3.0")
    model = client.wait_model(model_id)
    print(model.output_model)
"""

from .client import FileInput, VisviseClient
from .http import Environment
from .exceptions import (
    ModelGenerationError,
    NetworkError,
    PermissionDeniedError,
    PollingTimeoutError,
    QuotaExceededError,
    RateLimitError,
    SignatureError,
    WeaverError,
)
from .models import (
    DetailLevel,
    FaceType,
    FramingAIOutput,
    GetCosCredResult,
    ImageGen360Output,
    MeshRefineMode,
    ModelInfo,
    ModelStatus,
    NodeType,
    OutputModelFormat,
    ReduceFace,
    Text2Motion,
    UserQuota,
    View,
)

__version__ = "0.1.0"
__all__ = [
    "VisviseClient",
    "FileInput",
    "Environment",
    # exceptions
    "WeaverError",
    "NetworkError",
    "SignatureError",
    "PermissionDeniedError",
    "QuotaExceededError",
    "RateLimitError",
    "ModelGenerationError",
    "PollingTimeoutError",
    # models & enums
    "ModelInfo",
    "ModelStatus",
    "NodeType",
    "FaceType",
    "DetailLevel",
    "OutputModelFormat",
    "MeshRefineMode",
    "View",
    "ReduceFace",
    "UserQuota",
    "GetCosCredResult",
    "ImageGen360Output",
    "FramingAIOutput",
    "Text2Motion",
]
