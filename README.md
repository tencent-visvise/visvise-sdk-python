# VISVISE Weaver Python SDK

VISVISE Weaver OpenAPI 的 Python SDK，提供：

- 全部原子 API 方法（逐一对应 OpenAPI 接口）
- 各节点类型的高阶 `gen_xxx()` 方法（自动上传文件 + 创建任务）
- `wait_model()` 异步轮询方法

---

## 目录

- [安装](#安装)
- [快速开始](#快速开始)
- [客户端初始化](#客户端初始化)
- [高阶方法参考](#高阶方法参考)
  - [gen_360 — 图生360](#gen_360--图生360)
  - [gen_high_model — 图生高模](#gen_high_model--图生高模)
  - [gen_mid_model — 图生中模](#gen_mid_model--图生中模)
  - [gen_low_model — 图生低模](#gen_low_model--图生低模)
  - [gen_mesh_refine — 重布线](#gen_mesh_refine--重布线)
  - [gen_retopology — 重拓扑](#gen_retopology--重拓扑)
  - [gen_lod — LOD](#gen_lod--lod)
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

```bash
pip install visvise-weaver-sdk
```

如需使用本地文件自动上传功能，需额外安装腾讯云 COS SDK：

```bash
pip install "visvise-weaver-sdk[upload]"
```

---

## 快速开始

```python
from visvise import VisviseClient

client = VisviseClient(
    app_id="your_app_id",
    secret_key="your_secret_key",
)

# ① 图生360：生成多视图
mv_model_id = client.gen_360(
    main_view="https://cos.example.com/character.png",  # COS URL
    algorithm_model="hunyuan3D-MultiView-v3.0",
    name="my_360",
)

# ② 等待图生360完成，获取多视图输出
mv_info = client.wait_model(mv_model_id, interval=3, timeout=300)
output_view = mv_info.image_gen_360_output.output_view

# ③ 图生高模
high_model_id = client.gen_high_model(
    main_view=output_view.main_view,
    back_view=output_view.back_view,
    left_view=output_view.left_view,
    right_view=output_view.right_view,
    algorithm_model="hunyuan3D-v3.1",
    face_type=1,
    face_num=500000,
)

# ④ 等待高模完成
model_info = client.wait_model(high_model_id, timeout=900)
print("输出模型：", model_info.output_model)
```

---

## 客户端初始化

```python
from visvise import VisviseClient

client = VisviseClient(
    app_id="your_app_id",       # 必填，由平台分配
    secret_key="your_key",      # 必填，由平台分配
    base_url="https://ws.visvise.com.cn",  # 可选，默认值
    timeout=30,                 # 可选，单次请求超时（秒），默认 30
)
```

---

## 高阶方法参考

高阶方法封装了「COS 文件上传 + 创建异步任务」两步，传入文件路径（本地）或 COS URL 均可，返回 `model_id`。

### gen_360 — 图生360

从单张图片生成 360 度多视图。

```python
model_id = client.gen_360(
    main_view="path/to/character.png",   # 本地路径或 COS URL
    algorithm_model="hunyuan3D-MultiView-v3.0",
    name="gen_360",                      # 可选，任务名称
    enable_a_pose=False,                 # 可选
    style=None,                          # 可选，仅 VISVISE 自研模型支持
)
```

| 参数 | 必填 | 说明 |
|---|---|---|
| `main_view` | ✅ | 主视图本地路径或 COS URL |
| `algorithm_model` | ✅ | 算法模型名称 |
| `name` | — | 任务名称，默认 `gen_360` |
| `enable_a_pose` | — | 是否开启 A-Pose |
| `style` | — | 风格类型（仅 VISVISE 自研模型） |

---

### gen_high_model — 图生高模

从多视图生成高精度 3D 模型（node_type=11）。

```python
model_id = client.gen_high_model(
    main_view="https://cos.../main.png",
    algorithm_model="hunyuan3D-v3.1",
    output_model_format="fbx",
    face_type=1,
    face_num=500000,                # 可选，范围 1000~1500000
    back_view="https://cos.../back.png",   # 可选
    left_view="https://cos.../left.png",   # 可选
    right_view="https://cos.../right.png", # 可选
)
```

---

### gen_mid_model — 图生中模

中模要求四视图全部必传（node_type=3）。

```python
model_id = client.gen_mid_model(
    main_view="path/to/main.png",
    back_view="path/to/back.png",
    left_view="path/to/left.png",
    right_view="path/to/right.png",
    algorithm_model="VISVISE-MeshGen-V1.0.0",
    output_model_format="fbx",
    face_type=1,
)
```

---

### gen_low_model — 图生低模

低模只需主视图（node_type=13）。

```python
model_id = client.gen_low_model(
    main_view="path/to/main.png",
    algorithm_model="Tripo-v1.0-快速生成",
    output_model_format="fbx",
    face_type=1,
)
```

---

### gen_mesh_refine — 重布线

对模型进行布线优化（node_type=10）。

```python
model_id = client.gen_mesh_refine(
    model_path="path/to/model.zip",
    algorithm_model="VISVISE-MeshRefine-V1.0.0",
    input_model_format="fbx",
    enable_detail_preserve=True,    # 可选
)
```

---

### gen_retopology — 重拓扑

对高面数模型进行拓扑优化（node_type=1）。

> 注意：混元模型传 `detail_level`，VISVISE 自研模型传 `face_num`，二选一。

```python
# 混元模型
model_id = client.gen_retopology(
    model_path="path/to/model.zip",
    algorithm_model="hunyuan3D-RTP-v1.5",
    output_model_format="fbx",
    face_type=2,
    detail_level=3,   # 1:低 2:中 3:高
)

# VISVISE 自研模型
model_id = client.gen_retopology(
    model_path="path/to/model.zip",
    algorithm_model="VISVISE-RTP-v1.0",
    output_model_format="fbx",
    face_type=2,
    face_num=10000,
)
```

---

### gen_lod — LOD

生成多级细节模型（node_type=2），支持抽卡。

```python
from visvise import ReduceFace

model_ids = client.gen_lod(
    model_path="path/to/model.zip",
    algorithm_model="VISVISE-LOD-V1.0.0",
    reduce_faces=[
        ReduceFace(reduce_level=1, reduce_percent=50, face_type=2),
        ReduceFace(reduce_level=2, reduce_percent=25, face_type=2),
        ReduceFace(reduce_level=3, reduce_percent=13, face_type=2),
    ],
    output_model_format="fbx",
    gen_times=3,   # 抽卡 3 次，不需要抽卡传 1
)
# model_ids 有 3 个 ID（gen_times=3）
```

---

### gen_rigging — 骨骼架设

自动为模型生成骨骼（node_type=5）。

**zip 包要求：** 包含同名的 `.fbx` 和 `.json` 文件，json 示例：

```json
{
  "config": {
    "mesh_category": "humanoid",
    "algo_name": "VISVISE-GoRigging-V1.0.0"
  }
}
```

```python
model_id = client.gen_rigging(
    model_path="path/to/model.zip",   # 含 fbx + json 的 zip 包
    name="my_rigging",
)
```

参考示例文件：[rigging_demo.zip](https://visvise-weaver-bj-rel-1311802504.cos.ap-beijing.myqcloud.com/weaver/public/rigging_demo.zip)

---

### gen_skinning — 蒙皮生成

自动绑定蒙皮权重（node_type=6）。

**zip 包要求：** 包含同名的带骨骼 `.fbx` 和 `.json` 文件，json 示例：

```json
{
  "config": { "algo_name": "VISVISE-GoSkinning-V1.0.0" },
  "selection": {
    "mesh_names": ["Body_Mesh", "Hair_Mesh"],
    "joint_names": ["Bip001", "Bip001 Pelvis", "..."]
  }
}
```

```python
model_id = client.gen_skinning(
    model_path="path/to/skinning.zip",
    name="my_skinning",
)
```

参考示例文件：[skinning_demo.zip](https://visvise-weaver-bj-rel-1311802504.cos.ap-beijing.myqcloud.com/weaver/public/skinning_demo.zip)

---

### gen_video_motion — 视频生动画

从视频中提取动作驱动 3D 模型（node_type=4）。

```python
model_id = client.gen_video_motion(
    model_path="path/to/model.zip",
    video_path="path/to/dance.mp4",
    algorithm_model="VISVISE-FramingAI-Base-V1.5.0",
    output_model_format="fbx",
    with_hand=True,           # 可选：手部捕捉
    multiple_track=False,     # 可选：多人捕捉
)
```

---

### gen_text_motion — 文本生动画

通过提示词生成动画，一次返回 4 个模型供抽卡（node_type=4）。

```python
model_ids = client.gen_text_motion(
    model_path="path/to/model.zip",
    prompt="一个人在跳街舞",
    algorithm_model="VISVISE-TextMotion-V1.1.0",
    output_model_format="fbx",
)
# model_ids 包含 4 个 ID，等待其中你需要的那个即可
```

---

### gen_pose — 图生Pose

从参考图生成 Pose 模型（最多 10 张图片）。

```python
model_ids = client.gen_pose(
    model_path="path/to/model.zip",
    input_images=[
        "path/to/pose_ref_1.png",
        "path/to/pose_ref_2.png",
    ],
    algorithm_model="VISVISE-PosingAI-V1.0.0",
    output_model_format="fbx",
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

| 参数 | 说明 |
|---|---|
| `model_id` | 要等待的模型 ID |
| `interval` | 轮询间隔（秒），默认 2s |
| `timeout` | 超时时长（秒），默认 600s |

**异常：**

- `PollingTimeoutError`：超时仍未完成时抛出
- `ModelGenerationError`：模型生成失败（status=4）时抛出
- 轮询接口本身的网络/业务错误**不抛出**，会打印日志并继续重试

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

client = VisviseClient(...)

try:
    model_id = client.gen_360("image.png", algorithm_model="...")
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
from visvise import VisviseClient, PollingTimeoutError, ModelGenerationError

client = VisviseClient(app_id="...", secret_key="...")

# Step 1: 图生360
print("Step 1: 生成多视图...")
mv_id = client.gen_360(
    main_view="character.png",
    algorithm_model="hunyuan3D-MultiView-v3.0",
)
mv = client.wait_model(mv_id, interval=3, timeout=300)
views = mv.image_gen_360_output.output_view

# Step 2: 图生高模
print("Step 2: 生成高模...")
high_id = client.gen_high_model(
    main_view=views.main_view,
    back_view=views.back_view,
    left_view=views.left_view,
    right_view=views.right_view,
    algorithm_model="hunyuan3D-v3.1",
    face_type=1,
)
high_model = client.wait_model(high_id, timeout=900)
print("高模下载地址：", high_model.output_model)
```

---

### 示例二：动画生成流水线（骨骼 → 蒙皮 → 动画）

```python
client = VisviseClient(app_id="...", secret_key="...")

# Step 1: 骨骼架设
rig_id = client.gen_rigging("rigging_model.zip")
rig = client.wait_model(rig_id, timeout=600)
print("骨骼模型：", rig.output_model)

# Step 2: 蒙皮生成（使用骨骼架设的输出作为输入）
skin_id = client.gen_skinning("skinning_model.zip")
skin = client.wait_model(skin_id, timeout=600)

# Step 3: 视频生动画
anim_id = client.gen_video_motion(
    model_path="skinned_model.zip",
    video_path="dance.mp4",
    algorithm_model="VISVISE-FramingAI-Base-V1.5.0",
    with_hand=True,
)
anim = client.wait_model(anim_id, timeout=900)
print("动画下载地址：", anim.output_model)
```

---

### 示例三：LOD 生成（含抽卡）

```python
from visvise import ReduceFace

client = VisviseClient(app_id="...", secret_key="...")

model_ids = client.gen_lod(
    model_path="high_model.zip",
    algorithm_model="VISVISE-LOD-V1.0.0",
    reduce_faces=[
        ReduceFace(reduce_level=1, reduce_percent=50, face_type=2),
        ReduceFace(reduce_level=2, reduce_percent=25, face_type=2),
    ],
    gen_times=3,   # 生成 3 个版本供选择
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
