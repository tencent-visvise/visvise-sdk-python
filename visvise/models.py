"""
VISVISE Weaver SDK - 数据模型（dataclass）

与 API 文档中的数据结构一一对应。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ──────────────────────────────────────────────
# 枚举常量
# ──────────────────────────────────────────────

class NodeType:
    """节点类型枚举 (node_type)"""
    RE_TOPOLOGY = 1       # 重拓扑
    LOD = 2               # LOD
    IMG_TO_3D_HIGH = 3    # 图生3D（高模）
    ANIMATION = 4         # Framing AI 动画生成
    RIGGING = 5           # 骨骼架设
    SKINNING = 6          # 蒙皮
    IMG_TO_360 = 7        # 图生360
    TEXTURE = 8           # 贴图纹理
    UV = 9                # UV 展开
    MESH_REFINE = 10      # 布线优化
    IMG_TO_3D_MID = 11    # 图生3D（中模）
    IMG_TO_POSE = 12      # 图生 Pose
    IMG_TO_3D_LOW = 13    # 图生3D（低模）


class ModelStatus:
    """模型资产状态码"""
    INVALID = 0     # 无效
    PENDING = 1     # 等待生成
    RUNNING = 2     # 生成中
    SUCCESS = 3     # 生成成功
    FAILED = 4      # 生成失败


# ──────────────────────────────────────────────
# 公共请求结构
# ──────────────────────────────────────────────

@dataclass
class View:
    """多视图结构"""
    main_view: str
    back_view: Optional[str] = None
    left_view: Optional[str] = None
    right_view: Optional[str] = None

    def to_dict(self) -> dict:
        d: dict = {"main_view": self.main_view}
        if self.back_view:
            d["back_view"] = self.back_view
        if self.left_view:
            d["left_view"] = self.left_view
        if self.right_view:
            d["right_view"] = self.right_view
        return d


@dataclass
class ReduceFace:
    """LOD 单级减面配置"""
    reduce_level: int
    reduce_percent: int
    face_type: int  # 1:三角面 2:四边面

    def to_dict(self) -> dict:
        return {
            "reduce_level": self.reduce_level,
            "reduce_percent": self.reduce_percent,
            "face_type": self.face_type,
        }


# ──────────────────────────────────────────────
# 响应数据结构
# ──────────────────────────────────────────────

@dataclass
class CosCred:
    """COS 临时凭证"""
    tmp_secret_id: str
    tmp_secret_key: str
    session_token: str


@dataclass
class GetCosCredResult:
    """get_cos_cred 接口响应"""
    cred: CosCred
    start_time: int
    expired_time: int
    bucket: str
    region: str
    path_prefix: str

    @classmethod
    def from_dict(cls, d: dict) -> "GetCosCredResult":
        cred_d = d["cred"]
        return cls(
            cred=CosCred(
                tmp_secret_id=cred_d["tmp_secret_id"],
                tmp_secret_key=cred_d["tmp_secret_key"],
                session_token=cred_d["session_token"],
            ),
            start_time=d["start_time"],
            expired_time=d["expired_time"],
            bucket=d["bucket"],
            region=d["region"],
            path_prefix=d["path_prefix"],
        )


@dataclass
class UserQuota:
    """get_user_quota 接口响应"""
    quota: int
    server_ts: int

    @classmethod
    def from_dict(cls, d: dict) -> "UserQuota":
        return cls(quota=d["quota"], server_ts=d["server_ts"])


@dataclass
class FailedReason:
    """生成失败原因"""
    code: int
    reason: str

    @classmethod
    def from_dict(cls, d: dict) -> "FailedReason":
        return cls(code=d.get("code", -1), reason=d.get("reason", ""))


@dataclass
class LODFile:
    """单个 LOD 级别输出"""
    reduce_level: int
    download_url: str
    preview_img: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "LODFile":
        return cls(
            reduce_level=d.get("reduce_level", 0),
            download_url=d.get("download_url", ""),
            preview_img=d.get("preview_img", ""),
        )


@dataclass
class LODOutput:
    """LOD 输出文件集合"""
    lod_files: list[LODFile] = field(default_factory=list)
    zip_file: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "LODOutput":
        return cls(
            lod_files=[LODFile.from_dict(f) for f in d.get("lod_files", [])],
            zip_file=d.get("zip_file", ""),
        )


@dataclass
class ImageGen360Output:
    """图生360 输出结果"""
    output_view: Optional[View] = None
    horizontal_view_video: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "ImageGen360Output":
        ov = d.get("output_view")
        return cls(
            output_view=View(**{k: v for k, v in ov.items() if v}) if ov else None,
            horizontal_view_video=d.get("horizontal_view_video", ""),
        )


@dataclass
class Text2Motion:
    """文生动画单条输出"""
    output_model: str = ""
    preview_img: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "Text2Motion":
        return cls(
            output_model=d.get("output_model", ""),
            preview_img=d.get("preview_img", ""),
        )


@dataclass
class FramingAIOutput:
    """Framing AI 的输出结果"""
    text2_motion_result: list[Text2Motion] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "FramingAIOutput":
        return cls(
            text2_motion_result=[
                Text2Motion.from_dict(m) for m in d.get("text2_motion_result", [])
            ],
        )


@dataclass
class ModelInfo:
    """模型资产信息（拉取模型资产列表响应）"""
    model_id: str
    name: str
    status: int
    node_type: int
    create_ts: int = 0
    create_user: str = ""
    preview_img: str = ""
    output_model: str = ""
    input_model: str = ""
    input_video: str = ""
    time_cost: int = 0
    remaining_time: int = 0
    wait_time: int = 0
    failed_reason: Optional[FailedReason] = None
    lod_output: Optional[LODOutput] = None
    image_gen_360_output: Optional[ImageGen360Output] = None
    framing_ai_output: Optional[FramingAIOutput] = None
    params: Optional[dict] = None       # 原始生成参数（TemplateParams）
    input_view: Optional[dict] = None   # 原始输入视图
    algorithm_model: str = ""           # 使用的算法模型名

    @property
    def is_success(self) -> bool:
        return self.status == ModelStatus.SUCCESS

    @property
    def is_failed(self) -> bool:
        return self.status == ModelStatus.FAILED

    @property
    def is_pending(self) -> bool:
        return self.status in (ModelStatus.PENDING, ModelStatus.RUNNING)

    @classmethod
    def from_dict(cls, d: dict) -> "ModelInfo":
        fr = d.get("failed_reason")
        lod = d.get("lod_output")
        i360 = d.get("image_gen_360_output")
        fai = d.get("framing_ai_output")
        return cls(
            model_id=d.get("model_id", ""),
            name=d.get("name", ""),
            status=d.get("status", 0),
            node_type=d.get("node_type", 0),
            create_ts=d.get("create_ts", 0),
            create_user=d.get("create_user", ""),
            preview_img=d.get("preview_img", ""),
            output_model=d.get("output_model", ""),
            input_model=d.get("input_model", ""),
            input_video=d.get("input_video", ""),
            time_cost=d.get("time_cost", 0),
            remaining_time=d.get("remaining_time", 0),
            wait_time=d.get("wait_time", 0),
            failed_reason=FailedReason.from_dict(fr) if fr else None,
            lod_output=LODOutput.from_dict(lod) if lod else None,
            image_gen_360_output=ImageGen360Output.from_dict(i360) if i360 else None,
            framing_ai_output=FramingAIOutput.from_dict(fai) if fai else None,
            params=d.get("params"),
            input_view=d.get("input_view"),
            algorithm_model=d.get("algorithm_model", ""),
        )
