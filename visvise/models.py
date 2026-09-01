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
    SEGMENT_2D = 14       # 2D 拆分
    AUTO_LUV = 15         # 2UV（重生成 regenerate_model）
    PREPROCESS_2D = 16    # 2D 预处理


class PreprocessType:
    """2D 预处理类型枚举 (preprocess_type)。"""
    STYLIZED = 1          # 风格化
    PATTERNED = 2         # 去花纹


class StyleType:
    """原画风格化类型枚举 (style_type)。"""
    GRAYSCALE = 1         # 灰模风
    PIXEL = 2             # 像素风
    REALISTIC = 3         # 写实风
    CARTOON = 4           # 卡通手办风


class ModelStatus:
    """模型资产状态码"""
    INVALID = 0     # 无效
    PENDING = 1     # 等待生成
    RUNNING = 2     # 生成中
    SUCCESS = 3     # 生成成功
    FAILED = 4      # 生成失败


class FaceType:
    """面数类型枚举 (face_type)"""
    TRIANGLE = 1    # 三角面
    QUAD = 2        # 四边面


class DetailLevel:
    """精细程度枚举 (detail_level)，用于重拓扑"""
    LOW = 1         # 低
    MEDIUM = 2      # 中
    HIGH = 3        # 高


class OutputModelFormat:
    """输出模型格式枚举 (output_model_format)"""
    FBX = "fbx"
    OBJ = "obj"
    GLB = "glb"


class MeshRefineMode:
    """布线优化模式枚举 (mode)"""
    OPTIMIZE = 1    # 布线优化
    DENSIFY = 2     # 布线加密


class SegmentSplitType:
    """2D 拆分方式枚举 (split_type)"""
    FRONT_VIEW = 1  # 生成正视图拆分（默认）
    FOUR_VIEW = 2   # 生成四视图拆分


class SegmentGranularity:
    """2D 拆分颗粒度枚举 (granularity)"""
    COARSE = 1      # 粗（×50%）
    MEDIUM = 2      # 中（×70%，默认）
    FINE = 3        # 细（×100%）


class SegmentViewType:
    """2D 拆分重新编辑的视图类型枚举 (view_type)"""
    MAIN = 0        # 主视图（front，默认）
    LEFT = 1        # 左视图
    RIGHT = 2       # 右视图
    BACK = 3        # 背视图


class ImageGen360Style:
    """图生 360 风格枚举 (style)。

    仅 VISVISE 自研模型支持；服务端只接受以下固定值，传其它自定义值会被服务端拒绝。
    不传则不做风格转换。
    """
    GRAY_MODEL = "灰模"
    PHOTOREAL = "超写实"
    Q_TOON = "Q版卡通"
    PIXEL = "像素风格"

    @classmethod
    def values(cls) -> tuple[str, ...]:
        return (cls.GRAY_MODEL, cls.PHOTOREAL, cls.Q_TOON, cls.PIXEL)


# ──────────────────────────────────────────────
# 公共请求结构
# ──────────────────────────────────────────────

@dataclass
class View:
    """多视图结构（与 proto ``View`` 9 字段一一对应）"""
    main_view: str
    back_view: Optional[str] = None
    left_view: Optional[str] = None
    right_view: Optional[str] = None
    top_view: Optional[str] = None
    bottom_view: Optional[str] = None
    front_view: Optional[str] = None
    front_left_view: Optional[str] = None
    front_right_view: Optional[str] = None

    def to_dict(self) -> dict:
        d: dict = {"main_view": self.main_view}
        for key in (
            "back_view",
            "left_view",
            "right_view",
            "top_view",
            "bottom_view",
            "front_view",
            "front_left_view",
            "front_right_view",
        ):
            val = getattr(self, key)
            if val:
                d[key] = val
        return d


@dataclass
class StyleParam:
    """风格化结果参数，用于保存 2D 预处理资产。"""
    style_type: int
    result_image: str

    def to_dict(self) -> dict:
        return {
            "style_type": self.style_type,
            "result_image": self.result_image,
        }


@dataclass
class RemovePatternParam:
    """去花纹结果参数，用于保存 2D 预处理资产。"""
    result_image: str

    def to_dict(self) -> dict:
        return {"result_image": self.result_image}


@dataclass
class ReduceFace:
    """LOD 单级减面配置"""
    reduce_level: int
    reduce_percent: int
    face_type: int  # 1:三角面 2:四边面
    face_num: Optional[int] = None          # 保面面数
    face_tab: Optional[int] = None          # 保面Tab切换, 0-按比例, 1-按面数

    def to_dict(self) -> dict:
        d: dict = {
            "reduce_level": self.reduce_level,
            "reduce_percent": self.reduce_percent,
            "face_type": self.face_type,
        }
        if self.face_num is not None:
            d["face_num"] = self.face_num
        if self.face_tab is not None:
            d["face_tab"] = self.face_tab
        return d


