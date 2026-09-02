"""
VISVISE Weaver SDK - 原子 API 方法

每个方法对应文档中一个具体接口，失败时根据错误码抛出对应异常。

所有方法都需要传入 ``rtx`` 参数（实际使用人的 RTX 公司账号）。
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
    RemovePatternParam,
    StyleParam,
)

logger = logging.getLogger("visvise.api")


class VisviseAPI:
    """VISVISE Weaver 全部原子接口。

    通常不直接使用此类，而是通过 :class:`~visvise.client.VisviseClient` 访问。

    所有方法均需要传入 ``rtx`` 参数（实际使用人的 RTX 公司账号）。
    按照公司要求，**内部用户必须传实际使用人的 rtx**，不可代填。
    """

    def __init__(self, http: WeaverHTTPClient):
        self._http = http

    # ──────────────────────────────────────────────────────────────────────
    # 2.2  获取文件上传临时凭证
    # ──────────────────────────────────────────────────────────────────────

    def get_cos_cred(
        self, *, rtx: str, is_temp: bool = False, is_public: bool = False
    ) -> GetCosCredResult:
        """获取 COS 临时密钥，用于客户端直传文件。

        Args:
            rtx: 实际使用人的 RTX（公司账号）。**必填**。
            is_temp: 是否临时文件（7天后自动删除）。无特殊情况请保持 False。
            is_public: 是否上传到公有读目录。无特殊情况请保持 False。

        Returns:
            :class:`~visvise.models.GetCosCredResult`

        Raises:
            WeaverError / 子类: 接口错误
        """
        # is_temp/is_public=False 时不传该字段，避免签名不一致
        body: dict = {}
        if is_temp:
            body["is_temp"] = True
        if is_public:
            body["is_public"] = True
        data = self._http.post(
            "openapi/weaver/resource/get_cos_cred",
            body,
            rtx=rtx,
        )
        return GetCosCredResult.from_dict(data)

    # ──────────────────────────────────────────────────────────────────────
    # 2.3  获取用户剩余生成次数
    # ──────────────────────────────────────────────────────────────────────

    def get_user_quota(self, *, rtx: str) -> UserQuota:
        """获取当前 API Key 当日剩余生成次数。

        Args:
            rtx: 实际使用人的 RTX。**必填**。

        Returns:
            :class:`~visvise.models.UserQuota`

        Raises:
            WeaverError / 子类: 接口错误
        """
        data = self._http.post("openapi/weaver/resource/get_user_quota", {}, rtx=rtx)
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
        rtx: str,
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
            rtx: 实际使用人的 RTX。**必填**。
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

        data = self._http.post("openapi/weaver/resource/gen_3d_model", body, rtx=rtx)
        return data["model_ids"]

    # ──────────────────────────────────────────────────────────────────────
    # 2.5  生成多视图
    # ──────────────────────────────────────────────────────────────────────

    def gen_multi_views(
        self,
        name: str,
        input_view: View,
        params: dict,
        *,
        rtx: str,
    ) -> str:
        """从单张图生成多视图（异步）。

        Args:
            name: 任务名称。
            input_view: 输入视图，至少包含 main_view。
            params: TemplateParams，需填写 image_gen_360_params。
            rtx: 实际使用人的 RTX。**必填**。

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
        data = self._http.post("openapi/weaver/resource/gen_multi_views", body, rtx=rtx)
        return data["model_id"]

    # ──────────────────────────────────────────────────────────────────────
    # 2.6  拉取模型资产列表
    # ──────────────────────────────────────────────────────────────────────

    def get_model_list(
        self,
        *,
        rtx: str,
        model_id_list: Optional[list[str]] = None,
        node_type_list: Optional[list[int]] = None,
        status_list: Optional[list[int]] = None,
        keyword: Optional[str] = None,
        limit: int = 20,
        page: int = 1,
        sorter: Optional[dict] = None,
        model_type_list: Optional[list[int]] = None,
        last_ts: Optional[int] = None,
    ) -> tuple[list[ModelInfo], int]:
        """拉取模型资产列表。

        Args:
            rtx: 实际使用人的 RTX。**必填**。
            其它: 见参数说明。

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
        if model_type_list:
            body["model_type_list"] = model_type_list
        if last_ts is not None:
            body["last_ts"] = last_ts

        data = self._http.post("openapi/weaver/resource/get_model_list", body, rtx=rtx)
        models = [ModelInfo.from_dict(m) for m in data.get("model_list", [])]
        return models, data.get("total_count", 0)

    # ──────────────────────────────────────────────────────────────────────
    # 2.7  拉取算法模型列表
    # ──────────────────────────────────────────────────────────────────────

    def list_algorithm_model(
        self,
        node_type: int,
        sub_type: Optional[int] = None,
        *,
        rtx: str,
    ) -> list[str]:
        """获取指定节点类型支持的算法模型列表。

        Args:
            node_type: 节点类型。
            sub_type: 子类型（仅 node_type=4 时使用）：1 视频生动画，2 文生动画。
            rtx: 实际使用人的 RTX。**必填**。

        Returns:
            算法模型名称列表。

        Raises:
            WeaverError / 子类: 接口错误
        """
        body: dict = {"node_type": node_type}
        if sub_type is not None:
            body["type"] = sub_type
        data = self._http.post("openapi/weaver/resource/list_algorithm_model", body, rtx=rtx)
        return data.get("model_list", [])

    # ──────────────────────────────────────────────────────────────────────
    # 2.8  下载模型资产
    # ──────────────────────────────────────────────────────────────────────

    def download_model(self, model_id: str, *, rtx: str) -> str:
        """生成模型资产的带签名下载 URL。

        Args:
            model_id: 模型 ID。
            rtx: 实际使用人的 RTX。**必填**。

        Returns:
            带签名的下载 URL（24h 有效）。

        Raises:
            WeaverError / 子类: 接口错误
        """
        data = self._http.post(
            "openapi/weaver/resource/download_model",
            {"model_id": model_id},
            rtx=rtx,
        )
        # data 字段直接是 URL 字符串
        return data  # type: ignore[return-value]

    # ──────────────────────────────────────────────────────────────────────
    # 2.9  删除模型资产
    # ──────────────────────────────────────────────────────────────────────

    def delete_model(self, model_id: str, *, rtx: str) -> None:
        """删除单个模型资产。

        Args:
            model_id: 待删除的模型 ID。
            rtx: 实际使用人的 RTX。**必填**。

        Raises:
            WeaverError / 子类: 接口错误
        """
        self._http.post(
            "openapi/weaver/resource/delete_model",
            {"model_id": model_id},
            rtx=rtx,
        )

    # ──────────────────────────────────────────────────────────────────────
    # 2.10 批量删除模型
    # ──────────────────────────────────────────────────────────────────────

    def batch_delete_model(self, model_ids: list[str], *, rtx: str) -> None:
        """批量删除模型资产。

        Args:
            model_ids: 待删除的模型 ID 列表。
            rtx: 实际使用人的 RTX。**必填**。

        Raises:
            WeaverError / 子类: 接口错误
        """
        self._http.post(
            "openapi/weaver/resource/batch_delete_model",
            {"model_ids": model_ids},
            rtx=rtx,
        )

    # ──────────────────────────────────────────────────────────────────────
    # 2.10b 原地重生成模型资产
    # ──────────────────────────────────────────────────────────────────────

    def regenerate_model(
        self,
        model_id: str,
        *,
        rtx: str,
        params: Optional[dict] = None,
    ) -> None:
        """原地重生成模型资产。

        仅支持 2UV 节点（``node_type=15``，AUTO_LUV）资产；其它节点类型服务端会返回
        「模型类型不支持重新生成」错误。重生成不返回新的 model_id，原地覆盖，
        ``redo_count`` 递增。

        Args:
            model_id: 待重生成的模型 ID。
            rtx: 实际使用人的 RTX。**必填**。
            params: 可选，重新生成的参数（``TemplateParams`` 字典）。不传则复用该资产
                上次生成的参数。

        Raises:
            WeaverError / 子类: 接口错误
        """
        body: dict = {"model_id": model_id}
        if params is not None:
            body["params"] = params
        self._http.post("openapi/weaver/resource/regenerate_model", body, rtx=rtx)

    # ──────────────────────────────────────────────────────────────────────
    # 2.11 去除图片背景
    # ──────────────────────────────────────────────────────────────────────

    def remove_bg(self, image_url: str, *, rtx: str) -> str:
        """去除图片背景，返回透明背景图片 URL。

        Args:
            image_url: 输入图片地址。
            rtx: 实际使用人的 RTX。**必填**。

        Returns:
            输出图片地址。

        Raises:
            WeaverError / 子类: 接口错误
        """
        data = self._http.post(
            "openapi/weaver/resource/remove_background",
            {"image_url": image_url},
            rtx=rtx,
        )
        return data["image_url"]

    # ──────────────────────────────────────────────────────────────────────
    # 2D 预处理
    # ──────────────────────────────────────────────────────────────────────

    def style_transfer(self, input_view: str, style_type: int, *, rtx: str) -> str:
        """对原画进行风格化处理，返回处理结果图片 COS URL。

        Args:
            input_view: 输入原画的 VISVISE 平台 COS URL。
            style_type: 风格类型，使用 :class:`~visvise.models.StyleType` 常量。
            rtx: 实际使用人的 RTX。**必填**。

        Returns:
            处理结果图片的临时签名 COS 下载 URL（24h 有效）；用于保存资产时必须原样保留 query 参数。

        Raises:
            WeaverError / 子类: 接口错误。
        """
        data = self._http.post(
            "openapi/weaver/resource/style_transfer",
            {"input_view": input_view, "style_type": style_type},
            rtx=rtx,
        )
        return data["result_image"]

    def patter_auto_remove(self, input_view: str, *, rtx: str) -> str:
        """自动去除原画表面花纹，返回处理结果图片 COS URL。

        Args:
            input_view: 输入原画的 VISVISE 平台 COS URL。
            rtx: 实际使用人的 RTX。**必填**。

        Returns:
            处理结果图片的临时签名 COS 下载 URL（24h 有效）；用于保存资产时必须原样保留 query 参数。

        Raises:
            WeaverError / 子类: 接口错误
        """
        data = self._http.post(
            "openapi/weaver/resource/patter_auto_remove",
            {"input_view": input_view},
            rtx=rtx,
        )
        return data["result_image"]

    def gen_preprocess(
        self,
        name: str,
        input_view: str,
        preprocess_type: int,
        *,
        rtx: str,
        algorithm_model: Optional[str] = None,
        style_param: Optional[StyleParam] = None,
        remove_pattern_param: Optional[RemovePatternParam] = None,
    ) -> str:
        """将已处理图片保存为 2D 预处理模型资产。

        ``preprocess_type=PreprocessType.STYLIZED`` 时需传入 ``style_param``；
        ``preprocess_type=PreprocessType.PATTERNED`` 时需传入
        ``remove_pattern_param``。

        Args:
            name: 模型资产名称。
            input_view: 原始输入图片的 VISVISE 平台 COS URL。
            preprocess_type: 预处理类型，使用 :class:`~visvise.models.PreprocessType` 常量。
            rtx: 实际使用人的 RTX。**必填**。
            algorithm_model: 可选算法模型名称。
            style_param: 风格化结果参数；其 ``result_image`` 必须是 ``style_transfer``
                返回的完整临时签名 URL，不能移除或修改 query 参数。
            remove_pattern_param: 去花纹结果参数；其 ``result_image`` 必须是
                ``patter_auto_remove`` 返回的完整临时签名 URL，不能移除或修改 query 参数。

        Returns:
            已创建的 2D 预处理模型资产 ID。

        Raises:
            WeaverError / 子类: 接口错误
        """
        body: dict = {
            "name": name,
            "input_view": input_view,
            "preprocess_type": preprocess_type,
        }
        if algorithm_model is not None:
            body["algorithm_model"] = algorithm_model
        if style_param is not None:
            body["style_param"] = style_param.to_dict()
        if remove_pattern_param is not None:
            body["remove_pattern_param"] = remove_pattern_param.to_dict()

        data = self._http.post("openapi/weaver/resource/gen_preprocess", body, rtx=rtx)
        return data["model_id"]

    # ──────────────────────────────────────────────────────────────────────
    # 2.12 批量图生 Pose
    # ──────────────────────────────────────────────────────────────────────

    def batch_gen_pose(
        self,
        name: str,
        input_model: str,
        input_images: list[str],
        params: dict,
        *,
        rtx: str,
    ) -> list[str]:
        """批量图生 Pose（异步）。

        Args:
            name: 任务基础名称。
            input_model: FBX 模型 COS 地址（zip）。
            input_images: 参考图片 URL 列表（1~10 张）。
            params: ImageGenPoseParams 字典，需包含 algorithm_model 和 output_model_format。
            rtx: 实际使用人的 RTX。**必填**。

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
        data = self._http.post("openapi/weaver/resource/batch_gen_pose", body, rtx=rtx)
        return data["model_ids"]

    # ──────────────────────────────────────────────────────────────────────
    # 2.13 获取文生动画提示词 Demo 列表
    # ──────────────────────────────────────────────────────────────────────

    def get_text2motion_prompt_list(self, language: str = "zh", *, rtx: str) -> list[str]:
        """获取文生动画提示词 Demo 列表。

        Args:
            language: 语言类型，"zh" 中文 / "en" 英文。
            rtx: 实际使用人的 RTX。**必填**。

        Returns:
            提示词列表。

        Raises:
            WeaverError / 子类: 接口错误
        """
        data = self._http.post(
            "openapi/weaver/demo/get_text2motion_prompt_list",
            {"language": language},
            rtx=rtx,
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
        rtx: str,
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
            rtx: 实际使用人的 RTX。**必填**。
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
        return self._http.post_sse("openapi/weaver/component/init_segment", body, rtx=rtx)

    # ──────────────────────────────────────────────────────────────────────
    # 2.14 重新编辑（普通 JSON POST）
    # ──────────────────────────────────────────────────────────────────────

    def begin_segment(
        self,
        client_id: str,
        component_label: int,
        *,
        rtx: str,
        view_type: int = 0,
    ):
        """开始拆分：进入「分割状态」，指定要拆分的部件。

        Args:
            client_id: 分割会话 ID（由 ``init_segment`` / ``open_segment`` 返回）。
            component_label: 要拆分的部件 label。
            rtx: 实际使用人的 RTX。**必填**。
            view_type: 视图类型，0 主视图 / 1 左视图 / 2 右视图 / 3 背视图，默认 0。

        Returns:
            单视图操作结果（``OperatorResult`` 字典）。

        Raises:
            WeaverError / 子类: 接口错误
        """
        body: dict = {
            "client_id": client_id,
            "view_type": view_type,
            "component_label": component_label,
        }
        return self._http.post("openapi/weaver/component/begin_segment", body, rtx=rtx)

    def segment_component(
        self,
        client_id: str,
        *,
        rtx: str,
        view_type: int = 0,
        add_pixels: Optional[list] = None,
        remove_pixels: Optional[list] = None,
        rects: Optional[list] = None,
    ):
        """拆分：在分割状态下圈定要拆出的区域（可反复执行）。

        ``add_pixels`` 为正点（前景像素点）、``remove_pixels`` 为负点（背景像素点）、
        ``rects`` 为矩形框，三者共同圈定拆分区域。

        Args:
            client_id: 分割会话 ID。
            rtx: 实际使用人的 RTX。**必填**。
            view_type: 视图类型，默认 0。
            add_pixels: 正点列表，元素为 ``{"x": int, "y": int}``。
            remove_pixels: 负点列表，元素为 ``{"x": int, "y": int}``。
            rects: 矩形框列表，元素为
                ``{"left_top_pixel": {"x": int, "y": int}, "right_bottom_pixel": {"x": int, "y": int}}``。

        Returns:
            单视图操作结果（``OperatorResult`` 字典）。

        Raises:
            WeaverError / 子类: 接口错误
        """
        body: dict = {"client_id": client_id, "view_type": view_type}
        if add_pixels:
            body["add_pixels"] = add_pixels
        if remove_pixels:
            body["remove_pixels"] = remove_pixels
        if rects:
            body["rects"] = rects
        return self._http.post("openapi/weaver/component/segment", body, rtx=rtx)

    def confirm_segment(self, client_id: str, *, rtx: str, view_type: int = 0):
        """确认拆分：固化当前分割结果。

        Args:
            client_id: 分割会话 ID。
            rtx: 实际使用人的 RTX。**必填**。
            view_type: 视图类型，默认 0。

        Returns:
            单视图操作结果（``OperatorResult`` 字典）。

        Raises:
            WeaverError / 子类: 接口错误
        """
        body: dict = {"client_id": client_id, "view_type": view_type}
        return self._http.post("openapi/weaver/component/confirm_segment", body, rtx=rtx)

    def cancel_segment(self, client_id: str, *, rtx: str, view_type: int = 0):
        """取消拆分：回退到分割开始前的状态。

        Args:
            client_id: 分割会话 ID。
            rtx: 实际使用人的 RTX。**必填**。
            view_type: 视图类型，默认 0。

        Returns:
            单视图操作结果（``OperatorResult`` 字典）。

        Raises:
            WeaverError / 子类: 接口错误
        """
        body: dict = {"client_id": client_id, "view_type": view_type}
        return self._http.post("openapi/weaver/component/cancel_segment", body, rtx=rtx)

    def merge_component(
        self,
        client_id: str,
        component_labels: list,
        *,
        rtx: str,
        view_type: int = 0,
    ):
        """合并：将多个部件合并为一个连通体。

        Args:
            client_id: 分割会话 ID。
            component_labels: 要合并的部件 label 列表。
            rtx: 实际使用人的 RTX。**必填**。
            view_type: 视图类型，默认 0。

        Returns:
            多视图结果（``MultiViewSegmentResult`` 字典）。

        Raises:
            WeaverError / 子类: 接口错误
        """
        body: dict = {
            "client_id": client_id,
            "component_labels": component_labels,
            "view_type": view_type,
        }
        return self._http.post("openapi/weaver/component/merge", body, rtx=rtx)

    def auto_merge_component(self, client_id: str, *, rtx: str):
        """自动合并：自动合并所有相邻的连通体，无需指定 label。

        Args:
            client_id: 分割会话 ID。
            rtx: 实际使用人的 RTX。**必填**。

        Returns:
            多视图结果（``MultiViewSegmentResult`` 字典）。

        Raises:
            WeaverError / 子类: 接口错误
        """
        body: dict = {"client_id": client_id}
        return self._http.post("openapi/weaver/component/auto_merge", body, rtx=rtx)

    def boundary_adjust(
        self,
        client_id: str,
        component_label: int,
        paint_mask: str,
        *,
        rtx: str,
        view_type: int = 0,
    ):
        """修边：通过涂抹区域调整部件边界。

        Args:
            client_id: 分割会话 ID。
            component_label: 要调整边界的部件 label。
            paint_mask: 涂抹区域掩膜的 base64 编码。注意：这是与掩膜尺寸一致的
                **原始单字节数组**（每像素 1 字节，取值 0~255，非 0 表示涂抹）的 base64，
                而非 PNG 图片的 base64。
            rtx: 实际使用人的 RTX。**必填**。
            view_type: 视图类型，默认 0。

        Returns:
            单视图操作结果（``OperatorResult`` 字典）。

        Raises:
            WeaverError / 子类: 接口错误
        """
        body: dict = {
            "client_id": client_id,
            "view_type": view_type,
            "paint_mask": paint_mask,
            "component_label": component_label,
        }
        return self._http.post("openapi/weaver/component/boundary_adjust", body, rtx=rtx)

    def rename_component(
        self,
        client_id: str,
        component_label: int,
        new_name: str,
        *,
        rtx: str,
        view_type: int = 0,
    ):
        """部件重命名：重命名指定部件，四视图下同步修改所有视图。

        Args:
            client_id: 分割会话 ID。
            component_label: 要重命名的部件 label。
            new_name: 新名称，最长 20 个字符（60 字节）。
            rtx: 实际使用人的 RTX。**必填**。
            view_type: 视图类型，默认 0。

        Returns:
            多视图结果（``MultiViewSegmentResult`` 字典）。

        Raises:
            WeaverError / 子类: 接口错误
        """
        body: dict = {
            "client_id": client_id,
            "view_type": view_type,
            "component_label": component_label,
            "new_name": new_name,
        }
        return self._http.post("openapi/weaver/component/part_rename", body, rtx=rtx)

    def save_segment(
        self,
        client_id: str,
        name: str,
        algorithm_model: str,
        *,
        rtx: str,
        opened_model_id: Optional[str] = None,
    ):
        """保存拆分：将当前分割结果持久化为独立的 2D 分割资产（``node_type=14``）。

        Args:
            client_id: 分割会话 ID。
            name: 资产名称，1~100 个字符。
            algorithm_model: 2D 分割算法模型。
            rtx: 实际使用人的 RTX。**必填**。
            opened_model_id: 二次编辑时打开的原分割资产 ID，用于继承前端传参。

        Returns:
            模型资产信息（``ModelInfo`` 字典），``node_type=14``，可作为图生模任务的
            ``segment_model_id``。

        Raises:
            WeaverError / 子类: 接口错误
        """
        body: dict = {
            "client_id": client_id,
            "name": name,
            "algorithm_model": algorithm_model,
        }
        if opened_model_id:
            body["opened_model_id"] = opened_model_id
        return self._http.post("openapi/weaver/component/save_segment", body, rtx=rtx)

    def open_segment(self, model_id: str, *, rtx: str):
        """打开已有拆分：打开已保存的分割资产进行二次编辑，返回新的 ``client_id``。

        Args:
            model_id: 分割资产的 model_id（``node_type=14``）。
            rtx: 实际使用人的 RTX。**必填**。

        Returns:
            多视图结果（``MultiViewSegmentResult`` 字典），其中 ``client_id`` 为新的
            分割会话 ID。

        Raises:
            WeaverError / 子类: 接口错误
        """
        body: dict = {"model_id": model_id}
        return self._http.post("openapi/weaver/component/open_segment", body, rtx=rtx)
