# VISVISE Weaver Python SDK

[中文](README.md) | **English**

Python SDK for the VISVISE Weaver OpenAPI. It provides:

- All atomic API methods (1:1 mapping to OpenAPI endpoints)
- High-level `gen_xxx()` methods for each node type (auto-upload files + create tasks)
- `wait_model()` async polling helper

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Client Initialization](#client-initialization)
- [Enum Constants](#enum-constants)
- [High-Level Methods](#high-level-methods)
  - [gen_360 — Image to 360](#gen_360--image-to-360)
  - [gen_high_model — Image to High-poly](#gen_high_model--image-to-high-poly)
  - [gen_mid_model — Image to Mid-poly](#gen_mid_model--image-to-mid-poly)
  - [gen_low_model — Image to Low-poly](#gen_low_model--image-to-low-poly)
  - [gen_mesh_refine — Mesh Refinement](#gen_mesh_refine--mesh-refinement)
  - [gen_retopology — Retopology](#gen_retopology--retopology)
  - [gen_lod — LOD](#gen_lod--lod)
  - [gen_uv — UV Unwrap](#gen_uv--uv-unwrap)
  - [gen_texture — Texture Generation](#gen_texture--texture-generation)
  - [gen_rigging — Rigging](#gen_rigging--rigging)
  - [gen_skinning — Skinning](#gen_skinning--skinning)
  - [gen_video_motion — Video to Animation](#gen_video_motion--video-to-animation)
  - [gen_text_motion — Text to Animation](#gen_text_motion--text-to-animation)
  - [gen_pose — Image to Pose](#gen_pose--image-to-pose)
  - [gen_segment_2d — 2D Segmentation](#gen_segment_2d--2d-segmentation)
  - [wait_model — Wait for Completion](#wait_model--wait-for-completion)
- [Atomic API Methods](#atomic-api-methods)
- [Exceptions](#exceptions)
- [Full Workflow Examples](#full-workflow-examples)

---

## Installation

Install directly from the GitHub repository (Tencent Cloud COS dependency included):

```bash
pip install git+https://github.com/tencent-visvise/visvise-sdk-python.git@v1.0.2
```

Or via SSH:

```bash
pip install git+ssh://git@github.com/tencent-visvise/visvise-sdk-python.git@v1.0.2
```

> **Note:** The Tencent Cloud COS SDK is bundled by default; local file auto-upload works out of the box.

---

## Quick Start

```python
from visvise import VisviseClient, FaceType, OutputModelFormat

client = VisviseClient(
    app_id="your_app_id",
    secret_key="your_secret_key",
    uid="your_uid",
)

# 1) Image-to-360: upload local image, generate multi-views
mv_model_id = client.gen_360(
    main_view="character.png",          # local path, SDK uploads automatically
    name="my_360",
)

# 2) Wait for completion, fetch multi-view output
mv_info = client.wait_model(mv_model_id, interval=3, timeout=300)
output_view = mv_info.image_gen_360_output.output_view

# 3) Image-to-high-poly (pass COS URLs directly)
high_model_id = client.gen_high_model(
    main_view=output_view.main_view,
    back_view=output_view.back_view,
    left_view=output_view.left_view,
    right_view=output_view.right_view,
    output_model_format=OutputModelFormat.FBX,
    face_type=FaceType.TRIANGLE,
    face_num=500000,
)

# 4) Wait for completion
model_info = client.wait_model(high_model_id, timeout=900)
print("Output model:", model_info.output_model)
```

---

## Client Initialization

```python
from visvise import VisviseClient, Environment

client = VisviseClient(
    app_id="your_app_id",       # required, assigned by platform
    secret_key="your_key",      # required, assigned by platform
    uid="your_uid",             # required, the user ID of the account that obtained the key
    env=Environment.PROD,       # optional, default: production
    timeout=30,                 # optional, per-request HTTP timeout in seconds (default 30)
)
```

| Parameter | Required | Description |
|---|---|---|
| `app_id` | ✅ | Client identifier assigned by the platform |
| `secret_key` | ✅ | Signing key assigned by the platform |
| `uid` | ✅ | User ID, obtained from the account that registered the key |
| `env` | — | Environment: `Environment.PROD` (default) / `Environment.TEST` / `Environment.DEV` or a custom URL |
| `timeout` | — | Per-request HTTP timeout in seconds (default 30) |

---

## Enum Constants

The SDK exposes the following enum constants. Prefer them over hard-coded numbers/strings:

```python
from visvise import FaceType, DetailLevel, OutputModelFormat, MeshRefineMode, SegmentSplitType, SegmentGranularity

# Face type
FaceType.TRIANGLE  # 1 - triangle faces
FaceType.QUAD      # 2 - quad faces

# Detail level (for retopology)
DetailLevel.LOW    # 1 - low
DetailLevel.MEDIUM # 2 - medium
DetailLevel.HIGH   # 3 - high

# Output model format
OutputModelFormat.FBX  # "fbx"
OutputModelFormat.OBJ  # "obj"
OutputModelFormat.GLB  # "glb"

# Mesh refine mode
MeshRefineMode.OPTIMIZE  # 1 - mesh optimization
MeshRefineMode.DENSIFY   # 2 - mesh densification

# 2D segmentation split type
SegmentSplitType.FRONT_VIEW  # 1 - front-view split (default)
SegmentSplitType.FOUR_VIEW   # 2 - four-view split

# 2D segmentation granularity
SegmentGranularity.COARSE   # 1 - coarse
SegmentGranularity.MEDIUM   # 2 - medium (default)
SegmentGranularity.FINE     # 3 - fine
```

---

## High-Level Methods

High-level methods bundle "COS upload + async task creation" into a single call. Pass either a local file path or a VISVISE COS URL; each method returns a `model_id`.

> **About `algorithm_model`:** Every `gen_xxx` method's `algorithm_model` is optional. When omitted, the SDK calls `list_algorithm_model` and uses the first available model for the current account.

> **About file inputs:** All file parameters (e.g. `main_view` / `model_path` / `video_path` / `input_images`) accept three forms:
> - **Local path** (`str`): the SDK uploads the file automatically.
> - **VISVISE COS URL** (`str`): pass a `https://...myqcloud.com/...` link directly; the SDK skips upload.
> - **Binary content** (`bytes` / `BinaryIO`): the SDK auto-detects the format via magic bytes (images PNG/JPEG/GIF/BMP/WebP/TIFF, 3D models FBX/OBJ/GLB/GLTF, videos MP4/MOV/WebM/AVI, ZIP) and uploads as `<uuid>.<sniffed-ext>` — no filename required from the caller.

The examples below share the following imports:

```python
from visvise import (
    VisviseClient, Environment,
    FaceType, DetailLevel, OutputModelFormat, MeshRefineMode,
    SegmentSplitType, SegmentGranularity,
    ReduceFace, View,
)

client = VisviseClient(app_id="...", secret_key="...", uid="...")
```

### gen_360 — Image to 360

Generate 360-degree multi-views from a single image. → [Example](examples/gen_360.py)

```python
model_id = client.gen_360(
    main_view="path/to/character.png",   # required, main view (local path or VISVISE COS URL)
    algorithm_model=None,                # optional, e.g. "hunyuan3D-MultiView-v3.0"; auto-selected if omitted
    name="gen_360",                      # optional, task name
    enable_a_pose=None,                  # optional, enable A-Pose (True/False)
    style=None,                          # optional, style (VISVISE proprietary models only): grayscale / photoreal / Q-toon / pixel
    back_view=None,                      # optional, back view to improve quality
    left_view=None,                      # optional, left view
    right_view=None,                     # optional, right view
)
```

---

### gen_high_model — Image to High-poly

Generate a high-poly 3D model from images / multi-views (node_type=3). → [Example](examples/gen_high_model.py)

```python
model_id = client.gen_high_model(
    main_view="path/to/main.png",                 # required, main view
    algorithm_model=None,                          # optional, e.g. "hunyuan3D-v3.1"; auto-selected if omitted
    output_model_format=OutputModelFormat.FBX,    # optional, output format (default fbx)
    face_type=FaceType.TRIANGLE,                  # optional, face type (default triangle)
    name="gen_high_model",                         # optional, task name
    face_num=None,                                 # optional, target face count (1000-1500000); auto-tuned if omitted
    back_view=None,                                # optional, back view to improve quality
    left_view=None,                                # optional, left view
    right_view=None,                               # optional, right view
)
```

---

### gen_mid_model — Image to Mid-poly

Mid-poly generation requires all four views (node_type=11). → [Example](examples/gen_mid_model.py)

```python
model_id = client.gen_mid_model(
    main_view="path/to/main.png",                 # required (all four views are required)
    back_view="path/to/back.png",                 # required
    left_view="path/to/left.png",                 # required
    right_view="path/to/right.png",               # required
    algorithm_model=None,                          # optional, e.g. "VISVISE-MeshGen-V1.0.0"
    output_model_format=OutputModelFormat.FBX,    # optional, output format
    face_type=FaceType.TRIANGLE,                  # optional, face type
    name="gen_mid_model",                          # optional, task name
    segment_model_id=None,                         # optional, 2D segmentation asset ID (mid-poly only)
)
```

---

### gen_low_model — Image to Low-poly

Low-poly only needs the main view (node_type=13). → [Example](examples/gen_low_model.py)

```python
model_id = client.gen_low_model(
    main_view="path/to/main.png",                 # required, main view
    algorithm_model=None,                          # optional, e.g. "Tripo-v1.0-fast"
    output_model_format=OutputModelFormat.FBX,    # optional, output format
    face_type=FaceType.TRIANGLE,                  # optional, face type
    name="gen_low_model",                          # optional, task name
    back_view=None,                                # optional, back view
    left_view=None,                                # optional, left view
    right_view=None,                               # optional, right view
)
```

---

### gen_mesh_refine — Mesh Refinement

Mesh-line refinement (node_type=10). → [Example](examples/gen_mesh_refine.py)

```python
model_id = client.gen_mesh_refine(
    model_path="path/to/model.fbx",               # required, raw model is auto-zipped by the SDK
    algorithm_model=None,                          # optional, e.g. "VISVISE-MeshRefine-V1.0.0"
    input_model_format="fbx",                     # optional, input format (default fbx)
    name="gen_mesh_refine",                        # optional, task name
    mode=None,                                     # optional, MeshRefineMode.OPTIMIZE(1, default) / DENSIFY(2)
    color_model=None,                              # optional, colored model used to attach color info
)
```

---

### gen_retopology — Retopology

Retopology of high-poly models (node_type=1). → [Example](examples/gen_retopology.py)

> Note: pass `detail_level` for Hunyuan models, `face_num` for VISVISE proprietary models — choose one.

```python
model_id = client.gen_retopology(
    model_path="path/to/model.fbx",               # required, input model
    algorithm_model=None,                          # optional, e.g. "hunyuan3D-RTP-v1.5" / "VISVISE-RTP-V1.0.0"
    output_model_format=OutputModelFormat.FBX,    # optional, output format
    face_type=FaceType.QUAD,                      # optional, face type (default quad)
    name="gen_retopology",                         # optional, task name
    detail_level=DetailLevel.HIGH,                # optional (required by Hunyuan): DetailLevel.LOW/MEDIUM/HIGH
    face_num=None,                                 # optional (required by VISVISE proprietary): target face count
)
```

---

### gen_lod — LOD

Generate level-of-detail meshes (node_type=2), with multi-shot support. → [Example](examples/gen_lod.py)

```python
model_ids = client.gen_lod(
    model_path="path/to/model.fbx",               # required, input model
    reduce_faces=[                                 # required, reduction config list
        ReduceFace(reduce_level=1, reduce_percent=50, face_type=FaceType.QUAD),
        ReduceFace(reduce_level=2, reduce_percent=25, face_type=FaceType.QUAD),
    ],
    algorithm_model=None,                          # optional, e.g. "VISVISE-LOD-V1.0.0"
    output_model_format=OutputModelFormat.FBX,    # optional, output format
    name="gen_lod",                                # optional, task name
    gen_times=3,                                   # optional, number of variants (use 1 to disable multi-shot)
)
```

---

### gen_uv — UV Unwrap

Automatic UV unwrap (node_type=9). → [Example](examples/gen_uv.py)

```python
model_id = client.gen_uv(
    model_path="path/to/model.fbx",               # required, input model
    algorithm_model=None,                          # optional, e.g. "hunyuan3D-UV-v2.0"
    name="gen_uv",                                 # optional, task name
    enable_auto_smoothing=None,                    # optional, enable auto-smoothing
)
```

---

### gen_texture — Texture Generation

Generate textures for a model (node_type=8). → [Example](examples/gen_texture.py)

> At least one of `input_view.main_view` or `prompt` is required; both can be supplied together.

```python
model_id = client.gen_texture(
    model_path="path/to/model.fbx",               # required, input model
    algorithm_model=None,                          # optional, e.g. "hunyuan3D-TEX-v2.0"
    name="gen_texture",                            # optional, task name
    input_view=View(main_view="path/to/ref.png"), # optional, reference view (or use prompt instead)
    resolution=None,                               # optional, resolution (e.g. 1024 / 2048)
    unwarp_uv=None,                                # optional, also unwrap UV
    prompt=None,                                   # optional, text prompt for the texture
)
```

---

### gen_rigging — Rigging

Auto-rigging (node_type=5). The SDK packages the raw model + JSON parameters into a zip automatically — no manual zipping required. → [Example](examples/gen_rigging.py)

```python
model_id = client.gen_rigging(
    model_path="path/to/model.fbx",               # required, raw model (auto-zipped by SDK)
    algorithm_model=None,                          # optional, e.g. "VISVISE-GoRigging-V1.0.0"
    mesh_category="humanoid",                     # optional, "humanoid" (default) or "tetrapod"
    name="gen_rigging",                            # optional, task name
    template_skeleton=None,                        # optional, template skeleton to base the rig on
)
```

---

### gen_skinning — Skinning

Auto-skinning (node_type=6). The SDK packages the rigged model + selection JSON into a zip automatically. → [Example](examples/gen_skinning.py)

```python
model_id = client.gen_skinning(
    model_path="path/to/rigged_model.fbx",        # required, rigged model
    mesh_names=["Body_Mesh", "Hair_Mesh"],         # required, meshes to skin
    joint_names=["Bip001", "Bip001 Pelvis"],       # required, joints to skin
    algorithm_model=None,                          # optional, e.g. "VISVISE-GoSkinning-V1.0.0"
    name="gen_skinning",                           # optional, task name
)
```

---

### gen_video_motion — Video to Animation

Drive a 3D model from motion extracted from a video (node_type=4). → [Example](examples/gen_video_motion.py)

```python
model_id = client.gen_video_motion(
    model_path="path/to/model.zip",               # required, model zip
    video_path="path/to/dance.mp4",               # required, source video
    algorithm_model=None,                          # optional, e.g. "VISVISE-FramingAI-Base-V1.5.0"
    output_model_format=OutputModelFormat.FBX,    # optional, output format
    name="gen_video_motion",                       # optional, task name
    with_hand=None,                                # optional, enable hand capture
    multiple_track=None,                           # optional, enable multi-person capture
    rotate_axis_angle=None,                        # optional, rotation axis-angle [x, y, z] (radians)
)
```

---

### gen_text_motion — Text to Animation

Generate animation from a text prompt; returns 4 candidate models (node_type=4). → [Example](examples/gen_text_motion.py)

```python
model_ids = client.gen_text_motion(
    model_path="path/to/model.zip",               # required, model zip
    prompt="a person breakdancing",                # required, animation prompt
    algorithm_model=None,                          # optional, e.g. "VISVISE-TextMotion-V1.1.0"
    output_model_format=OutputModelFormat.FBX,    # optional, output format
    name="gen_text_motion",                        # optional, task name
)
# model_ids contains 4 IDs, wait for whichever you prefer
```

---

### gen_pose — Image to Pose

Generate pose models from reference images (up to 10). → [Example](examples/gen_pose.py)

```python
model_ids = client.gen_pose(
    model_path="path/to/model.zip",               # required, FBX model zip
    input_images=[                                 # required, reference images (1-10)
        "path/to/pose_ref_1.png",
        "path/to/pose_ref_2.png",
    ],
    algorithm_model=None,                          # optional, e.g. "VISVISE-PosingAI-V1.0.0"
    output_model_format=OutputModelFormat.FBX,    # optional, output format
    name="gen_pose",                               # optional, task name
)
```

---

### gen_segment_2d — 2D Segmentation

Component segmentation over multi-views from gen_360 (node_type=14, SSE protocol). The resulting `model_id` can be passed as `segment_model_id` for `gen_mid_model` / `gen_low_model`. → [Example](examples/gen_segment_2d.py)

```python
def on_thinking(content: str):
    print("[thinking]", content)

seg_model_id = client.gen_segment_2d(
    model_id_360="Model202604xxxxxx",             # required (or pass input_view), the gen_360 model_id
    algorithm_model=None,                          # optional, e.g. "VISVISE-Seg2D-V1.0.0"
    name="gen_segment_2d",                         # optional, task name
    input_view=None,                               # optional (or pass model_id_360), input view
    split_type=None,                               # optional, SegmentSplitType.FRONT_VIEW(1, default) / FOUR_VIEW(2)
    granularity=None,                              # optional, SegmentGranularity.COARSE(1) / MEDIUM(2, default) / FINE(3)
    prompt=None,                                   # optional, natural-language splitting rule (max 200 chars)
    on_thinking=on_thinking,                       # optional, callback for thinking events
)
# Use the result as segment_model_id for gen_mid_model / gen_low_model
mid_id = client.gen_mid_model(..., segment_model_id=seg_model_id)
```

---

### wait_model — Wait for Completion

Poll until an async task finishes; returns `ModelInfo`.

```python
model_info = client.wait_model(
    model_id="Model2026033100192028",
    interval=2,     # poll interval in seconds (default 2)
    timeout=600,    # max wait in seconds (default 600)
)

print(model_info.output_model)   # output model URL
print(model_info.time_cost)      # elapsed seconds
```

**Exceptions:**

- `PollingTimeoutError` — raised when the timeout is reached
- `ModelGenerationError` — raised when the task fails (status=4)
- `InvalidParamsError` — raised immediately on parameter errors during polling (no retry)
- Other network/business errors are logged and **silently retried**

---

## Atomic API Methods

Access low-level endpoints via `client.api.xxx()`:

```python
# Get temporary upload credentials
cred = client.api.get_cos_cred()

# Query remaining quota
quota = client.api.get_user_quota()
print(quota.quota)  # remaining count

# Fetch model list
models, total = client.api.get_model_list(
    model_id_list=["Model2026..."],
)

# Fetch algorithm models for a node type
alg_models = client.api.list_algorithm_model(node_type=4, sub_type=1)

# Get download URL
url = client.api.download_model("Model2026...")

# Delete a single model
client.api.delete_model("Model2026...")

# Batch delete
client.api.batch_delete_model(["Model2026...", "Model2026..."])

# Remove background
out_url = client.api.remove_bg("https://cos.../image.png")

# Text-to-motion prompt suggestions
prompts = client.api.get_text2motion_prompt_list(language="en")
```

---

## Exceptions

All SDK exceptions inherit from `WeaverError`; you can catch the base class or any subclass.

| Exception | Code | Description |
|---|---|---|
| `WeaverError` | any | Base exception |
| `NetworkError` | — | Connection / timeout errors |
| `SignatureError` | 411 | Signature failure |
| `SignatureExpiredError` | 412 | Signature expired (clock skew between client and server) |
| `InvalidParamsError` | 120008 | Invalid request parameters |
| `UserNotFoundError` | 120017 | User not found |
| `PermissionDeniedError` | 120018 | Permission denied |
| `QuotaExceededError` | 120020 | Daily quota exceeded |
| `ProjectPermissionError` | 120027 | Project permission missing |
| `ServerNetworkError` | 120028 | Server network error |
| `ServerTimeoutError` | 120032 | Server processing timeout |
| `RateLimitError` | 120040 | Too many requests |
| `ModelGenerationError` | — | Task failed (status=4) |
| `PollingTimeoutError` | — | wait_model timed out |

```python
from visvise import VisviseClient, WeaverError, QuotaExceededError, PollingTimeoutError

client = VisviseClient(...)

try:
    model_id = client.gen_360("image.png")
    model = client.wait_model(model_id)
except QuotaExceededError:
    print("Daily quota exceeded; please try again tomorrow")
except PollingTimeoutError as e:
    print(f"Timeout: {e.model_id}, {e.timeout}s")
except WeaverError as e:
    print(f"API error [{e.code}]: {e.message}")
```

---

## Full Workflow Examples

### Example 1: Image → High-poly (gen_360 + gen_high_model)

```python
from visvise import VisviseClient, FaceType, OutputModelFormat

client = VisviseClient(app_id="...", secret_key="...", uid="...")

# Step 1: Image-to-360
print("Step 1: generating multi-views...")
mv_id = client.gen_360(main_view="character.png")
mv = client.wait_model(mv_id, interval=3, timeout=300)
views = mv.image_gen_360_output.output_view

# Step 2: High-poly model
print("Step 2: generating high-poly model...")
high_id = client.gen_high_model(
    main_view=views.main_view,
    back_view=views.back_view,
    left_view=views.left_view,
    right_view=views.right_view,
    face_type=FaceType.TRIANGLE,
)
high_model = client.wait_model(high_id, timeout=900)
print("High-poly download URL:", high_model.output_model)
```

---

### Example 2: Animation pipeline (Rigging → Skinning → Animation)

```python
from visvise import VisviseClient, OutputModelFormat

client = VisviseClient(app_id="...", secret_key="...", uid="...")

# Step 1: Rigging (pass raw model — SDK auto-zips)
rig_id = client.gen_rigging(
    model_path="character.fbx",
    mesh_category="humanoid",
)
rig = client.wait_model(rig_id, timeout=600)
print("Rigged model:", rig.output_model)

# Step 2: Skinning (pass rigged model)
skin_id = client.gen_skinning(
    model_path="rigged_character.fbx",
    mesh_names=["Body_Mesh"],
    joint_names=["Bip001", "Bip001 Pelvis"],
)
skin = client.wait_model(skin_id, timeout=600)

# Step 3: Video-to-animation
anim_id = client.gen_video_motion(
    model_path="skinned_model.zip",
    video_path="dance.mp4",
    output_model_format=OutputModelFormat.FBX,
    with_hand=True,
)
anim = client.wait_model(anim_id, timeout=900)
print("Animation download URL:", anim.output_model)
```

---

### Example 3: LOD generation (with multi-shot)

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

# Wait for all variants
results = [client.wait_model(mid, timeout=300) for mid in model_ids]
for r in results:
    print(r.model_id, r.output_model)
```

---

## Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)  # detailed request/response logs

# Or restrict to visvise loggers
logging.getLogger("visvise").setLevel(logging.INFO)
```

---

## License

MIT License