@dataclass
class MotionSegment:
    """文生动画时间轴动作段（多段提示词 segments 的单个元素）。

    与 API 文档中的 ``MotionSegment`` 结构一一对应：

    * ``text``：该段动作描述（必填）。
    * ``num_frames`` / ``duration``：该段时长，二者必须传一个（二选一，
      同时提供时以 ``num_frames`` 为准）。
    * ``overlap_frames_with_prev`` / ``overlap_duration_with_prev``：
      与上一段之间的过渡（第 1 段无需传）。

    ``index``（段序号）为服务端内部字段，由服务端按数组顺序生成，SDK 不暴露。
    """
    text: str
    num_frames: Optional[int] = None
    duration: Optional[float] = None
    overlap_frames_with_prev: Optional[int] = None
    overlap_duration_with_prev: Optional[float] = None

    def to_dict(self) -> dict:
        d: dict = {"text": self.text}
        if self.num_frames is not None:
            d["num_frames"] = self.num_frames
        if self.duration is not None:
            d["duration"] = self.duration
        if self.overlap_frames_with_prev is not None:
            d["overlap_frames_with_prev"] = self.overlap_frames_with_prev
        if self.overlap_duration_with_prev is not None:
            d["overlap_duration_with_prev"] = self.overlap_duration_with_prev
        return d


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
    model_quota: int
    animation_quota: int
    server_ts: int
    image_processing_quota: int = 0

    @classmethod
    def from_dict(cls, d: dict) -> "UserQuota":
        return cls(
            model_quota=d["model_quota"],
            animation_quota=d["animation_quota"],
            server_ts=d["server_ts"],
            image_processing_quota=d.get("image_processing_quota", 0),
        )


@dataclass
class FailedReason:
    """生成失败原因"""
    code: int
    reason: str
    real_reason: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "FailedReason":
        return cls(
            code=d.get("code", -1),
            reason=d.get("reason", ""),
            real_reason=d.get("real_reason", ""),
        )


@dataclass
class FeedbackItem:
    """单条反馈"""
    result_index: int = 0      # 结果索引，普通节点为 1，文生动画节点为 1~4
    feedback_type: int = 0     # 反馈类型：0=未反馈，1=满意，2=不满意
    tags: list[str] = field(default_factory=list)  # 问题标签列表
    content: str = ""          # 反馈文字描述

    @classmethod
    def from_dict(cls, d: dict) -> "FeedbackItem":
        return cls(
            result_index=d.get("result_index", 0),
            feedback_type=d.get("feedback_type", 0),
            tags=d.get("tags", []),
            content=d.get("content", ""),
        )


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
    del_times: int = 0
    del_card_indexs: list[int] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "LODOutput":
        return cls(
            lod_files=[LODFile.from_dict(f) for f in d.get("lod_files", [])],
            zip_file=d.get("zip_file", ""),
            del_times=d.get("del_times", 0),
            del_card_indexs=d.get("del_card_indexs", []),
        )


@dataclass
class ImageGen360Output:
    """图生360 输出结果"""
    output_view: Optional[View] = None
    horizontal_view_video: str = ""
    vertical_view_video: str = ""
    horizontal_view_video_frames: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "ImageGen360Output":
        ov = d.get("output_view")
        return cls(
            output_view=View(**{k: v for k, v in ov.items() if v}) if ov else None,
            horizontal_view_video=d.get("horizontal_view_video", ""),
            vertical_view_video=d.get("vertical_view_video", ""),
            horizontal_view_video_frames=d.get("horizontal_view_video_frames", ""),
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
    rewrite_prompts: list[str] = field(default_factory=list)
    rewrite_applied: bool = False

    @classmethod
    def from_dict(cls, d: dict) -> "FramingAIOutput":
        return cls(
            text2_motion_result=[
                Text2Motion.from_dict(m) for m in d.get("text2_motion_result", [])
            ],
            rewrite_prompts=d.get("rewrite_prompts", []),
            rewrite_applied=d.get("rewrite_applied", False),
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
    parent_model_id: str = ""           # 父模型ID
    works_id: str = ""                  # 作品ID
    preview_model: str = ""             # 预览用的模型
    feedbacks: list[FeedbackItem] = field(default_factory=list)  # 反馈详情列表
    model_type: int = 0                 # 模型类型（Model3DType）
    rewrite_prompts: list[str] = field(default_factory=list)  # Rewrite 改写后的各段文本

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
            parent_model_id=d.get("parent_model_id", ""),
            works_id=d.get("works_id", ""),
            preview_model=d.get("preview_model", ""),
            feedbacks=[FeedbackItem.from_dict(f) for f in d.get("feedbacks", [])],
            model_type=d.get("model_type", 0),
            rewrite_prompts=d.get("rewrite_prompts", []),
        )
