"""
VISVISE Weaver SDK - 原子 API 方法

每个方法对应文档中一个具体接口，失败时根据错误码抛出对应异常。
"""

from __future__ import annotations

import logging
from typing import Optional

from .http import WeaverHTTPClient
from .models import (
    GetCosCredResult,
    ImageGen360Output,
    ModelInfo,
    UserQuota,
    View,
)

logger = logging.getLogger("visvise.api")


class VisviseAPI:
    """VISVISE Weaver 全部原子接口。

    通常不直接使用此类，而是通过 :class:`~visvise.client.VisviseClient` 访问。
    """

    def __init__(self, http: WeaverHTTPClient):
        self._http = http

    # ──────────────────────────────────────────────────────────────────────
    # 2.2  获取文件上传临时凭证
    # ──────────────────────────────────────────────────────────────────────

    def get_cos_cred(self, is_temp: bool = False) -> GetCosCredResult:
        """获取 COS 临时密钥，用于客户端直传文件。

        Args:
            is_temp: 是否临时文件（7天后自动删除）。无特殊情况请保持 False。

        Returns:
            :class:`~visvise.models.GetCosCredResult`

        Raises:
            WeaverError / 子类: 接口错误
        """
        # is_temp=False 时不传该字段，避免签名不一致
        body = {"is_temp": True} if is_temp else {}
        data = self._http.post(
            "openapi/weaver/resource/get_cos_cred",
            body,
        )
        return GetCosCredResult.from_dict(data)

    # ──────────────────────────────────────────────────────────────────────
    # 2.3  获取用户剩余生成次数
    # ──────────────────────────────────────────────────────────────────────

    def get_user_quota(self) -> UserQuota:
        """获取当前 API Key 当日剩余生成次数。

        Returns:
            :class:`~visvise.models.UserQuota`

        Raises:
            WeaverError / 子类: 接口错误
        """
        data = self._http.post("openapi/weaver/resource/get_user_quota", {})
        return UserQuota.from_dict(data)

    # ──────────────────────────────────────────────────────────────────────
    # 2.4  生成 3D 模型资产
    # ──────────────────────────────────────────────────────────────────────

    def gen_3d_model(
        self,
        name: str,
        node_type: int,
        params: dict,
        *,
        input_view: Optional[View] = None,
        input_model: Optional[str] = None,
        input_model_format: Optional[str] = None,
        input_video: Optional[str] = None,
    ) -> list[str]:
        """创建 3D 生成任务（异步）。

        Args:
            name: 模型资产名称。
            node_type: 节点类型，参考 :class:`~visvise.models.NodeType`。
            params: TemplateParams 字典，根据 node_type 填写对应子结构。
            input_view: 原画视图（图生360/图生模/贴图节点必传）。
            input_model: 模型 COS 地址（zip 文件）。
            input_model_format: 模型格式 fbx/obj/glb。
            input_video: 视频 COS 地址（视频生动画必传）。

        Returns:
            新生成的模型 ID 列表。

        Raises:
            WeaverError / 子类: 接口错误
        """
        body: dict = {
            "name": name,
            "node_type": node_type,
            "params": params,
        }
        if input_view is not None:
            body["input_view"] = input_view.to_dict()
        if input_model is not None:
            body["input_model"] = input_model
        if input_model_format is not None:
            body["input_model_format"] = input_model_format
        if input_video is not None:
            body["input_video"] = input_video

        data = self._http.post("openapi/weaver/resource/gen_3d_model", body)
        return data["model_ids"]

    # ──────────────────────────────────────────────────────────────────────
    # 2.5  生成多视图
    # ──────────────────────────────────────────────────────────────────────

    def gen_multi_views(
        self,
        name: str,
        input_view: View,
        params: dict,
    ) -> str:
        """从单张图生成多视图（异步）。

        Args:
            name: 任务名称。
            input_view: 输入视图，至少包含 main_view。
            params: TemplateParams，需填写 image_gen_360_params。

        Returns:
            新生成的模型 ID。

        Raises:
            WeaverError / 子类: 接口错误
        """
        body = {
            "name": name,
            "input_view": input_view.to_dict(),
            "params": params,
        }
        data = self._http.post("openapi/weaver/resource/gen_multi_views", body)
        return data["model_id"]

    # ──────────────────────────────────────────────────────────────────────
    # 2.6  拉取模型资产列表
    # ──────────────────────────────────────────────────────────────────────

    def get_model_list(
        self,
        *,
        model_id_list: Optional[list[str]] = None,
        node_type_list: Optional[list[int]] = None,
        status_list: Optional[list[int]] = None,
        keyword: Optional[str] = None,
        limit: int = 20,
        page: int = 1,
        sorter: Optional[dict] = None,
    ) -> tuple[list[ModelInfo], int]:
        """拉取模型资产列表。

        Returns:
            (model_list, total_count)

        Raises:
            WeaverError / 子类: 接口错误
        """
        body: dict = {"limit": limit, "page": page}
        if model_id_list:
            body["model_id_list"] = model_id_list
        if node_type_list:
            body["node_type_list"] = node_type_list
        if status_list:
            body["status_list"] = status_list
        if keyword:
            body["keyword"] = keyword
        if sorter:
            body["sorter"] = sorter

        data = self._http.post("openapi/weaver/resource/get_model_list", body)
        models = [ModelInfo.from_dict(m) for m in data.get("model_list", [])]
        return models, data.get("total_count", 0)

    # ──────────────────────────────────────────────────────────────────────
    # 2.7  拉取算法模型列表
    # ──────────────────────────────────────────────────────────────────────

    def list_algorithm_model(
        self,
        node_type: int,
        sub_type: Optional[int] = None,
    ) -> list[str]:
        """获取指定节点类型支持的算法模型列表。

        Args:
            node_type: 节点类型。
            sub_type: 子类型（仅 node_type=4 时使用）：1 视频生动画，2 文生动画。

        Returns:
            算法模型名称列表。

        Raises:
            WeaverError / 子类: 接口错误
        """
        body: dict = {"node_type": node_type}
        if sub_type is not None:
            body["type"] = sub_type
        data = self._http.post("openapi/weaver/resource/list_algorithm_model", body)
        return data.get("model_list", [])

    # ──────────────────────────────────────────────────────────────────────
    # 2.8  下载模型资产
    # ──────────────────────────────────────────────────────────────────────

    def download_model(self, model_id: str) -> str:
        """生成模型资产的带签名下载 URL。

        Args:
            model_id: 模型 ID。

        Returns:
            带签名的下载 URL（24h 有效）。

        Raises:
            WeaverError / 子类: 接口错误
        """
        data = self._http.post(
            "openapi/weaver/resource/download_model",
            {"model_id": model_id},
        )
        # data 字段直接是 URL 字符串
        return data  # type: ignore[return-value]

    # ──────────────────────────────────────────────────────────────────────
    # 2.9  删除模型资产
    # ──────────────────────────────────────────────────────────────────────

    def delete_model(self, model_id: str) -> None:
        """删除单个模型资产。

        Raises:
            WeaverError / 子类: 接口错误
        """
        self._http.post(
            "openapi/weaver/resource/delete_model",
            {"model_id": model_id},
        )

    # ──────────────────────────────────────────────────────────────────────
    # 2.10 批量删除模型
    # ──────────────────────────────────────────────────────────────────────

    def batch_delete_model(self, model_ids: list[str]) -> None:
        """批量删除模型资产。

        Args:
            model_ids: 待删除的模型 ID 列表。

        Raises:
            WeaverError / 子类: 接口错误
        """
        self._http.post(
            "openapi/weaver/resource/batch_delete_model",
            {"model_ids": model_ids},
        )

    # ──────────────────────────────────────────────────────────────────────
    # 2.11 去除图片背景
    # ──────────────────────────────────────────────────────────────────────

    def remove_bg(self, image_url: str) -> str:
        """去除图片背景，返回透明背景图片 URL。

        Args:
            image_url: 输入图片地址。

        Returns:
            输出图片地址。

        Raises:
            WeaverError / 子类: 接口错误
        """
        data = self._http.post(
            "openapi/weaver/resource/remove_background",
            {"image_url": image_url},
        )
        return data["image_url"]

    # ──────────────────────────────────────────────────────────────────────
    # 2.12 批量图生 Pose
    # ──────────────────────────────────────────────────────────────────────

    def batch_gen_pose(
        self,
        name: str,
        input_model: str,
        input_images: list[str],
        params: dict,
    ) -> list[str]:
        """批量图生 Pose（异步）。

        Args:
            name: 任务基础名称。
            input_model: FBX 模型 COS 地址（zip）。
            input_images: 参考图片 URL 列表（1~10 张）。
            params: ImageGenPoseParams 字典，需包含 algorithm_model 和 output_model_format。

        Returns:
            新生成的模型 ID 列表。

        Raises:
            WeaverError / 子类: 接口错误
        """
        body = {
            "name": name,
            "input_model": input_model,
            "input_images": input_images,
            "params": params,
        }
        data = self._http.post("openapi/weaver/resource/batch_gen_pose", body)
        return data["model_ids"]

    # ──────────────────────────────────────────────────────────────────────
    # 2.13 获取文生动画提示词 Demo 列表
    # ──────────────────────────────────────────────────────────────────────

    def get_text2motion_prompt_list(self, language: str = "zh") -> list[str]:
        """获取文生动画提示词 Demo 列表。

        Args:
            language: 语言类型，"zh" 中文 / "en" 英文。

        Returns:
            提示词列表。

        Raises:
            WeaverError / 子类: 接口错误
        """
        data = self._http.post(
            "openapi/weaver/demo/get_text2motion_prompt_list",
            {"language": language},
        )
        return data.get("prompt_list", [])

    # ──────────────────────────────────────────────────────────────────────
    # 2.14 初始化分割（SSE）
    # ──────────────────────────────────────────────────────────────────────

    def init_segment(
        self,
        name: str,
        algorithm_model: str,
        *,
        model_id: Optional[str] = None,
        input_view: Optional[View] = None,
        split_type: Optional[int] = None,
        granularity: Optional[int] = None,
        prompt: Optional[str] = None,
    ):
        """初始化 2D 分割（SSE 流式接口）。

        ``model_id`` 与 ``input_view`` 二选一。返回 generator，每次 yield 一个事件帧
        ``{"event": str, "data": Any}``，事件类型包括 ``pre_create`` / ``thinking``
        / ``reply`` / ``error``。

        Args:
            name: 资产名称（最长 100 字符）。
            algorithm_model: 算法模型名称。
            model_id: 图生 360 的 model_id。
            input_view: 输入视图。
            split_type: 拆分方式，1 正视图（默认）/ 2 四视图。
            granularity: 颗粒度，1 粗 / 2 中（默认）/ 3 细。
            prompt: 拆分提示词（最长 200 字符）。

        Yields:
            事件帧字典 ``{"event": str, "data": Any}``。

        Raises:
            ValueError: ``model_id`` 与 ``input_view`` 都未传时抛出。
            NetworkError: SSE 网络层异常。
        """
        if not model_id and not input_view:
            raise ValueError("init_segment 需要传入 model_id 或 input_view 其中一个")

        body: dict = {"name": name, "algorithm_model": algorithm_model}
        if model_id:
            body["model_id"] = model_id
        if input_view is not None:
            body["input_view"] = input_view.to_dict()
        if split_type is not None:
            body["split_type"] = split_type
        if granularity is not None:
            body["granularity"] = granularity
        if prompt is not None:
            body["prompt"] = prompt

        return self._http.post_sse("openapi/weaver/component/init_segment", body)
