# VISVISE Weaver Python SDK

**中文** | [English](README_EN.md)

VISVISE Weaver OpenAPI 的 Python SDK，提供：

- 全部原子 API 方法（逐一对应 OpenAPI 接口）
- 各节点类型的高阶 `gen_xxx()` 方法（自动上传文件 + 创建任务）
- `wait_model()` 异步轮询方法

---

## 目录

- [安装](#安装)
- [快速开始](#快速开始)
- [客户端初始化](#客户端初始化)
- [枚举常量](#枚举常量)
- [高阶方法参考](#高阶方法参考)
  - [gen_360 — 图生360](#gen_360--图生360)
  - [gen_high_model — 图生高模](#gen_high_model--图生高模)
  - [gen_mid_model — 图生中模](#gen_mid_model--图生中模)
  - [gen_low_model — 图生低模](#gen_low_model--图生低模)
  - [gen_mesh_refine — 重布线](#gen_mesh_refine--重布线)
  - [gen_retopology — 重拓扑](#gen_retopology--重拓扑)
  - [gen_lod — LOD](#gen_lod--lod)
  - [gen_uv — UV展开](#gen_uv--uv展开)
  - [gen_texture — 贴图纹理](#gen_texture--贴图纹理)
  - [gen_rigging — 骨骼架设](#gen_rigging--骨骼架设)
  - [gen_skinning — 蒙皮生成](#gen_skinning--蒙皮生成)
  - [gen_video_motion — 视频生动画](#gen_video_motion--视频生动画)
  - [gen_text_motion — 文本生动画](#gen_text_motion--文本生动画)
  - [gen_pose — 图生Pose](#gen_pose--图生pose)
  - [gen_segment_2d — 2D 拆分](#gen_segment_2d--2d-拆分)
  - [wait_model — 等待完成](#wait_model--等待完成)
- [原子 API 方法参考](#原子-api-方法参考)
- [异常说明](#异常说明)
- [完整流程示例](#完整流程示例)

---

## 安装

直接从 GitHub 仓库安装（包含 COS 上传依赖）：

```bash
pip install git+https://github.com/tencent-visvise/visvise-sdk-python.git@v1.1.1
```

或通过 SSH：

```bash
pip install git+ssh://git@github.com/tencent-visvise/visvise-sdk-python.git@v1.1.1
```

> **注：** 安装后即包含腾讯云 COS SDK，可直接使用本地文件自动上传功能，无需额外安装。

---

## 快速开始

```python
from visvise import VisviseClient, FaceType, OutputModelFormat

client = VisviseClient(
    app_id="your_app_id",
    secret_key="your_secret_key",
)

# ① 图生360：上传本地图片，生成多视图
mv_model_id = client.gen_360(
    main_view="character.png",          # 本地文件路径，SDK 自动上传
    name="my_360",
    rtx="caller_rtx",
)

# ② 等待图生360完成，获取多视图输出
mv_info = client.wait_model(mv_model_id, interval=3, timeout=300, rtx="caller_rtx")
output_view = mv_info.image_gen_360_output.output_view

# ③ 图生高模（多视图输出的 COS URL 直接传入）
high_model_id = client.gen_high_model(
    main_view=output_view.main_view,
    back_view=output_view.back_view,
    left_view=output_view.left_view,
    right_view=output_view.right_view,
    output_model_format=OutputModelFormat.FBX,
    face_type=FaceType.TRIANGLE,
    face_num=500000,
    rtx="caller_rtx",
)

# ④ 等待高模完成
model_info = client.wait_model(high_model_id, timeout=900, rtx="caller_rtx")
print("输出模型：", model_info.output_model)
```

---

## 客户端初始化

```python
from visvise import VisviseClient, Environment

client = VisviseClient(
    app_id="your_app_id",       # 必填，由平台分配
    secret_key="your_key",      # 必填，由平台分配
    env=Environment.PROD,       # 可选，默认生产环境
    timeout=30,                 # 可选，单次请求超时（秒），默认 30
)
```

| 参数 | 必填 | 说明 |
|---|---|---|
| `app_id` | ✅ | 由平台分配的客户端标识 |
| `secret_key` | ✅ | 由平台分配的签名密钥 |
| `env` | — | 环境：`Environment.PROD`（默认）/ `Environment.TEST` / `Environment.DEV` 或自定义 URL |
| `timeout` | — | 单次 HTTP 请求超时（秒），默认 30 |

> **关于 `rtx` 参数**：每次接口调用都需在方法参数中传入 `rtx`（实际使用人的 RTX 公司账号），它不在 client 构造函数中绑定。
> 按公司要求，**内部用户必须传入实际使用人的 rtx**，不可使用项目账号或共享账号代填；外部用户可传业务标识。

---

## 枚举常量

SDK 提供以下枚举常量，推荐使用枚举替代硬编码数字/字符串：

```python
from visvise import (
    FaceType, DetailLevel, OutputModelFormat, MeshRefineMode,
    SegmentSplitType, SegmentGranularity, ImageGen360Style,
)

# 面数类型
FaceType.TRIANGLE  # 1 - 三角面
FaceType.QUAD      # 2 - 四边面

# 精细程度（重拓扑）
DetailLevel.LOW    # 1 - 低
DetailLevel.MEDIUM # 2 - 中
DetailLevel.HIGH   # 3 - 高

# 输出模型格式
OutputModelFormat.FBX  # "fbx"
OutputModelFormat.OBJ  # "obj"
OutputModelFormat.GLB  # "glb"

# 布线优化模式
MeshRefineMode.OPTIMIZE  # 1 - 布线优化
MeshRefineMode.DENSIFY   # 2 - 布线加密

# 2D 拆分方式
SegmentSplitType.FRONT_VIEW  # 1 - 生成正视图拆分（默认）
SegmentSplitType.FOUR_VIEW   # 2 - 生成四视图拆分

# 2D 拆分颗粒度
SegmentGranularity.COARSE   # 1 - 粗
SegmentGranularity.MEDIUM   # 2 - 中（默认）
SegmentGranularity.FINE     # 3 - 细

# 图生 360 风格（仅 VISVISE 自研模型支持，传其它值会被服务端拒绝）
ImageGen360Style.GRAY_MODEL  # "灰模"
ImageGen360Style.PHOTOREAL   # "超写实"
ImageGen360Style.Q_TOON      # "Q版卡通"
ImageGen360Style.PIXEL       # "像素风格"
```

---

## 高阶方法参考

高阶方法封装了「COS 文件上传 + 创建异步任务」两步，传入文件路径（本地）或 COS URL 均可，返回 `model_id`。

> **关于 `algorithm_model` 参数：** 所有 gen_xxx 方法的 `algorithm_model` 参数均为可选。若不传，SDK 将自动调用 `list_algorithm_model` 获取当前账号可用的第一个算法模型。

> **关于文件输入：** 所有文件类参数（如 `main_view` / `model_path` / `video_path` / `input_images` 等）统一支持三种形式：
> - **本地路径**（`str`）：直接传文件路径，SDK 自动上传。
> - **VISVISE 平台 COS URL**（`str`）：传入 `https://...myqcloud.com/...` 形式的链接，SDK 不再上传。
> - **二进制内容**（`bytes` / `BinaryIO`）：SDK 自动通过 magic bytes 识别格式（图片 PNG/JPEG/GIF/BMP/WebP/TIFF、3D 模型 FBX/OBJ/GLB/GLTF、视频 MP4/MOV/WebM/AVI、ZIP），用 `<uuid>.<识别后缀>` 自动命名上传，无需用户提供文件名。

以下示例统一使用如下 import：

```python
from visvise import (
    VisviseClient, Environment,
    FaceType, DetailLevel, OutputModelFormat, MeshRefineMode,
    SegmentSplitType, SegmentGranularity,
    ReduceFace, View,
)

client = VisviseClient(app_id="...", secret_key="...")
```

### gen_360 — 图生360

从单张图片生成 360 度多视图。 → [示例代码](examples/gen_360.py)

```python
model_id = client.gen_360(
    main_view="path/to/character.png",   # 必填，主视图（本地路径或 VISVISE 平台 COS URL）
    algorithm_model=None,                # 可选，算法模型名（如 "hunyuan3D-MultiView-v3.0"）；不传则自动选首个可用模型
    name="gen_360",                      # 可选，任务名称
    enable_a_pose=None,                  # 可选，是否开启 A-Pose（True/False）
    style=None,                          # 可选，风格类型（仅 VISVISE 自研模型支持），只接受 ImageGen360Style 枚举：GRAY_MODEL/PHOTOREAL/Q_TOON/PIXEL，传其他值会报错
    back_view=None,                      # 可选，背视图，提升生成质量
    left_view=None,                      # 可选，左视图
    right_view=None,                     # 可选，右视图,
    rtx="caller_rtx",
)
```

---

### gen_high_model — 图生高模

从图片/多视图生成高精度 3D 模型（node_type=3）。 → [示例代码](examples/gen_high_model.py)

```python
model_id = client.gen_high_model(
    main_view="path/to/main.png",                 # 必填，主视图
    algorithm_model=None,                          # 可选，如 "hunyuan3D-v3.1"；不传则自动选首个可用模型
    output_model_format=OutputModelFormat.FBX,    # 可选，输出格式（默认 fbx）
    face_type=FaceType.TRIANGLE,                  # 可选，面数类型（默认三角面）
    name="gen_high_model",                         # 可选，任务名称
    face_num=None,                                 # 可选，目标面数（1000~1500000），不传则自动配置
    back_view=None,                                # 可选，背视图，提升质量
    left_view=None,                                # 可选，左视图
    right_view=None,                               # 可选，右视图,
    rtx="caller_rtx",
)
```

---

### gen_mid_model — 图生中模

中模要求四视图全部必传（node_type=11）。 → [示例代码](examples/gen_mid_model.py)

```python
model_id = client.gen_mid_model(
    main_view="path/to/main.png",                 # 必填，若是用户上传原画视图，则必填
    back_view="path/to/back.png",                 # 可选
    left_view="path/to/left.png",                 # 可选
    right_view="path/to/right.png",               # 可选
    algorithm_model=None,                         # 可选，如 "VISVISE-MeshGen-V1.0.0"；不传则自动选首个可用模型
    output_model_format=OutputModelFormat.FBX,    # 可选，输出格式（默认 fbx）
    face_type=FaceType.TRIANGLE,                  # 可选，面数类型
    name="gen_mid_model",                         # 可选，任务名称
    segment_model_id=None,                        # 可选，2D 分割资产 ID（仅中模有效），用于基于2D分割结果生成
    model_id_360=None,                                # 可选，图生360资产 ID，用于基于图生360结果生成
    rtx="caller_rtx",
)
```

---

### gen_low_model — 图生低模

低模只需主视图（node_type=13）。 → [示例代码](examples/gen_low_model.py)

```python
model_id = client.gen_low_model(
    main_view="path/to/main.png",                 # 必填，主视图
    algorithm_model=None,                          # 可选，如 "Tripo-v1.0-快速生成"
    output_model_format=OutputModelFormat.FBX,    # 可选，输出格式
    face_type=FaceType.TRIANGLE,                  # 可选，面数类型
    name="gen_low_model",                          # 可选，任务名称
    back_view=None,                                # 可选，背视图
    left_view=None,                                # 可选，左视图
    right_view=None,                               # 可选，右视图,
    rtx="caller_rtx",
)
```

---

### gen_mesh_refine — 重布线

对模型进行布线优化（node_type=10）。 → [示例代码](examples/gen_mesh_refine.py)

```python
model_id = client.gen_mesh_refine(
    model_path="path/to/model.fbx",               # 必填，输入模型（裸模型 SDK 自动打 zip）
    algorithm_model=None,                          # 可选，如 "VISVISE-MeshRefine-V1.0.0"
    input_model_format=OutputModelFormat.FBX,                     # 可选，输入模型格式（默认 fbx）
    name="gen_mesh_refine",                        # 可选，任务名称
    mode=None,                                     # 可选，MeshRefineMode.OPTIMIZE(1, 默认) / DENSIFY(2)
    color_model=None,                              # 可选，带颜色的模型，用于为输出附加颜色,
    rtx="caller_rtx",
)
```

---

### gen_retopology — 重拓扑

对高面数模型进行拓扑优化（node_type=1）。 → [示例代码](examples/gen_retopology.py)

> 注意：混元模型传 `detail_level`，VISVISE 自研模型传 `face_num`，二选一。

```python
model_id = client.gen_retopology(
    model_path="path/to/model.fbx",               # 必填，输入模型
    algorithm_model=None,                          # 可选，如 "hunyuan3D-RTP-v1.5" / "VISVISE-RTP-V1.0.0"
    output_model_format=OutputModelFormat.FBX,    # 可选，输出格式
    face_type=FaceType.QUAD,                      # 可选，面数类型（默认四边面）
    name="gen_retopology",                         # 可选，任务名称
    detail_level=DetailLevel.HIGH,                # 可选，混元模型必传：DetailLevel.LOW/MEDIUM/HIGH
    face_num=None,                                 # 可选，VISVISE 自研模型必传：指定输出面数,
    rtx="caller_rtx",
)
```

---

### gen_lod — LOD

生成多级细节模型（node_type=2），支持抽卡。 → [示例代码](examples/gen_lod.py)

```python
model_ids = client.gen_lod(
    model_path="path/to/model.fbx",               # 必填，输入模型
    reduce_faces=[                                 # 必填，减面配置列表
        ReduceFace(reduce_level=1, reduce_percent=50, face_type=FaceType.QUAD),
        ReduceFace(reduce_level=2, reduce_percent=25, face_type=FaceType.QUAD),
    ],
    algorithm_model=None,                          # 可选，如 "VISVISE-LOD-V1.0.0"
    output_model_format=OutputModelFormat.FBX,    # 可选，输出格式
    name="gen_lod",                                # 可选，任务名称
    gen_times=3,                                   # 可选，生成次数（抽卡），不需要抽卡传 1,
    rtx="caller_rtx",
)
```

---

### gen_uv — UV展开

自动 UV 展开（node_type=9）。 → [示例代码](examples/gen_uv.py)

```python
model_id = client.gen_uv(
    model_path="path/to/model.fbx",               # 必填，输入模型
    algorithm_model=None,                          # 可选，如 "hunyuan3D-UV-v2.0"
    name="gen_uv",                                 # 可选，任务名称
    enable_auto_smoothing=None,                    # 可选，是否启用自动平滑,
    rtx="caller_rtx",
)
```

---

### gen_texture — 贴图纹理

为模型生成贴图纹理（node_type=8）。 → [示例代码](examples/gen_texture.py)

> `input_view.main_view` 与 `prompt` 至少传一个，可同时传入。

```python
model_id = client.gen_texture(
    model_path="path/to/model.fbx",               # 必填，输入模型
    algorithm_model=None,                          # 可选，如 "hunyuan3D-TEX-v2.0"
    name="gen_texture",                            # 可选，任务名称
    input_view=View(main_view="path/to/ref.png"), # 可选，原画视图（与 prompt 至少传一个）
    resolution=None,                               # 可选，分辨率（如 1024 / 2048）
    unwarp_uv=None,                                # 可选，是否同时展开 UV
    prompt=None,                                   # 可选，贴图文本提示词,
    rtx="caller_rtx",
)
```

---

### gen_rigging — 骨骼架设

自动为模型生成骨骼（node_type=5）。SDK 自动将模型文件与参数 JSON 打包成 zip 上传，无需手动准备 zip 包。 → [示例代码](examples/gen_rigging.py)

```python
model_id = client.gen_rigging(
    model_path="path/to/model.fbx",               # 必填，裸模型文件即可，SDK 自动打包
    algorithm_model=None,                          # 可选，如 "VISVISE-GoRigging-V1.0.0"
    mesh_category="humanoid",                     # 可选，"humanoid"（人形，默认）或 "tetrapod"（四足）
    name="gen_rigging",                            # 可选，任务名称
    template_skeleton=None,                        # 可选，模板骨骼，传入后将基于该模板进行架设
    mesh_names=None,                               # 可选，需要骨骼架设的网格名称列表
    generate_root=False,                           # 可选，是否生成 root 骨骼（默认 False）
    temperature=-1,                                # 可选，高级采样-自由度，取值范围 0~1（默认 -1）
    num_beams=-1,                                  # 可选，高级采样-搜索广度，取值范围 5~15（默认 -1）
    algo_scenario=None,                            # 可选，生成方式（仅 mesh_category=humanoid 时有效）：
                                                   #   1 = 默认一键自动生成
                                                   #   2 = 人形角色+上传模版（需同时传 template_skeleton）
                                                   #   3 = 主体骨骼人形角色生成附加骨骼
    rtx="caller_rtx",
)
```

---

### gen_skinning — 蒙皮生成

自动绑定蒙皮权重（node_type=6）。SDK 自动将模型文件与参数 JSON 打包成 zip 上传。 → [示例代码](examples/gen_skinning.py)

```python
model_id = client.gen_skinning(
    model_path="path/to/rigged_model.fbx",        # 必填，带骨骼的模型文件
    mesh_names=["Body_Mesh", "Hair_Mesh"],         # 必填，需要蒙皮的网格名称列表
    joint_names=["Bip001", "Bip001 Pelvis"],       # 必填，需要蒙皮的骨骼名称列表
    algorithm_model=None,                          # 可选，如 "VISVISE-GoSkinning-V1.0.0"
    name="gen_skinning",                           # 可选，任务名称,
    rtx="caller_rtx",
)
```

---

### gen_video_motion — 视频生动画

从视频中提取动作驱动 3D 模型（node_type=4）。 → [示例代码](examples/gen_video_motion.py)

```python
model_id = client.gen_video_motion(
    model_path="path/to/model.zip",               # 必填，模型 zip 包
    video_path="path/to/dance.mp4",               # 必填，驱动视频
    algorithm_model=None,                          # 可选，如 "VISVISE-FramingAI-Base-V1.5.0"
    output_model_format=OutputModelFormat.FBX,    # 可选，输出格式
    name="gen_video_motion",                       # 可选，任务名称
    with_hand=None,                                # 可选，是否开启手部捕捉
    multiple_track=None,                           # 可选，是否开启多人捕捉
    rotate_axis_angle=None,                        # 可选，旋转轴角 [x, y, z]（弧度）,
    rtx="caller_rtx",
)
```

---

### gen_text_motion — 文本生动画

通过提示词生成动画，一次返回 4 个模型供抽卡（node_type=4）。 → [示例代码](examples/gen_text_motion.py)

```python
model_ids = client.gen_text_motion(
    model_path="path/to/model.zip",               # 必填，模型 zip 包
    prompt="一个人在跳街舞",                        # 必填，动画提示词
    algorithm_model=None,                          # 可选，如 "VISVISE-TextMotion-V1.1.0"
    output_model_format=OutputModelFormat.FBX,    # 可选，输出格式
    name="gen_text_motion",                        # 可选，任务名称,
    rtx="caller_rtx",
)
# model_ids 包含 4 个 ID，等待其中你需要的那个即可
```

---

### gen_pose — 图生Pose

从参考图生成 Pose 模型（最多 10 张图片）。 → [示例代码](examples/gen_pose.py)

```python
model_ids = client.gen_pose(
    model_path="path/to/model.zip",               # 必填，FBX 模型 zip 包
    input_images=[                                 # 必填，参考图片列表（1~10 张）
        "path/to/pose_ref_1.png",
        "path/to/pose_ref_2.png",
    ],
    algorithm_model=None,                          # 可选，如 "VISVISE-PosingAI-V1.0.0"
    output_model_format=OutputModelFormat.FBX,    # 可选，输出格式
    name="gen_pose",                               # 可选，任务名称,
    rtx="caller_rtx",
)
```

---

### gen_segment_2d — 2D 拆分

对图生 360 输出的多视图进行组件分割（node_type=14，SSE 协议）。生成的分割资产 `model_id` 可作为图生中模/低模的 `segment_model_id` 输入。 → [示例代码](examples/gen_segment_2d.py)

```python
def on_thinking(content: str):
    print("[思考]", content)

seg_model_id = client.gen_segment_2d(
    model_id_360="Model202604xxxxxx",             # 必填（与 input_view 二选一），图生 360 的 model_id
    algorithm_model=None,                          # 可选，如 "VISVISE-Seg2D-V1.0.0"
    name="gen_segment_2d",                         # 可选，任务名称
    input_view=None,                               # 可选（与 model_id_360 二选一），输入视图
    split_type=None,                               # 可选，SegmentSplitType.FRONT_VIEW(1, 默认) / FOUR_VIEW(2)
    granularity=None,                              # 可选，SegmentGranularity.COARSE(1) / MEDIUM(2, 默认) / FINE(3)
    prompt=None,                                   # 可选，自然语言描述拆分规则（最长 200 字符）
    on_thinking=on_thinking,                       # 可选，处理 thinking 事件的回调,
    rtx="caller_rtx",
)
# 后续可作为 segment_model_id 传给 gen_mid_model / gen_low_model
mid_id = client.gen_mid_model(..., segment_model_id=seg_model_id, rtx="caller_rtx")
```

---

### wait_model — 等待完成

轮询等待异步任务完成，返回 `ModelInfo`。

```python
model_info = client.wait_model(
    model_id="Model2026033100192028",
    interval=2,     # 轮询间隔（秒），默认 2
    timeout=600,    # 超时时长（秒），默认 600,
    rtx="caller_rtx",
)

print(model_info.output_model)   # 输出模型下载 URL
print(model_info.time_cost)      # 耗时（秒）
```

**异常：**

- `PollingTimeoutError`：超时仍未完成时抛出
- `ModelGenerationError`：模型生成失败（status=4）时抛出
- `InvalidParamsError`：轮询接口返回参数错误时立即抛出（不重试）
- 其他网络/业务错误**不抛出**，会打印日志并继续重试

---

## 原子 API 方法参考

通过 `client.api.xxx(rtx="caller_rtx")` 访问底层接口：

```python
# 获取临时上传凭证
cred = client.api.get_cos_cred(rtx="caller_rtx")

# 查询剩余配额
quota = client.api.get_user_quota(rtx="caller_rtx")
print(quota.quota)  # 剩余次数

# 拉取模型列表
models, total = client.api.get_model_list(
    model_id_list=["Model2026..."],
    rtx="caller_rtx",
)

# 获取算法模型列表
alg_models = client.api.list_algorithm_model(node_type=4, sub_type=1, rtx="caller_rtx")

# 获取下载链接
url = client.api.download_model("Model2026...", rtx="caller_rtx")

# 删除单个
client.api.delete_model("Model2026...", rtx="caller_rtx")

# 批量删除
client.api.batch_delete_model(["Model2026...", "Model2026..."], rtx="caller_rtx")

# 去除背景
out_url = client.api.remove_bg("https://cos.../image.png", rtx="caller_rtx")

# 文生动画提示词列表
prompts = client.api.get_text2motion_prompt_list(language="zh", rtx="caller_rtx")
```

---

## 异常说明

所有 SDK 异常均继承自 `WeaverError`，可以捕获基类也可以精确捕获子类。

| 异常类 | 对应错误码 | 说明 |
|---|---|---|
| `WeaverError` | 任意 | 基础异常 |
| `NetworkError` | — | 网络连接失败、超时等 |
| `SignatureError` | 410 | 签名错误 |
| `SignatureExpiredError` | 411 | 签名过期，本地时钟与服务端偏差过大 |
| `InvalidParamsError` | 120008 | 请求参数错误 |
| `UserNotFoundError` | 120017 | 用户未找到 |
| `PermissionDeniedError` | 120018 | 用户无权限 |
| `QuotaExceededError` | 120020 | 每日配额超出上限 |
| `ProjectPermissionError` | 120027 | 项目权限未授权 |
| `ServerNetworkError` | 120028 | 服务器网络错误 |
| `ServerTimeoutError` | 120032 | 服务器处理超时 |
| `RateLimitError` | 120040 | 请求过于频繁 |
| `ModelGenerationError` | — | 模型生成失败（status=4） |
| `PollingTimeoutError` | — | wait_model 等待超时 |

```python
from visvise import VisviseClient, WeaverError, QuotaExceededError, PollingTimeoutError

client = VisviseClient(app_id="...", secret_key="...")

try:
    model_id = client.gen_360("image.png", rtx="caller_rtx")
    model = client.wait_model(model_id, rtx="caller_rtx")
except QuotaExceededError:
    print("今日配额已用完，明天再试")
except PollingTimeoutError as e:
    print(f"等待超时: {e.model_id}, {e.timeout}s")
except WeaverError as e:
    print(f"接口错误 [{e.code}]: {e.message}")
```

---

## 完整流程示例

### 示例一：图片 → 高模（图生360 + 图生高模）

```python
from visvise import VisviseClient, FaceType, OutputModelFormat

client = VisviseClient(app_id="...", secret_key="...")

# Step 1: 图生360
print("Step 1: 生成多视图...")
mv_id = client.gen_360(main_view="character.png", rtx="caller_rtx")
mv = client.wait_model(mv_id, interval=3, timeout=300, rtx="caller_rtx")
views = mv.image_gen_360_output.output_view

# Step 2: 图生高模
print("Step 2: 生成高模...")
high_id = client.gen_high_model(
    main_view=views.main_view,
    back_view=views.back_view,
    left_view=views.left_view,
    right_view=views.right_view,
    face_type=FaceType.TRIANGLE,
    rtx="caller_rtx",
)
high_model = client.wait_model(high_id, timeout=900, rtx="caller_rtx")
print("高模下载地址：", high_model.output_model)
```

---

### 示例二：动画生成流水线（骨骼 → 蒙皮 → 动画）

```python
from visvise import VisviseClient, OutputModelFormat

client = VisviseClient(app_id="...", secret_key="...")

# Step 1: 骨骼架设（直接传裸模型文件，SDK 自动打包）
rig_id = client.gen_rigging(
    model_path="character.fbx",
    mesh_category="humanoid",
    rtx="caller_rtx",
)
rig = client.wait_model(rig_id, timeout=600, rtx="caller_rtx")
print("骨骼模型：", rig.output_model)

# Step 2: 蒙皮生成（传入带骨骼的模型）
skin_id = client.gen_skinning(
    model_path="rigged_character.fbx",
    mesh_names=["Body_Mesh"],
    joint_names=["Bip001", "Bip001 Pelvis"],
    rtx="caller_rtx",
)
skin = client.wait_model(skin_id, timeout=600, rtx="caller_rtx")

# Step 3: 视频生动画
anim_id = client.gen_video_motion(
    model_path="skinned_model.zip",
    video_path="dance.mp4",
    output_model_format=OutputModelFormat.FBX,
    with_hand=True,
    rtx="caller_rtx",
)
anim = client.wait_model(anim_id, timeout=900, rtx="caller_rtx")
print("动画下载地址：", anim.output_model)
```

---

### 示例三：LOD 生成（含抽卡）

```python
from visvise import VisviseClient, ReduceFace, FaceType, OutputModelFormat

client = VisviseClient(app_id="...", secret_key="...")

model_ids = client.gen_lod(
    model_path="high_model.fbx",
    reduce_faces=[
        ReduceFace(reduce_level=1, reduce_percent=50, face_type=FaceType.QUAD),
        ReduceFace(reduce_level=2, reduce_percent=25, face_type=FaceType.QUAD),
    ],
    output_model_format=OutputModelFormat.FBX,
    gen_times=3,
    rtx="caller_rtx",
)

# 等待全部完成
results = [client.wait_model(mid, timeout=300, rtx="caller_rtx") for mid in model_ids]
for r in results:
    print(r.model_id, r.output_model)
```

---

## 开启日志

```python
import logging
logging.basicConfig(level=logging.DEBUG)  # 查看详细请求/响应日志

# 或只开启 visvise 相关日志
logging.getLogger("visvise").setLevel(logging.INFO)
```

---

## 许可证

MIT License
