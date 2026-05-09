# VISVISE Weaver Python SDK

**[English](README_EN.md)** | 中文

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
  - [wait_model — 等待完成](#wait_model--等待完成)
- [原子 API 方法参考](#原子-api-方法参考)
- [异常说明](#异常说明)
- [完整流程示例](#完整流程示例)

---

## 安装

直接从 GitHub 仓库安装（包含 COS 上传依赖）：

```bash
pip install git+https://github.com/tencent-visvise/visvise-sdk-python.git
```

或通过 SSH：

```bash
pip install git+ssh://git@github.com/tencent-visvise/visvise-sdk-python.git
```

> **注：** 安装后即包含腾讯云 COS SDK，可直接使用本地文件自动上传功能，无需额外安装。

---

## 快速开始

```python
from visvise import VisviseClient, FaceType, OutputModelFormat

client = VisviseClient(
    app_id="your_app_id",
    secret_key="your_secret_key",
    uid="your_uid",
)

# ① 图生360：上传本地图片，生成多视图
mv_model_id = client.gen_360(
    main_view="character.png",          # 本地文件路径，SDK 自动上传
    name="my_360",
)

# ② 等待图生360完成，获取多视图输出
mv_info = client.wait_model(mv_model_id, interval=3, timeout=300)
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
)

# ④ 等待高模完成
model_info = client.wait_model(high_model_id, timeout=900)
print("输出模型：", model_info.output_model)
```

---

## 客户端初始化

```python
from visvise import VisviseClient, Environment

client = VisviseClient(
    app_id="your_app_id",       # 必填，由平台分配
    secret_key="your_key",      # 必填，由平台分配
    uid="your_uid",             # 必填，从申请 key 的登录账号获取
    env=Environment.PROD,       # 可选，默认生产环境
    timeout=30,                 # 可选，单次请求超时（秒），默认 30
)
```

| 参数 | 必填 | 说明 |
|---|---|---|
| `app_id` | ✅ | 由平台分配的客户端标识 |
| `secret_key` | ✅ | 由平台分配的签名密钥 |
| `uid` | ✅ | 用户 ID，从申请 key 的登录账号获取 |
| `env` | — | 环境：`Environment.PROD`（默认）/ `Environment.TEST` / `Environment.DEV` 或自定义 URL |
| `timeout` | — | 单次 HTTP 请求超时（秒），默认 30 |

---

## 枚举常量

SDK 提供以下枚举常量，推荐使用枚举替代硬编码数字/字符串：

```python
from visvise import FaceType, DetailLevel, OutputModelFormat, MeshRefineMode

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
```

---

## 高阶方法参考

高阶方法封装了「COS 文件上传 + 创建异步任务」两步，传入文件路径（本地）或 COS URL 均可，返回 `model_id`。

> **关于 `algorithm_model` 参数：** 所有 gen_xxx 方法的 `algorithm_model` 参数均为可选。若不传，SDK 将自动调用 `list_algorithm_model` 获取当前账号可用的第一个算法模型。

以下示例统一使用如下 import：

```python
from visvise import (
    VisviseClient, Environment,
    FaceType, DetailLevel, OutputModelFormat, MeshRefineMode,
    ReduceFace, View,
)

client = VisviseClient(app_id="...", secret_key="...", uid="...")
```

### gen_360 — 图生360

从单张图片生成 360 度多视图。 → [示例代码](examples/gen_360.py)

```python
model_id = client.gen_360(
    main_view="path/to/character.png",
    algorithm_model="hunyuan3D-MultiView-v3.0",  # 可选
    name="gen_360",
    enable_a_pose=False,
    style=None,
)
```

---

### gen_high_model — 图生高模

从多视图生成高精度 3D 模型（node_type=3）。 → [示例代码](examples/gen_high_model.py)

```python
model_id = client.gen_high_model(
    main_view="path/to/main.png",               # 本地文件路径，SDK 自动上传
    algorithm_model="hunyuan3D-v3.1",           # 可选
    output_model_format=OutputModelFormat.FBX,
    face_type=FaceType.TRIANGLE,
    face_num=500000,
    back_view="path/to/back.png",               # 可选
    left_view="path/to/left.png",               # 可选
    right_view="path/to/right.png",             # 可选
)
```

---

### gen_mid_model — 图生中模

中模要求四视图全部必传（node_type=11）。 → [示例代码](examples/gen_mid_model.py)

```python
model_id = client.gen_mid_model(
    main_view="path/to/main.png",
    back_view="path/to/back.png",
    left_view="path/to/left.png",
    right_view="path/to/right.png",
    algorithm_model="VISVISE-MeshGen-V1.0.0",   # 可选
    output_model_format=OutputModelFormat.FBX,
    face_type=FaceType.TRIANGLE,
    segment_model_id=None,                       # 可选，2D 分割资产 ID
)
```

---

### gen_low_model — 图生低模

低模只需主视图（node_type=13）。 → [示例代码](examples/gen_low_model.py)

```python
model_id = client.gen_low_model(
    main_view="path/to/main.png",
    algorithm_model="Tripo-v1.0-快速生成",      # 可选
    output_model_format=OutputModelFormat.FBX,
    face_type=FaceType.TRIANGLE,
)
```

---

### gen_mesh_refine — 重布线

对模型进行布线优化（node_type=10）。 → [示例代码](examples/gen_mesh_refine.py)

```python
model_id = client.gen_mesh_refine(
    model_path="path/to/model.fbx",             # 本地模型文件，SDK 自动打包上传
    algorithm_model="VISVISE-MeshRefine-V1.0.0", # 可选
    input_model_format="fbx",
    mode=MeshRefineMode.OPTIMIZE,                # 可选，1 布线优化（默认）/ 2 布线加密
    color_model="path/to/color_model.fbx",       # 可选，带颜色的模型
)
```

---

### gen_retopology — 重拓扑

对高面数模型进行拓扑优化（node_type=1）。 → [示例代码](examples/gen_retopology.py)

> 注意：混元模型传 `detail_level`，VISVISE 自研模型传 `face_num`，二选一。

```python
# 混元模型
model_id = client.gen_retopology(
    model_path="path/to/model.fbx",
    algorithm_model="hunyuan3D-RTP-v1.5",       # 可选
    output_model_format=OutputModelFormat.FBX,
    face_type=FaceType.QUAD,
    detail_level=DetailLevel.HIGH,
)

# VISVISE 自研模型
model_id = client.gen_retopology(
    model_path="path/to/model.fbx",
    algorithm_model="VISVISE-RTP-V1.0.0",
    output_model_format=OutputModelFormat.FBX,
    face_type=FaceType.QUAD,
    face_num=10000,
)
```

---

### gen_lod — LOD

生成多级细节模型（node_type=2），支持抽卡。 → [示例代码](examples/gen_lod.py)

```python
from visvise import ReduceFace

model_ids = client.gen_lod(
    model_path="path/to/model.fbx",
    reduce_faces=[
        ReduceFace(reduce_level=1, reduce_percent=50, face_type=FaceType.QUAD),
        ReduceFace(reduce_level=2, reduce_percent=25, face_type=FaceType.QUAD),
    ],
    algorithm_model="VISVISE-LOD-V1.0.0",       # 可选
    output_model_format=OutputModelFormat.FBX,
    gen_times=3,
)
```

---

### gen_uv — UV展开

自动 UV 展开（node_type=9）。 → [示例代码](examples/gen_uv.py)

```python
model_id = client.gen_uv(
    model_path="path/to/model.fbx",
    algorithm_model="hunyuan3D-UV-v2.0",        # 可选
    enable_auto_smoothing=True,                  # 可选
)
```

---

### gen_texture — 贴图纹理

为模型生成贴图纹理（node_type=8）。 → [示例代码](examples/gen_texture.py)

```python
from visvise import View

model_id = client.gen_texture(
    model_path="path/to/model.fbx",
    algorithm_model="hunyuan3D-TEX-v2.0",       # 可选
    input_view=View(main_view="path/to/ref.png"),
    resolution=2048,
    prompt="写实风格",                            # 可选
)
```

---

### gen_rigging — 骨骼架设

自动为模型生成骨骼（node_type=5）。SDK 自动将模型文件与参数 JSON 打包成 zip 上传，无需手动准备 zip 包。 → [示例代码](examples/gen_rigging.py)

```python
model_id = client.gen_rigging(
    model_path="path/to/model.fbx",             # 裸模型文件即可，SDK 自动打包
    algorithm_model="VISVISE-GoRigging-V1.0.0", # 可选
    mesh_category="humanoid",                    # "humanoid"（人形）或 "tetrapod"（四足）
)
rig = client.wait_model(model_id)
print("骨骼模型：", rig.output_model)
```

---

### gen_skinning — 蒙皮生成

自动绑定蒙皮权重（node_type=6）。SDK 自动将模型文件与参数 JSON 打包成 zip 上传。 → [示例代码](examples/gen_skinning.py)

```python
model_id = client.gen_skinning(
    model_path="path/to/rigged_model.fbx",      # 带骨骼的模型文件
    mesh_names=["Body_Mesh", "Hair_Mesh"],       # 需要蒙皮的网格名称列表
    joint_names=["Bip001", "Bip001 Pelvis"],     # 需要蒙皮的骨骼名称列表
    algorithm_model="VISVISE-GoSkinning-V1.0.0", # 可选
)
skin = client.wait_model(model_id)
print("蒙皮模型：", skin.output_model)
```

---

### gen_video_motion — 视频生动画

从视频中提取动作驱动 3D 模型（node_type=4）。 → [示例代码](examples/gen_video_motion.py)

```python
model_id = client.gen_video_motion(
    model_path="path/to/model.zip",
    video_path="path/to/dance.mp4",
    algorithm_model="VISVISE-FramingAI-Base-V1.5.0", # 可选
    output_model_format=OutputModelFormat.FBX,
    with_hand=True,
    multiple_track=False,
)
```

---

### gen_text_motion — 文本生动画

通过提示词生成动画，一次返回 4 个模型供抽卡（node_type=4）。 → [示例代码](examples/gen_text_motion.py)

```python
model_ids = client.gen_text_motion(
    model_path="path/to/model.zip",
    prompt="一个人在跳街舞",
    algorithm_model="VISVISE-TextMotion-V1.1.0", # 可选
    output_model_format=OutputModelFormat.FBX,
)
# model_ids 包含 4 个 ID，等待其中你需要的那个即可
```

---

### gen_pose — 图生Pose

从参考图生成 Pose 模型（最多 10 张图片）。 → [示例代码](examples/gen_pose.py)

```python
model_ids = client.gen_pose(
    model_path="path/to/model.zip",
    input_images=["path/to/pose_ref_1.png", "path/to/pose_ref_2.png"],
    algorithm_model="VISVISE-PosingAI-V1.0.0",  # 可选
    output_model_format=OutputModelFormat.FBX,
)
```

---

### wait_model — 等待完成

轮询等待异步任务完成，返回 `ModelInfo`。

```python
model_info = client.wait_model(
    model_id="Model2026033100192028",
    interval=2,     # 轮询间隔（秒），默认 2
    timeout=600,    # 超时时长（秒），默认 600
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

通过 `client.api.xxx()` 访问底层接口：

```python
# 获取临时上传凭证
cred = client.api.get_cos_cred()

# 查询剩余配额
quota = client.api.get_user_quota()
print(quota.quota)  # 剩余次数

# 拉取模型列表
models, total = client.api.get_model_list(
    model_id_list=["Model2026..."],
)

# 获取算法模型列表
alg_models = client.api.list_algorithm_model(node_type=4, sub_type=1)

# 获取下载链接
url = client.api.download_model("Model2026...")

# 删除单个
client.api.delete_model("Model2026...")

# 批量删除
client.api.batch_delete_model(["Model2026...", "Model2026..."])

# 去除背景
out_url = client.api.remove_bg("https://cos.../image.png")

# 文生动画提示词列表
prompts = client.api.get_text2motion_prompt_list(language="zh")
```

---

## 异常说明

所有 SDK 异常均继承自 `WeaverError`，可以捕获基类也可以精确捕获子类。

| 异常类 | 对应错误码 | 说明 |
|---|---|---|
| `WeaverError` | 任意 | 基础异常 |
| `NetworkError` | — | 网络连接失败、超时等 |
| `SignatureError` | 400 | 签名错误 |
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

client = VisviseClient(app_id="...", secret_key="...", uid="...")

try:
    model_id = client.gen_360("image.png")
    model = client.wait_model(model_id)
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

client = VisviseClient(app_id="...", secret_key="...", uid="...")

# Step 1: 图生360
print("Step 1: 生成多视图...")
mv_id = client.gen_360(main_view="character.png")
mv = client.wait_model(mv_id, interval=3, timeout=300)
views = mv.image_gen_360_output.output_view

# Step 2: 图生高模
print("Step 2: 生成高模...")
high_id = client.gen_high_model(
    main_view=views.main_view,
    back_view=views.back_view,
    left_view=views.left_view,
    right_view=views.right_view,
    face_type=FaceType.TRIANGLE,
)
high_model = client.wait_model(high_id, timeout=900)
print("高模下载地址：", high_model.output_model)
```

---

### 示例二：动画生成流水线（骨骼 → 蒙皮 → 动画）

```python
from visvise import VisviseClient, OutputModelFormat

client = VisviseClient(app_id="...", secret_key="...", uid="...")

# Step 1: 骨骼架设（直接传裸模型文件，SDK 自动打包）
rig_id = client.gen_rigging(
    model_path="character.fbx",
    mesh_category="humanoid",
)
rig = client.wait_model(rig_id, timeout=600)
print("骨骼模型：", rig.output_model)

# Step 2: 蒙皮生成（传入带骨骼的模型）
skin_id = client.gen_skinning(
    model_path="rigged_character.fbx",
    mesh_names=["Body_Mesh"],
    joint_names=["Bip001", "Bip001 Pelvis"],
)
skin = client.wait_model(skin_id, timeout=600)

# Step 3: 视频生动画
anim_id = client.gen_video_motion(
    model_path="skinned_model.zip",
    video_path="dance.mp4",
    output_model_format=OutputModelFormat.FBX,
    with_hand=True,
)
anim = client.wait_model(anim_id, timeout=900)
print("动画下载地址：", anim.output_model)
```

---

### 示例三：LOD 生成（含抽卡）

```python
from visvise import VisviseClient, ReduceFace, FaceType, OutputModelFormat

client = VisviseClient(app_id="...", secret_key="...", uid="...")

model_ids = client.gen_lod(
    model_path="high_model.fbx",
    reduce_faces=[
        ReduceFace(reduce_level=1, reduce_percent=50, face_type=FaceType.QUAD),
        ReduceFace(reduce_level=2, reduce_percent=25, face_type=FaceType.QUAD),
    ],
    output_model_format=OutputModelFormat.FBX,
    gen_times=3,
)

# 等待全部完成
results = [client.wait_model(mid, timeout=300) for mid in model_ids]
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
