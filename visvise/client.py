"""
VISVISE Weaver SDK - 主客户端

提供：
- 原子 API 方法（通过 .api 属性）
- 各节点类型的高阶 gen_xxx() 方法（封装上传 + 创建任务）
- wait_model() 轮询方法
"""

from __future__ import annotations

import io
import logging
import os
import time
import uuid
import zipfile
from typing import IO, Optional, Union

from .api import VisviseAPI
from .exceptions import ModelGenerationError, PollingTimeoutError, WeaverError
from .http import Environment, WeaverHTTPClient
from .models import (
    GetCosCredResult,
    ModelInfo,
    ModelStatus,
    NodeType,
    ReduceFace,
    UserQuota,
    View,
)

logger = logging.getLogger("visvise.client")

# 文件输入类型：本地路径字符串 / bytes 二进制内容 / 文件对象（BinaryIO）
FileInput = Union[str, bytes, IO[bytes]]

# 直接支持的模型格式（非 zip，需要自动打包）
_MODEL_EXTENSIONS = {".fbx", ".obj", ".glb", ".gltf"}


def _is_zip_bytes(data: bytes) -> bool:
    """通过 magic bytes 判断内容是否为 zip 格式。"""
    return data[:4] == b"PK\x03\x04"


def _wrap_in_zip(data: bytes, inner_filename: str) -> bytes:
    """将单个文件打包为内存 zip，返回 zip bytes。"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(inner_filename, data)
    return buf.getvalue()


class VisviseClient:
    """VISVISE Weaver Python SDK 主入口。

    使用方式::

        from visvise import VisviseClient, Environment

        # 线上生产环境（默认）
        client = VisviseClient(app_id="your_app_id", secret_key="your_key", uid="your_uid")

        # 测试环境
        client = VisviseClient("app_id", "key", "uid", env=Environment.TEST)

        # 开发环境
        client = VisviseClient("app_id", "key", "uid", env=Environment.DEV)

        # 自定义域名（如代理）
        client = VisviseClient("app_id", "key", "uid", env="https://my-proxy.example.com")

        # 高阶方法：自动上传文件 + 创建任务，返回 model_id
        model_id = client.gen_360(
            main_view="/path/to/character.png",
            algorithm_model="hunyuan3D-MultiView-v3.0",
        )

        # 等待完成
        model = client.wait_model(model_id)
        print(model.output_model)

    Args:
        app_id: 由平台分配的客户端标识。
        secret_key: 由平台分配的签名密钥。
        uid: 用户 ID，从申请 key 的登录账号获取。当前一期未做严格校验，但必须传入；二期将做严格校验。
        env: 环境配置，支持 :class:`~visvise.http.Environment` 枚举或自定义 URL 字符串。
             默认 :attr:`~visvise.http.Environment.PROD`（线上生产环境）。
        timeout: 单次 HTTP 请求超时（秒），默认 30。
    """

    def __init__(
        self,
        app_id: str,
        secret_key: str,
        uid: str,
        env: str | Environment = Environment.PROD,
        timeout: int = 30,
    ):
        self._http = WeaverHTTPClient(
            app_id=app_id,
            secret_key=secret_key,
            uid=uid,
            base_url=env,
            timeout=timeout,
        )
        self.api = VisviseAPI(self._http)

    # ══════════════════════════════════════════════════════════════════════
    # COS 文件上传工具（内部使用）
    # ══════════════════════════════════════════════════════════════════════

    def _resolve_file(
        self,
        source: FileInput,
        filename: Optional[str] = None,
        is_temp: bool = False,
    ) -> str:
        """将文件输入统一解析并上传到 COS，返回 VISVISE 平台 COS URL。

        支持三种输入形式：

        * **本地路径**（``str``）：文件路径，检测到为已有文件则上传；
          若为 ``https://`` 等 URL 字符串，直接原样返回，不上传。
          ⚠️  传入 URL 时，必须是通过本 SDK 或 VISVISE 平台上传所得的 VISVISE 平台 COS URL，
          不能使用其他业务或第三方的 COS 地址，否则服务端无法访问该文件。
        * **bytes**：原始二进制内容，直接上传。
        * **文件对象**（``IO[bytes]``，如 ``open(..., "rb")``、``BytesIO``）：
          读取内容后上传。

        Args:
            source: 文件输入，支持本地路径 / bytes / BinaryIO。
            filename: 上传到 COS 时使用的文件名。
                      bytes/BinaryIO 输入时建议提供以便平台识别格式；
                      省略时自动生成随机名。
            is_temp: 是否临时文件（7天后自动删除）。

        Returns:
            上传后的 VISVISE 平台 COS URL，或原始 URL 字符串（如果 source 本身已是 URL）。

        Raises:
            ImportError: 未安装 cos-python-sdk-v5。
            WeaverError: 获取凭证失败。
        """
        # ── 已是 URL（VISVISE 平台 COS URL），直接返回，不再上传 ──
        # 注意：此处仅做格式判断，调用方需确保传入的 URL 来自 VISVISE 平台
        if isinstance(source, str) and not os.path.isfile(source):
            return source

        try:
            from qcloud_cos import CosConfig, CosS3Client  # type: ignore
        except ImportError as e:
            raise ImportError(
                "文件上传需要安装 cos-python-sdk-v5：pip install cos-python-sdk-v5"
            ) from e

        cred: GetCosCredResult = self.api.get_cos_cred(is_temp=is_temp)
        config = CosConfig(
            Region=cred.region,
            SecretId=cred.cred.tmp_secret_id,
            SecretKey=cred.cred.tmp_secret_key,
            Token=cred.cred.session_token,
        )
        cos_client = CosS3Client(config)

        # ── 确定上传内容和文件名 ──
        path_prefix = cred.path_prefix.rstrip("/") + "/"
        if isinstance(source, str):
            # 本地路径
            _filename = filename or os.path.basename(source)
            cos_key = f"{path_prefix}{_filename}"
            logger.info("上传文件 %s → cos://%s/%s", source, cred.bucket, cos_key)
            with open(source, "rb") as f:
                cos_client.put_object(Bucket=cred.bucket, Body=f, Key=cos_key)

        elif isinstance(source, (bytes, bytearray)):
            # 二进制内容
            _filename = filename or f"upload_{uuid.uuid4().hex[:8]}.bin"
            cos_key = f"{path_prefix}{_filename}"
            logger.info("上传 bytes (%d bytes) → cos://%s/%s", len(source), cred.bucket, cos_key)
            cos_client.put_object(Bucket=cred.bucket, Body=source, Key=cos_key)

        else:
            # 文件对象 (BinaryIO / BytesIO)
            data = source.read()
            _filename = filename or getattr(source, "name", None)
            _filename = os.path.basename(_filename) if _filename else f"upload_{uuid.uuid4().hex[:8]}.bin"
            cos_key = f"{path_prefix}{_filename}"
            logger.info("上传文件对象 (%d bytes) → cos://%s/%s", len(data), cred.bucket, cos_key)
            cos_client.put_object(Bucket=cred.bucket, Body=data, Key=cos_key)

        cos_url = f"https://{cred.bucket}.cos.{cred.region}.myqcloud.com/{cos_key}"
        logger.info("上传完成：%s", cos_url)
        return cos_url

    # 向后兼容别名
    def _upload_file(self, source: FileInput, filename: Optional[str] = None, is_temp: bool = False) -> str:
        return self._resolve_file(source, filename=filename, is_temp=is_temp)

    # ══════════════════════════════════════════════════════════════════════
    # 模型 zip 构建工具（骨骼架设 / 蒙皮共用）
    # ══════════════════════════════════════════════════════════════════════

    def _build_model_zip(
        self,
        source: FileInput,
        json_data: dict,
        filename: Optional[str] = None,
    ) -> tuple[bytes, str]:
        """从模型文件输入构建包含 JSON 参数文件的 zip 包。

        处理逻辑：

        1. 读取 source 的原始字节内容。
        2. **若原始内容本身是 zip**：
           - 解压，找到第一个非 ``.json`` 的文件作为模型文件。
           - 用传入的 ``json_data`` 替换（或新增）同名 ``.json`` 文件。
           - 重新打包成新的 zip。
        3. **若原始内容不是 zip**（裸模型文件，如 .fbx / .obj / .glb）：
           - 以 ``filename`` 命名该文件，生成同名 ``.json``，一起打包成 zip。

        Args:
            source: 模型文件输入，支持本地路径（str）、bytes 或 BinaryIO。
                    ⚠️ 不接受 COS URL。
            json_data: 要写入 json 参数文件的 Python dict。
            filename: bytes/BinaryIO 输入时指定文件名（含扩展名）。
                      如省略则自动生成。

        Returns:
            ``(zip_bytes, zip_filename)``：打包后的 zip 内容和文件名。

        Raises:
            ValueError: source 为 COS URL 字符串时抛出。
        """
        import json as _json

        # ── 读取原始字节 & 确定来源文件名 ──
        if isinstance(source, str):
            if not os.path.isfile(source):
                raise ValueError(
                    f"model_path 只接受本地文件路径或二进制内容，不接受 COS URL：{source!r}"
                )
            src_filename = filename or os.path.basename(source)
            with open(source, "rb") as f:
                raw = f.read()
        elif isinstance(source, (bytes, bytearray)):
            raw = bytes(source)
            src_filename = filename or f"model_{uuid.uuid4().hex[:8]}.fbx"
        else:
            raw = source.read()
            src_filename = filename or getattr(source, "name", None)
            src_filename = (
                os.path.basename(src_filename)
                if src_filename
                else f"model_{uuid.uuid4().hex[:8]}.fbx"
            )

        json_bytes = _json.dumps(json_data, ensure_ascii=False, indent=2).encode("utf-8")

        # ── 若原始内容是 zip，解压后重新打包 ──
        if _is_zip_bytes(raw):
            logger.debug("_build_model_zip: 输入已是 zip，解压后重新打包")
            existing: dict[str, bytes] = {}
            with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                for name in zf.namelist():
                    existing[name] = zf.read(name)

            # 找到模型文件（第一个非 .json 的条目）
            model_entry = next(
                (n for n in existing if not n.lower().endswith(".json")), None
            )
            if model_entry is None:
                raise ValueError("输入的 zip 包中未找到模型文件（非 .json 条目）")

            stem = os.path.splitext(model_entry)[0]
            json_entry = f"{stem}.json"
            zip_filename = f"{stem}.zip"

            # 替换 / 新增 json，保留其他文件
            new_files: dict[str, bytes] = {
                k: v for k, v in existing.items() if k != json_entry
            }
            new_files[json_entry] = json_bytes

            logger.info(
                "_build_model_zip: 重打包 zip，model=%s json=%s → %s",
                model_entry, json_entry, zip_filename,
            )

        else:
            # ── 裸模型文件，直接打包 ──
            stem = os.path.splitext(src_filename)[0]
            json_entry = f"{stem}.json"
            zip_filename = f"{stem}.zip"
            new_files = {
                src_filename: raw,
                json_entry: json_bytes,
            }
            logger.info(
                "_build_model_zip: 打包 %s + %s → %s",
                src_filename, json_entry, zip_filename,
            )

        # ── 组装 zip ──
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for entry_name, entry_data in new_files.items():
                zf.writestr(entry_name, entry_data)

        return buf.getvalue(), zip_filename

    # ══════════════════════════════════════════════════════════════════════
    # 模型文件专用上传（自动 zip 打包）
    # ══════════════════════════════════════════════════════════════════════

    def _resolve_model_file(
        self,
        source: FileInput,
        filename: Optional[str] = None,
        is_temp: bool = False,
    ) -> str:
        """上传模型文件到 COS，自动处理 zip 打包逻辑。

        规则：
        - 已是 **VISVISE 平台 COS URL**（``https://`` 字符串）：直接返回，不做任何处理。
          ⚠️  必须是通过本 SDK 或 VISVISE 平台上传所得的 VISVISE 平台 COS URL，不能使用其他业务的地址。
        - 已是 **zip 文件**（本地 .zip 路径 / zip 格式的 bytes/BinaryIO）：直接上传。
        - 是 **模型文件**（.fbx / .obj / .glb 等本地路径 / 对应 bytes/BinaryIO）：
          自动打包为 zip 后上传，zip 内文件名保留原始文件名。

        Args:
            source: 文件输入，支持三种形式：
                - 本地路径（str）
                - VISVISE 平台 COS URL（str，必须是本平台上传所得地址）
                - bytes 或 BinaryIO（二进制内容）
            filename: bytes/BinaryIO 输入时指定文件名（含扩展名，如 ``model.fbx``）。
                      用于判断是否需要打包，以及 zip 内部的文件名。
                      若省略且无法从 source 推断，则视为 zip 直接上传。
            is_temp: 是否临时文件。

        Returns:
            上传后的 VISVISE 平台 COS URL，或原始 URL 字符串。
        """
        # ── 已是 URL，直接返回 ──
        if isinstance(source, str) and not os.path.isfile(source):
            return source

        # ── 本地路径处理 ──
        if isinstance(source, str):
            ext = os.path.splitext(source)[1].lower()
            if ext in _MODEL_EXTENSIONS:
                # 非 zip 模型文件：读取 → 打包 → 上传
                with open(source, "rb") as f:
                    raw = f.read()
                base = os.path.basename(source)
                stem = os.path.splitext(base)[0]
                zip_bytes = _wrap_in_zip(raw, base)
                zip_name = f"{stem}.zip"
                logger.info("自动打包 %s → %s 后上传", base, zip_name)
                return self._resolve_file(zip_bytes, filename=zip_name, is_temp=is_temp)
            else:
                # .zip 或其他格式，直接上传
                return self._resolve_file(source, filename=filename, is_temp=is_temp)

        # ── bytes / BinaryIO：读取内容 ──
        if isinstance(source, (bytes, bytearray)):
            raw = bytes(source)
        else:
            raw = source.read()
            # 尝试从文件对象 name 属性获取文件名
            if filename is None:
                name_attr = getattr(source, "name", None)
                if name_attr:
                    filename = os.path.basename(name_attr)

        # 判断是否已经是 zip
        if _is_zip_bytes(raw):
            _fname = filename or f"model_{uuid.uuid4().hex[:8]}.zip"
            logger.debug("内容已是 zip 格式，直接上传：%s", _fname)
            return self._resolve_file(raw, filename=_fname, is_temp=is_temp)

        # 非 zip：需要打包
        if filename:
            inner_name = filename
            stem = os.path.splitext(filename)[0]
            zip_name = f"{stem}.zip"
        else:
            inner_name = f"model_{uuid.uuid4().hex[:8]}.fbx"
            zip_name = inner_name.replace(".fbx", ".zip")

        zip_bytes = _wrap_in_zip(raw, inner_name)
        logger.info("自动打包二进制内容（%d bytes）→ %s 后上传", len(raw), zip_name)
        return self._resolve_file(zip_bytes, filename=zip_name, is_temp=is_temp)

    # ══════════════════════════════════════════════════════════════════════
    # wait_model —— 轮询等待模型完成
    # ══════════════════════════════════════════════════════════════════════

    def wait_model(
        self,
        model_id: str,
        interval: float = 2.0,
        timeout: int = 600,
    ) -> ModelInfo:
        """轮询等待模型生成完成。

        Args:
            model_id: 要等待的模型 ID。
            interval: 轮询间隔（秒），默认 2s。
            timeout: 超时时长（秒），默认 600s（10分钟）。

        Returns:
            完成后的 :class:`~visvise.models.ModelInfo`。

        Raises:
            PollingTimeoutError: 超过 timeout 仍未完成。
            ModelGenerationError: 模型生成失败（status=4）。
            InvalidParamsError: 轮询接口返回参数错误时立即抛出（不重试）。
            注意：其他业务/网络错误不抛出异常，会打印日志并继续重试。
        """
        from .exceptions import InvalidParamsError  # 避免循环导入
        start = time.time()

        while True:
            elapsed = time.time() - start
            if elapsed >= timeout:
                raise PollingTimeoutError(model_id, timeout)

            try:
                models, _ = self.api.get_model_list(model_id_list=[model_id], limit=10)
            except InvalidParamsError:
                # 参数错误无法靠重试恢复，直接抛出
                raise
            except WeaverError as e:
                # 其他接口错误：打印警告，继续等待
                logger.warning("轮询时接口错误（将继续重试）: %s", e)
                time.sleep(interval)
                continue

            if not models:
                logger.warning("未找到模型 %s，继续等待...", model_id)
                time.sleep(interval)
                continue

            model = models[0]

            if model.status == ModelStatus.SUCCESS:
                logger.info(
                    "模型 %s 生成成功（耗时 %ds）output_model=%s",
                    model_id,
                    model.time_cost,
                    model.output_model,
                )
                return model

            if model.status == ModelStatus.FAILED:
                fr = model.failed_reason
                code = fr.code if fr else -1
                reason = fr.reason if fr else "未知原因"
                raise ModelGenerationError(
                    f"模型生成失败: {reason}",
                    code=code,
                    model_id=model_id,
                )

            # PENDING / RUNNING
            remaining = model.remaining_time
            status_name = "等待中" if model.status == ModelStatus.PENDING else "生成中"
            logger.debug(
                "模型 %s %s，预计剩余 %ds（已等待 %.0fs）",
                model_id,
                status_name,
                remaining,
                elapsed,
            )
            time.sleep(interval)

    # ══════════════════════════════════════════════════════════════════════
    # 高阶方法：gen_xxx
    # 每个方法对应一种节点类型，封装「上传文件 + 创建任务」，返回 model_id
    # ══════════════════════════════════════════════════════════════════════

    # ── 3.1 图生360 ─────────────────────────────────────────────────────

    def gen_360(
        self,
        main_view: FileInput,
        algorithm_model: str,
        name: str = "gen_360",
        *,
        main_view_filename: Optional[str] = None,
        enable_a_pose: Optional[bool] = None,
        style: Optional[str] = None,
        back_view: Optional[FileInput] = None,
        back_view_filename: Optional[str] = None,
        left_view: Optional[FileInput] = None,
        left_view_filename: Optional[str] = None,
        right_view: Optional[FileInput] = None,
        right_view_filename: Optional[str] = None,
    ) -> str:
        """图生360：从图片生成多视图。

        Args:
            main_view: 主视图，支持本地路径、VISVISE 平台 COS URL 或 bytes/BinaryIO。
            algorithm_model: 算法模型名称（如 ``hunyuan3D-MultiView-v3.0``）。
            name: 任务名称。
            main_view_filename: bytes/BinaryIO 输入时指定文件名（含扩展名）。
            enable_a_pose: 是否开启 A-Pose。
            style: 风格类型（仅 VISVISE 自研模型支持）。
            back_view / left_view / right_view: 可选的额外视图，同样支持三种输入形式。
            back_view_filename / left_view_filename / right_view_filename: 对应文件名。

        Returns:
            新生成的模型 ID。

        Raises:
            WeaverError / 子类
        """
        view = View(
            main_view=self._resolve_file(main_view, filename=main_view_filename),
            back_view=self._resolve_file(back_view, filename=back_view_filename) if back_view is not None else None,
            left_view=self._resolve_file(left_view, filename=left_view_filename) if left_view is not None else None,
            right_view=self._resolve_file(right_view, filename=right_view_filename) if right_view is not None else None,
        )
        img360: dict = {"algorithm_model": algorithm_model}
        if enable_a_pose is not None:
            img360["enable_a_pose"] = enable_a_pose
        if style:
            img360["style"] = style

        return self.api.gen_multi_views(
            name=name,
            input_view=view,
            params={"image_gen_360_params": img360},
        )

    # ── 3.2 图生高模 ─────────────────────────────────────────────────────

    def gen_high_model(
        self,
        main_view: FileInput,
        algorithm_model: str,
        output_model_format: str = "fbx",
        face_type: int = 1,
        name: str = "gen_high_model",
        *,
        main_view_filename: Optional[str] = None,
        face_num: Optional[int] = None,
        back_view: Optional[FileInput] = None,
        back_view_filename: Optional[str] = None,
        left_view: Optional[FileInput] = None,
        left_view_filename: Optional[str] = None,
        right_view: Optional[FileInput] = None,
        right_view_filename: Optional[str] = None,
    ) -> str:
        """图生高模（node_type=3）。

        Args:
            main_view: 主视图，支持本地路径、VISVISE 平台 COS URL 或 bytes/BinaryIO。
            algorithm_model: 算法模型名称（可通过 list_algorithm_model(node_type=3) 获取）。
            output_model_format: 输出格式 fbx/obj/glb，默认 fbx。
            face_type: 面数类型 1:三角面 2:四边面，默认 1。
            name: 任务名称。
            main_view_filename: bytes/BinaryIO 时指定文件名。
            face_num: 面数，取值范围 1000~1500000，不传自动配置。
            back_view / left_view / right_view: 额外视图，同样支持三种输入形式。

        Returns:
            新生成的模型 ID。
        """
        view = View(
            main_view=self._resolve_file(main_view, filename=main_view_filename),
            back_view=self._resolve_file(back_view, filename=back_view_filename) if back_view is not None else None,
            left_view=self._resolve_file(left_view, filename=left_view_filename) if left_view is not None else None,
            right_view=self._resolve_file(right_view, filename=right_view_filename) if right_view is not None else None,
        )
        img_params: dict = {
            "algorithm_model": algorithm_model,
            "output_model_format": output_model_format,
            "face_type": face_type,
        }
        if face_num is not None:
            img_params["face_num"] = face_num

        return self.api.gen_3d_model(
            name=name,
            node_type=NodeType.IMG_TO_3D_HIGH,
            params={"image_gen_model_params": img_params},
            input_view=view,
        )[0]

    # ── 3.3 图生中模 ─────────────────────────────────────────────────────

    def gen_mid_model(
        self,
        main_view: FileInput,
        back_view: FileInput,
        left_view: FileInput,
        right_view: FileInput,
        algorithm_model: str,
        output_model_format: str = "fbx",
        face_type: int = 1,
        name: str = "gen_mid_model",
        *,
        main_view_filename: Optional[str] = None,
        back_view_filename: Optional[str] = None,
        left_view_filename: Optional[str] = None,
        right_view_filename: Optional[str] = None,
    ) -> str:
        """图生中模（node_type=11）。

        注意：中模要求四视图全部必传。

        Args:
            main_view / back_view / left_view / right_view: 四视图，均支持本地路径、VISVISE 平台 COS URL 或 bytes/BinaryIO。
            algorithm_model: 算法模型（可通过 list_algorithm_model(node_type=11) 获取）。
            output_model_format: 输出格式，默认 fbx。
            face_type: 面数类型，默认 1。
            name: 任务名称。
            *_filename: bytes/BinaryIO 输入时对应的文件名。

        Returns:
            新生成的模型 ID。
        """
        view = View(
            main_view=self._resolve_file(main_view, filename=main_view_filename),
            back_view=self._resolve_file(back_view, filename=back_view_filename),
            left_view=self._resolve_file(left_view, filename=left_view_filename),
            right_view=self._resolve_file(right_view, filename=right_view_filename),
        )
        return self.api.gen_3d_model(
            name=name,
            node_type=NodeType.IMG_TO_3D_MID,
            params={"image_gen_model_params": {
                "algorithm_model": algorithm_model,
                "output_model_format": output_model_format,
                "face_type": face_type,
            }},
            input_view=view,
        )[0]

    # ── 3.4 图生低模 ─────────────────────────────────────────────────────

    def gen_low_model(
        self,
        main_view: FileInput,
        algorithm_model: str,
        output_model_format: str = "fbx",
        face_type: int = 1,
        name: str = "gen_low_model",
        *,
        main_view_filename: Optional[str] = None,
        back_view: Optional[FileInput] = None,
        back_view_filename: Optional[str] = None,
        left_view: Optional[FileInput] = None,
        left_view_filename: Optional[str] = None,
        right_view: Optional[FileInput] = None,
        right_view_filename: Optional[str] = None,
    ) -> str:
        """图生低模（node_type=13）。

        Args:
            main_view: 主视图（必传），支持本地路径、VISVISE 平台 COS URL 或 bytes/BinaryIO。
            algorithm_model: 算法模型（如 ``Tripo-v1.0-快速生成``）。
            back_view / left_view / right_view: 可选额外视图。
        """
        view = View(
            main_view=self._resolve_file(main_view, filename=main_view_filename),
            back_view=self._resolve_file(back_view, filename=back_view_filename) if back_view is not None else None,
            left_view=self._resolve_file(left_view, filename=left_view_filename) if left_view is not None else None,
            right_view=self._resolve_file(right_view, filename=right_view_filename) if right_view is not None else None,
        )
        return self.api.gen_3d_model(
            name=name,
            node_type=NodeType.IMG_TO_3D_LOW,
            params={"image_gen_model_params": {
                "algorithm_model": algorithm_model,
                "output_model_format": output_model_format,
                "face_type": face_type,
            }},
            input_view=view,
        )[0]

    # ── 3.5 重布线 ───────────────────────────────────────────────────────

    def gen_mesh_refine(
        self,
        model_path: FileInput,
        algorithm_model: str,
        input_model_format: str = "fbx",
        name: str = "gen_mesh_refine",
        *,
        filename: Optional[str] = None,
        enable_detail_preserve: Optional[bool] = None,
    ) -> str:
        """重布线/布线优化（node_type=10）。

        Args:
            model_path: 输入模型（zip），支持本地路径、VISVISE 平台 COS URL 或 bytes/BinaryIO。
            algorithm_model: 算法模型（如 ``VISVISE-MeshRefine-V1.0.0``）。
            input_model_format: 输入模型格式，默认 fbx。
            name: 任务名称。
            filename: bytes/BinaryIO 时指定文件名（建议带 .zip 后缀）。
            enable_detail_preserve: 是否细节保留。
        """
        cos_url = self._resolve_model_file(model_path, filename=filename)
        params: dict = {
            "algorithm_model": algorithm_model,
            "input_model_format": input_model_format,
        }
        if enable_detail_preserve is not None:
            params["enable_detail_preserve"] = enable_detail_preserve

        return self.api.gen_3d_model(
            name=name,
            node_type=NodeType.MESH_REFINE,
            params={"mesh_refine_params": params},
            input_model=cos_url,
        )[0]

    # ── 3.6 重拓扑 ───────────────────────────────────────────────────────

    def gen_retopology(
        self,
        model_path: FileInput,
        algorithm_model: str,
        output_model_format: str = "fbx",
        face_type: int = 2,
        name: str = "gen_retopology",
        *,
        filename: Optional[str] = None,
        detail_level: Optional[int] = None,
        face_num: Optional[int] = None,
    ) -> str:
        """重拓扑（node_type=1）。

        Args:
            model_path: 输入模型（zip），支持本地路径、VISVISE 平台 COS URL 或 bytes/BinaryIO。
            algorithm_model: 算法模型（如 ``hunyuan3D-RTP-v1.5``）。
            output_model_format: 输出格式，默认 fbx。
            face_type: 面数类型 1:三角面 2:四边面，默认 2。
            name: 任务名称。
            filename: bytes/BinaryIO 时指定文件名。
            detail_level: 精细程度 1/2/3（混元模型必传）。
            face_num: 指定面数（VISVISE 自研模型必传）。

        Note:
            ``detail_level`` 和 ``face_num`` 根据算法模型二选一。
        """
        cos_url = self._resolve_model_file(model_path, filename=filename)
        params: dict = {
            "algorithm_model": algorithm_model,
            "output_model_format": output_model_format,
            "face_type": face_type,
        }
        if detail_level is not None:
            params["detail_level"] = detail_level
        if face_num is not None:
            params["face_num"] = face_num

        return self.api.gen_3d_model(
            name=name,
            node_type=NodeType.RE_TOPOLOGY,
            params={"re_topology_params": params},
            input_model=cos_url,
        )[0]

    # ── 3.7 LOD ──────────────────────────────────────────────────────────

    def gen_lod(
        self,
        model_path: FileInput,
        algorithm_model: str,
        reduce_faces: list[ReduceFace],
        output_model_format: str = "fbx",
        name: str = "gen_lod",
        *,
        filename: Optional[str] = None,
        gen_times: int = 3,
    ) -> list[str]:
        """LOD 减面（node_type=2）。

        Args:
            model_path: 输入模型（zip），支持本地路径、VISVISE 平台 COS URL 或 bytes/BinaryIO。
            algorithm_model: 算法模型（如 ``VISVISE-LOD-V1.0.0``）。
            reduce_faces: 减面配置列表，参考 :class:`~visvise.models.ReduceFace`。
            output_model_format: 输出格式，默认 fbx。
            name: 任务名称。
            filename: bytes/BinaryIO 时指定文件名。
            gen_times: 生成次数（用于抽卡），不需要抽卡传 1，建议传 3。

        Returns:
            模型 ID 列表（gen_times=3 时返回 3 个 ID）。
        """
        cos_url = self._resolve_model_file(model_path, filename=filename)
        return self.api.gen_3d_model(
            name=name,
            node_type=NodeType.LOD,
            params={"lod_params": {
                "algorithm_model": algorithm_model,
                "output_model_format": output_model_format,
                "reduce_faces": [rf.to_dict() for rf in reduce_faces],
                "gen_times": gen_times,
            }},
            input_model=cos_url,
        )

    # ── 3.8 UV 展开 ───────────────────────────────────────────────────────

    def gen_uv(
        self,
        model_path: FileInput,
        algorithm_model: str,
        name: str = "gen_uv",
        *,
        filename: Optional[str] = None,
        enable_auto_smoothing: Optional[bool] = None,
    ) -> str:
        """UV 展开（node_type=9）。

        Args:
            model_path: 输入模型（zip），支持本地路径、VISVISE 平台 COS URL 或 bytes/BinaryIO。
            algorithm_model: UV 展开算法模型名称。
            name: 任务名称。
            filename: bytes/BinaryIO 时指定文件名。
            enable_auto_smoothing: 可选，是否启用自动平滑。

        Returns:
            新生成的模型 ID。
        """
        cos_url = self._resolve_model_file(model_path, filename=filename)
        uv_params: dict = {"algorithm_model": algorithm_model}
        if enable_auto_smoothing is not None:
            uv_params["enable_auto_smoothing"] = enable_auto_smoothing

        return self.api.gen_3d_model(
            name=name,
            node_type=NodeType.UV,
            params={"uv_params": uv_params},
            input_model=cos_url,
        )[0]

    # ── 3.9 贴图纹理 ─────────────────────────────────────────────────────

    def gen_texture(
        self,
        model_path: FileInput,
        algorithm_model: str,
        name: str = "gen_texture",
        *,
        filename: Optional[str] = None,
        input_view: Optional[View] = None,
        resolution: Optional[int] = None,
        unwarp_uv: Optional[bool] = None,
        prompt: Optional[str] = None,
    ) -> str:
        """贴图纹理生成（node_type=8）。

        Args:
            model_path: 输入模型（zip），支持本地路径、VISVISE 平台 COS URL 或 bytes/BinaryIO。
            algorithm_model: 贴图算法模型名称。
            name: 任务名称。
            filename: bytes/BinaryIO 时指定文件名。
            input_view: 原画视图（:class:`~visvise.models.View`），支持传入四视图。
                        ``main_view`` 与 ``prompt`` 必须传其中一个，可同时传入。
            resolution: 可选，贴图分辨率（如 ``1024``、``2048``）。
            unwarp_uv: 可选，是否同时展开 UV。
            prompt: 贴图文本提示词，与 ``input_view.main_view`` 必须传其中一个，可同时传入。

        Raises:
            ValueError: ``input_view.main_view`` 和 ``prompt`` 均未传时抛出。

        Returns:
            新生成的模型 ID。
        """
        main_view_url = input_view.main_view if input_view else None
        if not main_view_url and not prompt:
            raise ValueError(
                "gen_texture 需要至少提供 input_view.main_view 或 prompt 其中一个"
            )

        cos_url = self._resolve_model_file(model_path, filename=filename)
        tex_params: dict = {"algorithm_model": algorithm_model}
        if resolution is not None:
            tex_params["resolution"] = resolution
        if unwarp_uv is not None:
            tex_params["unwarp_uv"] = unwarp_uv
        if prompt is not None:
            tex_params["prompt"] = prompt

        # 上传 input_view 中的本地路径（服务端不接受本地路径，必须是 COS URL）
        resolved_view: Optional[View] = None
        if input_view is not None:
            resolved_view = View(
                main_view=self._resolve_file(input_view.main_view) if input_view.main_view else input_view.main_view,
                back_view=self._resolve_file(input_view.back_view) if input_view.back_view else None,
                left_view=self._resolve_file(input_view.left_view) if input_view.left_view else None,
                right_view=self._resolve_file(input_view.right_view) if input_view.right_view else None,
            )

        return self.api.gen_3d_model(
            name=name,
            node_type=NodeType.TEXTURE,
            params={"tex_params": tex_params},
            input_model=cos_url,
            input_view=resolved_view,
        )[0]

    # ── 4.2 骨骼架设 ─────────────────────────────────────────────────────

    def gen_rigging(
        self,
        model_path: FileInput,
        algorithm_model: str,
        mesh_category: str = "humanoid",
        name: str = "gen_rigging",
        *,
        filename: Optional[str] = None,
    ) -> str:
        """骨骼架设（node_type=5）。

        SDK 内部自动将模型文件与参数 JSON 打包成 zip 后上传，无需手动准备 zip 包。

        Args:
            model_path: 模型文件（.fbx / .obj / .glb）的本地路径、bytes 或 BinaryIO。
                        ⚠️ 此参数只接受本地文件和二进制内容，不接受 COS URL。
            algorithm_model: 骨骼架设算法模型名称，可通过
                :meth:`~visvise.api.VisviseAPI.list_algorithm_model`
                （node_type=5）获取。例如 ``"VISVISE-GoRigging-V1.0.0"``。
            mesh_category: 模型类别，``"humanoid"``（人形，默认）或 ``"tetrapod"``（四足动物）。
            name: 任务名称。
            filename: bytes/BinaryIO 输入时指定模型文件名（含扩展名，如 ``model.fbx``）。

        Returns:
            新生成的模型 ID。
        """
        # 1. 构建 JSON 参数
        import json as _json
        json_data = {
            "config": {
                "mesh_category": mesh_category,
                "algo_name": algorithm_model,
            }
        }

        # 2. 组装 zip（兼容裸模型文件和已是 zip 的输入）
        zip_bytes, zip_filename = self._build_model_zip(
            model_path, json_data=json_data, filename=filename
        )

        logger.info("gen_rigging: 上传 %s (%d bytes)", zip_filename, len(zip_bytes))

        # 3. 上传并创建任务
        cos_url = self._resolve_file(zip_bytes, filename=zip_filename)
        return self.api.gen_3d_model(
            name=name,
            node_type=NodeType.RIGGING,
            params={},
            input_model=cos_url,
        )[0]

    # ── 4.3 蒙皮生成 ─────────────────────────────────────────────────────

    def gen_skinning(
        self,
        model_path: FileInput,
        algorithm_model: str,
        mesh_names: list[str],
        joint_names: list[str],
        name: str = "gen_skinning",
        *,
        filename: Optional[str] = None,
    ) -> str:
        """蒙皮生成（node_type=6）。

        SDK 内部自动将模型文件与参数 JSON 打包成 zip 后上传，无需手动准备 zip 包。

        Args:
            model_path: 带骨骼的模型文件（.fbx / .obj / .glb）的本地路径、bytes 或 BinaryIO。
                        ⚠️ 此参数只接受本地文件和二进制内容，不接受 COS URL。
            algorithm_model: 蒙皮算法模型名称，可通过
                :meth:`~visvise.api.VisviseAPI.list_algorithm_model`
                （node_type=6）获取。例如 ``"VISVISE-GoSkinning-V1.0.0"``。
            mesh_names: 需要蒙皮的网格名称列表，如 ``["Body_Mesh", "Hair_Mesh"]``。
            joint_names: 需要蒙皮的骨骼名称列表，如 ``["Bip001", "Bip001 Pelvis", ...]``。
            name: 任务名称。
            filename: bytes/BinaryIO 输入时指定模型文件名（含扩展名，如 ``model.fbx``）。

        Returns:
            新生成的模型 ID。
        """
        # 1. 构建 JSON 参数
        import json as _json
        json_data = {
            "config": {
                "algo_name": algorithm_model,
            },
            "selection": {
                "mesh_names": mesh_names,
                "joint_names": joint_names,
            },
        }

        # 2. 组装 zip（兼容裸模型文件和已是 zip 的输入）
        zip_bytes, zip_filename = self._build_model_zip(
            model_path, json_data=json_data, filename=filename
        )

        logger.info("gen_skinning: 上传 %s (%d bytes)", zip_filename, len(zip_bytes))

        # 3. 上传并创建任务
        cos_url = self._resolve_file(zip_bytes, filename=zip_filename)
        return self.api.gen_3d_model(
            name=name,
            node_type=NodeType.SKINNING,
            params={},
            input_model=cos_url,
        )[0]

    # ── 4.4.1 视频生动画 ─────────────────────────────────────────────────

    def gen_video_motion(
        self,
        model_path: FileInput,
        video_path: FileInput,
        algorithm_model: str,
        output_model_format: str = "fbx",
        name: str = "gen_video_motion",
        *,
        model_filename: Optional[str] = None,
        video_filename: Optional[str] = None,
        with_hand: Optional[bool] = None,
        multiple_track: Optional[bool] = None,
        rotate_axis_angle: Optional[list[float]] = None,
    ) -> str:
        """视频生动画（node_type=4）。

        Args:
            model_path: 模型 zip 包，支持本地路径、VISVISE 平台 COS URL 或 bytes/BinaryIO。
            video_path: 驱动视频（非 zip），支持本地路径、VISVISE 平台 COS URL 或 bytes/BinaryIO。
            algorithm_model: 算法模型（如 ``VISVISE-FramingAI-Base-V1.5.0``）。
            output_model_format: 输出格式，默认 fbx。
            name: 任务名称。
            model_filename / video_filename: bytes/BinaryIO 时指定对应文件名。
            with_hand: 是否开启手部捕捉。
            multiple_track: 是否开启多人捕捉。
            rotate_axis_angle: 旋转轴角 [x, y, z]（弧度）。

        Returns:
            新生成的模型 ID。
        """
        model_url = self._resolve_model_file(model_path, filename=model_filename)
        video_url = self._resolve_file(video_path, filename=video_filename)

        framing: dict = {
            "algorithm_model": algorithm_model,
            "output_model_format": output_model_format,
        }
        if with_hand is not None:
            framing["with_hand"] = with_hand
        if multiple_track is not None:
            framing["multiple_track"] = multiple_track
        if rotate_axis_angle is not None:
            framing["rotate_axis_angle"] = rotate_axis_angle

        return self.api.gen_3d_model(
            name=name,
            node_type=NodeType.ANIMATION,
            params={"framing_ai_params": framing},
            input_model=model_url,
            input_video=video_url,
        )[0]

    # ── 4.4.2 文本生动画 ─────────────────────────────────────────────────

    def gen_text_motion(
        self,
        model_path: FileInput,
        prompt: str,
        algorithm_model: str,
        output_model_format: str = "fbx",
        name: str = "gen_text_motion",
        *,
        filename: Optional[str] = None,
    ) -> list[str]:
        """文本生动画（node_type=4）。

        一次生成 4 个动画模型供抽卡选择。

        Args:
            model_path: 模型 zip 包，支持本地路径、VISVISE 平台 COS URL 或 bytes/BinaryIO。
            prompt: 动画提示词（如 "一个人在跳街舞"）。
            algorithm_model: 文生动画模型（如 ``VISVISE-TextMotion-V1.1.0``）。
            output_model_format: 输出格式，默认 fbx。
            name: 任务名称。
            filename: bytes/BinaryIO 时指定文件名。

        Returns:
            4 个新生成的模型 ID 列表（用于抽卡）。
        """
        model_url = self._resolve_model_file(model_path, filename=filename)
        return self.api.gen_3d_model(
            name=name,
            node_type=NodeType.ANIMATION,
            params={"framing_ai_params": {
                "algorithm_model": algorithm_model,
                "output_model_format": output_model_format,
                "prompt": prompt,
            }},
            input_model=model_url,
        )

    # ── 4.5 图生 Pose ─────────────────────────────────────────────────────

    def gen_pose(
        self,
        model_path: FileInput,
        input_images: list[FileInput],
        algorithm_model: str,
        output_model_format: str = "fbx",
        name: str = "gen_pose",
        *,
        model_filename: Optional[str] = None,
        image_filenames: Optional[list[Optional[str]]] = None,
    ) -> list[str]:
        """批量图生 Pose（最多 10 张图片）。

        Args:
            model_path: FBX 模型 zip 包，支持本地路径、VISVISE 平台 COS URL 或 bytes/BinaryIO。
            input_images: 参考图片列表（1~10 个），每个元素支持本地路径、VISVISE 平台 COS URL 或 bytes/BinaryIO。
            algorithm_model: 算法模型（如 ``VISVISE-PosingAI-V1.0.0``）。
            output_model_format: 输出格式，默认 fbx。
            name: 任务名称。
            model_filename: model_path 为 bytes/BinaryIO 时指定文件名。
            image_filenames: 与 input_images 一一对应的文件名列表，元素可为 None。

        Returns:
            新生成的模型 ID 列表。
        """
        model_url = self._resolve_model_file(model_path, filename=model_filename)
        _fnames = image_filenames or [None] * len(input_images)
        uploaded_images = [
            self._resolve_file(img, filename=fname)
            for img, fname in zip(input_images, _fnames)
        ]
        return self.api.batch_gen_pose(
            name=name,
            input_model=model_url,
            input_images=uploaded_images,
            params={
                "algorithm_model": algorithm_model,
                "output_model_format": output_model_format,
            },
        )

