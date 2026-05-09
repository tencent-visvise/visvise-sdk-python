# VISVISE Weaver Python SDK

中文 | **[English](README_EN.md)**

> This is the English version. [Click here for Chinese (中文)](README.md).

VISVISE Weaver OpenAPI Python SDK, providing:

- All atomic API methods (1:1 mapping to OpenAPI endpoints)
- High-level `gen_xxx()` methods for each node type (auto-upload files + create tasks)
- `wait_model()` async polling method

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Client Initialization](#client-initialization)
- [Enum Constants](#enum-constants)
- [High-Level Methods](#high-level-methods)
- [Atomic API Methods](#atomic-api-methods)
- [Exceptions](#exceptions)

---

## Installation

Install directly from GitHub (includes COS upload dependency):

```bash
pip install git+https://github.com/tencent-visvise/visvise-sdk-python.git@v1.0.0
```

Or via SSH:

```bash
pip install git+ssh://git@github.com/tencent-visvise/visvise-sdk-python.git@v1.0.0
```

> **Note:** The COS SDK is included by default. Local file auto-upload works out of the box.

---

## Quick Start

```python
from visvise import VisviseClient, FaceType, OutputModelFormat

client = VisviseClient(
    app_id="your_app_id",
    secret_key="your_secret_key",
    uid="your_uid",
)

# Step 1: Generate 360 multi-view from a single image
mv_model_id = client.gen_360(
    main_view="character.png",          # Local file path, SDK auto-uploads
    name="my_360",
)

# Step 2: Wait for 360 generation to complete
mv_info = client.wait_model(mv_model_id, interval=3, timeout=300)
output_view = mv_info.image_gen_360_output.output_view

# Step 3: Generate high-poly model from multi-views
high_model_id = client.gen_high_model(
    main_view=output_view.main_view,
    back_view=output_view.back_view,
    left_view=output_view.left_view,
    right_view=output_view.right_view,
    output_model_format=OutputModelFormat.FBX,
    face_type=FaceType.TRIANGLE,
    face_num=500000,
)

# Step 4: Wait for high-poly model to complete
model_info = client.wait_model(high_model_id, timeout=900)
print("Output model:", model_info.output_model)
```

---

## Client Initialization

```python
from visvise import VisviseClient, Environment

client = VisviseClient(
    app_id="your_app_id",       # Required, assigned by platform
    secret_key="your_key",      # Required, assigned by platform
    uid="your_uid",             # Required, from your login account
    env=Environment.PROD,       # Optional, default production
    timeout=30,                 # Optional, HTTP timeout in seconds
)
```

| Parameter | Required | Description |
|---|---|---|
| `app_id` | Yes | Client ID assigned by platform |
| `secret_key` | Yes | Signing key assigned by platform |
| `uid` | Yes | User ID from your login account |
| `env` | No | `Environment.PROD` (default) / `.TEST` / `.DEV` or custom URL |
| `timeout` | No | HTTP request timeout in seconds, default 30 |

---

## Enum Constants

SDK provides enum constants to replace hard-coded values:

```python
from visvise import FaceType, DetailLevel, OutputModelFormat, MeshRefineMode

# Face type
FaceType.TRIANGLE  # 1 - Triangle faces
FaceType.QUAD      # 2 - Quad faces

# Detail level (for retopology)
DetailLevel.LOW    # 1
DetailLevel.MEDIUM # 2
DetailLevel.HIGH   # 3

# Output model format
OutputModelFormat.FBX  # "fbx"
OutputModelFormat.OBJ  # "obj"
OutputModelFormat.GLB  # "glb"

# Mesh refine mode
MeshRefineMode.OPTIMIZE  # 1 - Mesh optimization
MeshRefineMode.DENSIFY   # 2 - Mesh densification
```

---

## High-Level Methods

High-level methods wrap "COS file upload + async task creation". Pass local file paths or COS URLs, returns `model_id`.

> **About `algorithm_model`:** All gen_xxx methods accept an optional `algorithm_model`. If not provided, the SDK automatically fetches the first available model for the current account.

The following imports are used in all examples below:

```python
from visvise import (
    VisviseClient, Environment,
    FaceType, DetailLevel, OutputModelFormat, MeshRefineMode,
    ReduceFace, View,
)

client = VisviseClient(app_id="...", secret_key="...", uid="...")
```

| Method | Description | Example |
|---|---|---|
| `gen_360` | Image → 360 multi-view | [gen_360.py](examples/gen_360.py) |
| `gen_high_model` | Image → High-poly 3D (node_type=3) | [gen_high_model.py](examples/gen_high_model.py) |
| `gen_mid_model` | Image → Mid-poly 3D (node_type=11) | [gen_mid_model.py](examples/gen_mid_model.py) |
| `gen_low_model` | Image → Low-poly 3D (node_type=13) | [gen_low_model.py](examples/gen_low_model.py) |
| `gen_mesh_refine` | Mesh refinement (node_type=10) | [gen_mesh_refine.py](examples/gen_mesh_refine.py) |
| `gen_retopology` | Retopology (node_type=1) | [gen_retopology.py](examples/gen_retopology.py) |
| `gen_lod` | LOD generation (node_type=2) | [gen_lod.py](examples/gen_lod.py) |
| `gen_uv` | UV unwrap (node_type=9) | [gen_uv.py](examples/gen_uv.py) |
| `gen_texture` | Texture generation (node_type=8) | [gen_texture.py](examples/gen_texture.py) |
| `gen_rigging` | Auto rigging (node_type=5) | [gen_rigging.py](examples/gen_rigging.py) |
| `gen_skinning` | Auto skinning (node_type=6) | [gen_skinning.py](examples/gen_skinning.py) |
| `gen_video_motion` | Video → Animation (node_type=4) | [gen_video_motion.py](examples/gen_video_motion.py) |
| `gen_text_motion` | Text → Animation (node_type=4) | [gen_text_motion.py](examples/gen_text_motion.py) |
| `gen_pose` | Image → Pose (node_type=12) | [gen_pose.py](examples/gen_pose.py) |
| `wait_model` | Poll until task completes | — |

### Key Examples

```python
# Rigging - just pass a bare model file, SDK auto-packages into zip
model_id = client.gen_rigging(
    model_path="character.fbx",
    mesh_category="humanoid",     # "humanoid" or "tetrapod"
)

# Skinning - pass rigged model + mesh/joint names
model_id = client.gen_skinning(
    model_path="rigged_model.fbx",
    mesh_names=["Body_Mesh"],
    joint_names=["Bip001", "Bip001 Pelvis"],
)

# Retopology with enums
model_id = client.gen_retopology(
    model_path="model.fbx",
    output_model_format=OutputModelFormat.FBX,
    face_type=FaceType.QUAD,
    detail_level=DetailLevel.HIGH,
)

# LOD with multiple levels
model_ids = client.gen_lod(
    model_path="model.fbx",
    reduce_faces=[
        ReduceFace(reduce_level=1, reduce_percent=50, face_type=FaceType.QUAD),
        ReduceFace(reduce_level=2, reduce_percent=25, face_type=FaceType.QUAD),
    ],
    output_model_format=OutputModelFormat.FBX,
    gen_times=3,
)

# Wait for completion
model_info = client.wait_model(model_id, interval=2, timeout=600)
print(model_info.output_model)
```

---

## Atomic API Methods

Access low-level endpoints via `client.api.xxx()`:

```python
cred = client.api.get_cos_cred()
quota = client.api.get_user_quota()
models, total = client.api.get_model_list(model_id_list=["Model2026..."])
alg_models = client.api.list_algorithm_model(node_type=4, sub_type=1)
url = client.api.download_model("Model2026...")
client.api.delete_model("Model2026...")
client.api.batch_delete_model(["Model2026...", "Model2026..."])
out_url = client.api.remove_bg("https://cos.../image.png")
prompts = client.api.get_text2motion_prompt_list(language="en")
```

---

## Exceptions

All exceptions inherit from `WeaverError`:

| Exception | Error Code | Description |
|---|---|---|
| `WeaverError` | any | Base exception |
| `NetworkError` | — | Connection / timeout errors |
| `SignatureError` | 400 | Signature verification failed |
| `InvalidParamsError` | 120008 | Invalid request parameters |
| `PermissionDeniedError` | 120018 | Permission denied |
| `QuotaExceededError` | 120020 | Daily quota exceeded |
| `RateLimitError` | 120040 | Rate limit hit |
| `ModelGenerationError` | — | Model generation failed (status=4) |
| `PollingTimeoutError` | — | wait_model timed out |

```python
from visvise import WeaverError, QuotaExceededError, PollingTimeoutError

try:
    model_id = client.gen_360("image.png")
    model = client.wait_model(model_id)
except QuotaExceededError:
    print("Daily quota exceeded")
except PollingTimeoutError as e:
    print(f"Timeout: {e.model_id}, {e.timeout}s")
except WeaverError as e:
    print(f"API error [{e.code}]: {e.message}")
```

---

## License

MIT License
