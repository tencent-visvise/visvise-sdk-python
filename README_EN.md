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
  - [gen_style_transfer / gen_patter_auto_remove — 2D Preprocessing](#gen_style_transfer--gen_patter_auto_remove--2d-preprocessing)
  - [gen_high_model — Image to High-poly](#gen_high_model--image-to-high-poly)
  - [gen_mid_model — Image to Mid-poly](#gen_mid_model--image-to-mid-poly)
  - [gen_low_model — Image to Low-poly](#gen_low_model--image-to-low-poly)
  - [gen_mesh_refine — Mesh Refinement](#gen_mesh_refine--mesh-refinement)
  - [gen_retopology — Retopology](#gen_retopology--retopology)
  - [gen_rtp_connected— Retopology — Connected](#gen_rtp_connected-retopology--connected)
  - [gen_lod — LOD](#gen_lod--lod)
  - [gen_uv — UV Unwrap](#gen_uv--uv-unwrap)
  - [gen_texture — Texture Generation](#gen_texture--texture-generation)
  - [gen_rigging — Rigging](#gen_rigging--rigging)
  - [gen_skinning — Skinning](#gen_skinning--skinning)
  - [gen_video_motion — Video to Animation](#gen_video_motion--video-to-animation)
  - [gen_text_motion — Text to Animation](#gen_text_motion--text-to-animation)
  - [gen_pose — Image to Pose](#gen_pose--image-to-pose)
  - [gen_segment_2d — 2D Segmentation](#gen_segment_2d--2d-segmentation)
  - [cond_part_autofit — Nude Model Split](#cond_part_autofit--nude-model-split)
  - [model_auto_merge — Model Auto Merge](#model_auto_merge--model-auto-merge)
  - [wait_model — Wait for Completion](#wait_model--wait-for-completion)
  - [image_cutout — Image Cutout](#image_cutout--image-cutout)
- [Atomic API Methods](#atomic-api-methods)
- [Exceptions](#exceptions)
- [Full Workflow Examples](#full-workflow-examples)

---

## Installation

Install directly from the GitHub repository (Tencent Cloud COS dependency included):

```bash
pip install git+https://github.com/tencent-visvise/visvise-sdk-python.git@v1.2.4
```

Or via SSH:

```bash
pip install git+ssh://git@github.com/tencent-visvise/visvise-sdk-python.git@v1.2.4
```

> **Note:** The Tencent Cloud COS SDK is bundled by default; local file auto-upload works out of the box.

---

## Quick Start

```python
from visvise import VisviseClient, FaceType, OutputModelFormat

client = VisviseClient(
    app_id="your_app_id",
    secret_key="your_secret_key",
)

# 1) Image-to-360: upload local image, generate multi-views
mv_model_id = client.gen_360(
    main_view="character.png",          # local path, SDK uploads automatically
    name="my_360",
    rtx="caller_rtx",
)

# 2) Wait for completion, fetch multi-view output
mv_info = client.wait_model(mv_model_id, interval=3, timeout=300, rtx="caller_rtx")
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
    rtx="caller_rtx",
)

# 4) Wait for completion
model_info = client.wait_model(high_model_id, timeout=900, rtx="caller_rtx")
print("Output model:", model_info.output_model)
```

---

## Client Initialization

```python
from visvise import VisviseClient, Environment

client = VisviseClient(
    app_id="your_app_id",       # required, assigned by platform
    secret_key="your_key",      # required, assigned by platform
    env=Environment.PROD,       # optional, default: production
    timeout=30,                 # optional, per-request HTTP timeout in seconds (default 30)
)
```

| Parameter | Required | Description |
|---|---|---|
| `app_id` | ✅ | Client identifier assigned by the platform |
| `secret_key` | ✅ | Signing key assigned by the platform |
| `env` | — | Environment: `Environment.PROD` (default) / `Environment.TEST` / `Environment.DEV` or a custom URL |
| `timeout` | — | Per-request HTTP timeout in seconds (default 30) |

> **About the `rtx` parameter**: every API call requires an `rtx` argument (the actual user's RTX company account); it is **not** bound at client construction time.
> Per company policy, **internal users MUST pass the actual end-user's RTX** — using a shared / project account is not allowed. External users may pass any business identifier.

---

## Enum Constants

The SDK exposes the following enum constants. Prefer them over hard-coded numbers/strings:

```python
from visvise import (
    FaceType, DetailLevel, OutputModelFormat, MeshRefineMode,
    SegmentSplitType, ImageGen360Style,
    NodeType, PreprocessType, StyleParam, StyleType,
    ImageCutoutMode,
)

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


# Image-to-360 style (VISVISE proprietary models only; any other value will be rejected)
ImageGen360Style.GRAY_MODEL  # "灰模"      - gray model
ImageGen360Style.PHOTOREAL   # "超写实"    - photoreal
ImageGen360Style.Q_TOON      # "Q版卡通"  - Q-style toon
ImageGen360Style.PIXEL       # "像素风格" - pixel art

# 2D preprocessing
PreprocessType.STYLIZED      # 1 - style transfer
PreprocessType.PATTERNED     # 2 - automatic pattern removal

# Stylized
StyleType.GRAYSCALE          # 1 - grayscale
StyleType.PIXEL              # 2 - pixel art
StyleType.REALISTIC          # 3 - realistic
StyleType.CARTOON            # 4 - cartoon figurine

# Image cutout mode
ImageCutoutMode.DIRECT        # 1 - direct cutout (transparent background, default)
ImageCutoutMode.SOLID_COLOR   # 2 - cutout with solid-color background
ImageCutoutMode.REPLACE       # 3 - cutout and replace the background
```

---

## High-Level Methods

High-level methods bundle "COS upload + task creation" into a single call. Pass either a local file path or a VISVISE COS URL; each method returns a `model_id`. `gen_style_transfer` / `gen_patter_auto_remove` are synchronous; other `gen_xxx()` methods usually create asynchronous tasks.

`cond_part_autofit` (nude model split) and `model_auto_merge` (model auto merge) are also **synchronous**: they return the processed result object directly, **do not create a model asset**, and need no `wait_model()` call.

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
    SegmentSplitType,
    StyleType, ReduceFace, View,
)

client = VisviseClient(app_id="...", secret_key="...")
```

### gen_360 — Image to 360

Generate 360-degree multi-views from a single image. → [Example](examples/gen_360.py)

```python
model_id = client.gen_360(
    main_view="path/to/character.png",   # required, main view (local path or VISVISE COS URL)
    algorithm_model=None,                # optional, e.g. "hunyuan3D-MultiView-v3.0"; auto-selected if omitted
    name="gen_360",                      # optional, task name
    enable_a_pose=None,                  # optional, enable A-Pose (True/False)
    prompt=None,                         # optional, text prompt
    style=None,                          # optional, style (VISVISE proprietary models only). Must be one of ImageGen360Style: GRAY_MODEL/PHOTOREAL/Q_TOON/PIXEL — any other value will be rejected
    enable_head_refinement=None,         # optional, enable head (face) refinement
    aspect_ratio=None,                   # optional, aspect ratio, e.g. "1:1"
    enable_background_removal=None,      # optional, enable background removal
    seed=None,                           # optional, random seed (auto-generated by the algorithm if omitted)
    enable_15deg=None,                   # optional, enable perspective correction
    extra_references=None,               # optional, reference images (ImageGen360ExtraReference), uploaded to COS automatically
    revision=None,                       # optional, revision params (ImageGen360Revision), views uploaded to COS automatically
    back_view=None,                      # optional, back view to improve quality
    left_view=None,                      # optional, left view
    right_view=None,                     # optional, right view,
    rtx="caller_rtx",
)
```

> Optional parameters map one-to-one to the backend `ImageGen360Params`; the SDK does not validate them, the server does.
>
> **Reference images and revision**:
>
> ```python
> from visvise import ImageGen360ExtraReference, ImageGen360Revision, ImageGen360RevisionViews
>
> model_id = client.gen_360(
>     main_view="character.png",
>     extra_references=[
>         ImageGen360ExtraReference(path="ref.png", prompt="reference image description"),
>     ],
>     revision=ImageGen360Revision(
>         caption="the full caption returned by the previous call (pass it back as-is)",
>         prompt="the modification instruction for this round",
>         views=ImageGen360RevisionViews(main_view="m.png", back_view="b.png"),
>     ),
>     rtx="caller_rtx",
> )
> ```
>
> `revision.views` supports four views (main / back / left / right); empty ones are not sent.

---

### gen_style_transfer / gen_patter_auto_remove — 2D Preprocessing

Synchronously processes an input image and saves it as a `node_type=16` asset. It returns the `model_id` directly; `wait_model()` is not required. → [Example](examples/gen_preprocess.py)

```python
# Style transfer
styled_id = client.gen_style_transfer(
    input_view="character.png",                    # required, local path, VISVISE COS URL, bytes, or BinaryIO input image
    style_type=StyleType.GRAYSCALE,                 # optional, grayscale (default), pixel, realistic, or cartoon
    algorithm_model="VISVISE-Pre2D-V1.0.0",         # optional, algorithm model; use None to select the first available model
    name="styled_character",                         # optional, asset name; default "gen_style_transfer"
    rtx="caller_rtx",                               # required, actual caller's RTX
)

# Automatic pattern removal
patterned_id = client.gen_patter_auto_remove(
    input_view="character.png",                    # required, local path, VISVISE COS URL, bytes, or BinaryIO input image
    algorithm_model="VISVISE-Pre2D-V1.0.0",         # optional, algorithm model; use None to select the first available model
    name="pattern_removed_character",                # optional, asset name; default "gen_patter_auto_remove"
    rtx="caller_rtx",                               # required, actual caller's RTX
)
```

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
    right_view=None,                               # optional, right view,
    rtx="caller_rtx",
)
```

---

### gen_mid_model — Image to Mid-poly

Mid-poly generation requires all four views (node_type=11). → [Example](examples/gen_mid_model.py)

```python
model_id = client.gen_mid_model(
    main_view="path/to/main.png",                 # required if uploading original art view
    back_view="path/to/back.png",                 # optional
    left_view="path/to/left.png",                 # optional
    right_view="path/to/right.png",               # optional
    algorithm_model=None,                         # optional, e.g. "VISVISE-MeshGen-V1.0.0"; auto-selected if omitted
    output_model_format=OutputModelFormat.FBX,    # optional, output format (default fbx)
    face_type=FaceType.TRIANGLE,                  # optional, face type
    name="gen_mid_model",                         # optional, task name
    face_num=None,                                # optional, target face count (0-30000, 0 = default), auto if omitted
    model_size=None,                              # optional, expected model size in cm (mid-poly only, default 100.0, must be > 0)
    segment_model_id=None,                        # optional, 2D segmentation asset ID (mid-poly only), generate from 2D segmentation result
    model_id_360=None,                            # optional, gen_360 asset ID, generate from gen_360 result
    group_ids=None,                               # optional, custom part-group NPZ file
    part_mesh_path=None,                          # optional, OBJ file containing all parts
    label_to_id=None,                             # optional, JSON file containing the part-name-to-ID mapping
    rtx="caller_rtx",
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
    face_num=None,                                 # optional, target face count (100~60000); auto if omitted
    back_view=None,                                # optional, back view
    left_view=None,                                # optional, left view
    right_view=None,                               # optional, right view,
    rtx="caller_rtx",
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
    face_num=None,                                 # optional, target face count (optimize mode only, (0,50000], 0 = auto)
    color_model=None,                              # optional, colored model used to attach color info,
    rtx="caller_rtx",
)
```

---

### gen_retopology — Retopology

Retopology of high-poly models (node_type=1). → [Example](examples/gen_retopology.py)

> Note: pass `detail_level` for Hunyuan models, `face_num` for VISVISE proprietary models — choose one.
>
> VISVISE proprietary (VV) models are **two-stage**: first run [Retopology — Connected](#gen_rtp_connected-retopology--connected) to produce the connected-component artifact, edit it on the frontend, save it, then use the saved connected-component asset ID as `parent_model_id` for this node.

```python
# Hunyuan model example
model_id = client.gen_retopology(
    model_path="path/to/model.fbx",               # required, input model
    algorithm_model=None,                          # optional, e.g. "hunyuan3D-RTP-v1.5" / "VISVISE-RTP-V1.0.0"
    output_model_format=OutputModelFormat.FBX,    # optional, output format
    face_type=FaceType.QUAD,                      # optional, face type (default quad)
    name="gen_retopology",                         # optional, task name
    detail_level=DetailLevel.HIGH,                # optional (required by Hunyuan): DetailLevel.LOW/MEDIUM/HIGH
    face_num=None,                                 # optional (required by VISVISE proprietary): target face count
    smooth_strength=None,                          # optional, smoothing strength: 0.0 (no smoothing) / 1.0 (full smoothing), default 1.0
    parent_model_id=None,                          # optional (required for two-stage VV): saved connected-component asset ID
    rtx="caller_rtx",
)

# VISVISE proprietary model example (two-stage: parent_model_id points to the saved connected-component asset)
model_id = client.gen_retopology(
    model_path="path/to/edited_connected.zip",
    algorithm_model="VV-RTP-V1.5.0",
    face_num=10000,                                 # optional, VISVISE proprietary
    smooth_strength=1.0,
    parent_model_id="Model2026112700098765",        # optional, required for two-stage VV
    rtx="caller_rtx",
)
```

---

### gen_rtp_connected— Retopology — Connected

The first stage of the two-stage VISVISE proprietary (VV) retopology: group a high-poly model into connected components (node_type=19), producing the component meshes and the grouping data. → [Example](examples/gen_rtp_connected.py)

Call flow:

1. `gen_rtp_connected` creates the grouping task (async); the artifact is the asset's `output_model` (zip);
2. Download and edit the connected-component grouping on the frontend, repack it into a zip and upload it to your own COS directory;
3. `save_rtp_connected` saves that artifact (**synchronous**), returning a new connected-component asset ID (`node_type=19`, `status=3`);
4. Use that ID as the `parent_model_id` of `gen_retopology` for the second stage.

```python
# Stage 1: create the connected-component grouping task
connected_id = client.gen_rtp_connected(
    model_path="path/to/model.fbx",     # required, input model (raw models are zipped by the SDK)
    algorithm_model=None,               # optional, algorithm model; auto-selected if omitted
    name="my_rtp_connected",             # optional, task name
    rtx="caller_rtx",
)

# Wait for completion, download output_model (the grouping artifact zip) and edit it on the frontend
connected = client.wait_model(connected_id, timeout=900, rtx="caller_rtx")

# Save the edited artifact (a local zip is uploaded to your own COS directory automatically)
saved_id = client.save_rtp_connected(
    connected_id,                        # required, first-stage (grouping) asset ID
    "path/to/edited_connected.zip",      # required, artifact zip (local path / COS URL / bytes)
    "my_connected",                      # required, name of the new asset
    rtx="caller_rtx",
)

# Stage 2: retopology (parent_model_id points to the saved connected-component asset)
rtp_id = client.gen_retopology(
    "path/to/edited_connected.zip",
    algorithm_model="VV-RTP-V1.5.0",
    face_num=10000,
    parent_model_id=saved_id,
    rtx="caller_rtx",
)
```

> All parameter validation (ownership/status of `model_id`, `output_model` must be a `.zip` under your own COS directory, etc.) is done by the server; the SDK only forwards parameters and uploads files.

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
    gen_times=3,                                   # optional, number of variants (use 1 to disable multi-shot),
    rtx="caller_rtx",
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
    enable_auto_smoothing=None,                    # optional, enable auto-smoothing,
    rtx="caller_rtx",
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
    prompt=None,                                   # optional, text prompt for the texture,
    rtx="caller_rtx",
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
    mesh_names=None,                               # optional, mesh names list to rig
    generate_root=False,                           # optional, whether to generate root bone (default False)
    temperature=-1,                                # optional, advanced sampling - freedom, range 0~1 (default -1)
    num_beams=-1,                                  # optional, advanced sampling - search breadth, range 5~15 (default -1)
    algo_scenario=None,                            # optional, generation mode (only for mesh_category=humanoid):
                                                   #   1 = default one-click auto generation
                                                   #   2 = humanoid + template (requires template_skeleton)
                                                   #   3 = main body humanoid rig with additional bones
    rtx="caller_rtx",
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
    name="gen_skinning",                           # optional, task name,
    rtx="caller_rtx",
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
    rotate_axis_angle=None,                        # optional, rotation axis-angle [x, y, z] (radians),
    rtx="caller_rtx",
)
```

---

### gen_text_motion — Text to Animation

Generate animation from text prompts (node_type=4); returns 1 model_id (a single model contains 4 candidates).
Supports two modes: multi-prompt `segments` (takes priority when non-empty) and single `prompt` (fallback). → [Example](examples/gen_text_motion.py)

```python
from visvise import MotionSegment

# Mode 1: multi-prompt segments (1~15 segments)
model_ids = client.gen_text_motion(
    model_path="path/to/model.zip",               # required, model zip
    segments=[
        MotionSegment(text="Raise the right hand slowly", num_frames=60),
        MotionSegment(text="Walk two steps forward", num_frames=90, overlap_frames_with_prev=10),
    ],
    algorithm_model="MotusAI-T2M-V1.5",           # optional, e.g. "MotusAI-T2M-V1.5"
    output_model_format=OutputModelFormat.FBX,    # optional, output format
    name="gen_text_motion",                        # optional, task name
    enable_rewrite=None,                          # optional, enable rewrite (default True)
    enable_loop=None,                             # optional, loop playback
    loop_frames=None,                             # optional, loop frames (1~20, only meaningful when enable_loop=True),
    rtx="caller_rtx",
)

# Mode 2: single prompt (fallback when segments is empty)
model_ids = client.gen_text_motion(
    model_path="path/to/model.zip",
    prompt="a person breakdancing",                # single animation prompt
    algorithm_model=None,                          # optional, e.g. "MotusAI-T2M-V1.5"
    output_model_format=OutputModelFormat.FBX,
    name="gen_text_motion",
    duration=None,                                 # optional, duration in seconds (single-prompt mode only)
    rtx="caller_rtx",
)
# model_ids usually contains 1 ID; a single model holds multiple candidates
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
    name="gen_pose",                               # optional, task name,
    rtx="caller_rtx",
)
```

---

### gen_segment_2d — 2D Segmentation

Component segmentation over multi-views from gen_360 (node_type=14, SSE protocol). The resulting `model_id` can be passed as `segment_model_id` for `gen_mid_model` / `gen_low_model`. → [Example](examples/gen_segment_2d.py)

Gen360 can also be skipped: upload local artwork directly (six views as needed, local paths are
uploaded to COS automatically) with `skip_360_preprocess=True`, optionally
`skip_remove_background=True`. → [Example](examples/gen_segment_2d_skip360.py)

```python
def on_thinking(content: str):
    print("[thinking]", content)

seg_model_id = client.gen_segment_2d(
    model_id_360="Model202604xxxxxx",             # required (or pass input_view), the gen_360 model_id
    algorithm_model=None,                          # optional, e.g. "VISVISE-Seg2D-V1.0.0"
    name="gen_segment_2d",                         # optional, task name
    input_view=None,                               # optional (or pass model_id_360), input view
    split_type=None,                               # optional, SegmentSplitType.FRONT_VIEW(1, default) / FOUR_VIEW(2, multi-view)
    skip_360_preprocess=None,                      # optional, skip 360 preprocess, default False
    skip_remove_background=None,                   # optional, skip background removal (default False; only effective when skip_360_preprocess=True)
    decomposition_plan=None,                       # optional, decomposition plan (json file), local path uploaded automatically; omitted when empty
    on_thinking=on_thinking,                       # optional, callback for thinking events,
    rtx="caller_rtx",
)
# Use the result as segment_model_id for gen_mid_model / gen_low_model
mid_id = client.gen_mid_model(..., segment_model_id=seg_model_id, rtx="caller_rtx")
```

---

### cond_part_autofit — Nude Model Split

Replaces the specified parts of the original model with the corresponding **nude models**
(e.g. a headless body nude model) and outputs the merged model. **Synchronous** interface:
it only returns the processed model and **does not create a model asset**, so there is no
need to call `wait_model()`.

> ⚠️ The server-side algorithm runs for up to 5 minutes. Set the client `timeout` to at least
> 330 seconds: `VisviseClient(app_id, secret_key, timeout=330)`

| Parameter | Required | Description |
|---|---|---|
| `original_part_mesh_path` | ✅ | COS path of the original model (local path / bytes are uploaded by the SDK); must be under the caller's own COS directory |
| `ref_mesh_path` | ✅ | COS path of the reference model (local path / bytes are uploaded by the SDK) |
| `replace_part_names` | — | Part name → nude model file name mapping, e.g. `{"无头身体裸模": "female_headless.obj"}`; omit to replace nothing |
| `rtx` | ✅ | The RTX of the actual user |

**Returns** `CondPartAutofitResult`:

| Field | Description |
|---|---|
| `output_obj_path` | COS URL of the merged obj (temporary signature, valid for 24h) |
| `background_color` | Final background color (English color name); empty when the algorithm returns none |

```python
result = client.cond_part_autofit(
    original_part_mesh_path="path/to/original_model.obj",   # required, original model (local path is uploaded automatically)
    ref_mesh_path="path/to/ref_model.obj",                  # required, reference model (local path is uploaded automatically)
    replace_part_names={"无头身体裸模": "female_headless.obj"},  # optional, part name → nude model file name
    rtx="caller_rtx",
)
print(result.output_obj_path)    # COS URL of the merged obj (temporary signature, valid for 24h)
print(result.background_color)   # final background color (English color name)
```

---

### model_auto_merge — Model Auto Merge

Merges multiple part meshes into one complete model (mid-poly / high-poly), optionally using
a reference model to fill in the parts missing from the original part package. **Synchronous**
interface: it only returns the processed model and **does not create a model asset**.

> ⚠️ The server-side algorithm runs for up to 5 minutes; set the client `timeout` to at least 330 seconds.
> ⚠️ `original_part_mesh_path` must end with `.zip` (a part package), otherwise the server
> returns `120008`; the SDK does not enforce this.

| Parameter | Required | Description |
|---|---|---|
| `original_part_mesh_path` | ✅ | Path to the zipped part mesh package (local path / bytes are uploaded by the SDK) |
| `ref_mesh_path` | — | Reference model obj (local path / bytes are uploaded by the SDK); when provided, the algorithm fills in the missing parts from it |
| `support_rotate` | — | Whether rotation is supported, default `False` |
| `rtx` | ✅ | The RTX of the actual user |

**Returns** `ModelAutoMergeResult`:

| Field | Description |
|---|---|
| `output_obj_path` | COS URL of the merged model (temporary signature, valid for 24h) |
| `elapsed_time` | Algorithm elapsed seconds |
| `ref_filled_parts` | Part names filled in from the reference model; empty when `ref_mesh_path` is omitted |
| `part_bbox_iou` | Part name → bbox IoU against the reference part |
| `mean_bbox_iou` | Mean bbox IoU of all parts (closer to 1 means a better fit) |

```python
result = client.model_auto_merge(
    original_part_mesh_path="path/to/parts.zip",   # required, part mesh package (local path is uploaded automatically)
    ref_mesh_path="path/to/ref_model.obj",          # optional, reference model used to fill in missing parts
    support_rotate=False,                           # optional, whether rotation is supported (default False)
    rtx="caller_rtx",
)
print(result.output_obj_path)    # COS URL of the merged model (temporary signature, valid for 24h)
print(result.elapsed_time)       # algorithm elapsed seconds
print(result.ref_filled_parts)   # part names filled in from the reference model
print(result.part_bbox_iou)      # part name → bbox IoU
print(result.mean_bbox_iou)      # mean bbox IoU
```

---

### wait_model — Wait for Completion

Poll until an async task finishes; returns `ModelInfo`.

```python
model_info = client.wait_model(
    model_id="Model2026033100192028",
    interval=2,     # poll interval in seconds (default 2)
    timeout=600,    # max wait in seconds (default 600),
    rtx="caller_rtx",
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

### image_cutout — Image Cutout

Removes the background of the given images. Three modes are supported: **direct cutout**,
**cutout with a solid-color background**, and **cutout with a replaced background**.
This is a synchronous endpoint: it only returns the processed images and **creates no model asset**.
→ [Example code](examples/image_cutout.py)

```python
# Cutout is synchronous and may take minutes on the server — raise the client timeout
client = VisviseClient(app_id="...", secret_key="...", timeout=300)

result = client.image_cutout(
    images=[                              # required, images to process (local path / VISVISE COS URL / bytes / BinaryIO)
        "path/to/character.png",
        "path/to/character_2.png",
    ],
    mode=ImageCutoutMode.DIRECT,           # optional, default 1 (direct cutout, transparent background)
    background_color="white",              # optional, background color name, default "white"
    rtx="caller_rtx",
)

print(result.image_list)         # processed image URLs (temporary signature, valid for 24h)
print(result.background_color)   # final background color
```

> **Notes:**
> 1. Input images must live in the caller's own COS directory; local paths / bytes are uploaded
>    to the current account directory by the SDK.
> 2. This is a synchronous endpoint — set the client `timeout` to at least 300 seconds
>    (the default 30s will time out).
> 3. Result URLs carry a temporary signature valid for 24h; keep the query string intact.

---

## Atomic API Methods

Access low-level endpoints via `client.api.xxx(rtx="caller_rtx")`:

```python
# Get temporary upload credentials
cred = client.api.get_cos_cred(rtx="caller_rtx")

# Query remaining quota
quota = client.api.get_user_quota(rtx="caller_rtx")
print(quota.model_quota)  # remaining model count
print(quota.animation_quota)  # remaining animation count

# Fetch model list
models, total = client.api.get_model_list(
    model_id_list=["Model2026..."],
    rtx="caller_rtx",
)

# Fetch algorithm models for a node type
alg_models = client.api.list_algorithm_model(node_type=4, sub_type=1, rtx="caller_rtx")

# Get download URL
url = client.api.download_model("Model2026...", rtx="caller_rtx")

# Delete a single model
client.api.delete_model("Model2026...", rtx="caller_rtx")

# Batch delete
client.api.batch_delete_model(["Model2026...", "Model2026..."], rtx="caller_rtx")

# Remove background
out_url = client.api.remove_bg("https://cos.../image.png", rtx="caller_rtx")

# Image cutout (atomic API, image_list must be VISVISE COS URLs already uploaded)
cutout = client.api.image_cutout(
    ["https://cos.../image.png"],
    ImageCutoutMode.DIRECT,     # 1 direct cutout / 2 solid-color background / 3 replace background
    "white",                    # background color name
    rtx="caller_rtx",
)
print(cutout.image_list)        # processed image URLs
print(cutout.background_color)  # final background color

# Text-to-motion prompt suggestions
prompts = client.api.get_text2motion_prompt_list(language="en", rtx="caller_rtx")

# Nude model split (synchronous)
nude = client.api.cond_part_autofit(
    original_part_mesh_path="https://cos.../original_model.obj",
    ref_mesh_path="https://cos.../ref_model.obj",
    replace_part_names={"无头身体裸模": "female_headless.obj"},
    rtx="caller_rtx",
)
print(nude.output_obj_path)     # dict-style access also works: nude["output_obj_path"]

# Model auto merge (synchronous)
merged = client.api.model_auto_merge(
    original_part_mesh_path="https://cos.../parts.zip",
    ref_mesh_path="https://cos.../ref_model.obj",
    support_rotate=False,
    rtx="caller_rtx",
)
print(merged.mean_bbox_iou)

# Save the retopology-connected artifact (synchronous endpoint)
result = client.api.save_rtp_connected(
    "Model2026...",                       # first-stage (connected-component grouping) asset ID
    "https://cos.../edited_connected.zip",  # artifact zip (must live under your own COS directory)
    "my_connected",                        # name of the new asset
    rtx="caller_rtx",
)
print(result.model_id)  # the new connected-component asset ID (node_type=19)
```

---

## Exceptions

All SDK exceptions inherit from `WeaverError`; you can catch the base class or any subclass.

| Exception | Code | Description |
|---|---|---|
| `WeaverError` | any | Base exception |
| `NetworkError` | — | Connection / timeout errors |
| `SignatureError` | 410 | Signature failure |
| `SignatureExpiredError` | 411 | Signature expired (clock skew between client and server) |
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
    model_id = client.gen_360("image.png", rtx="caller_rtx")
    model = client.wait_model(model_id, rtx="caller_rtx")
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

client = VisviseClient(app_id="...", secret_key="...")

# Step 1: Image-to-360
print("Step 1: generating multi-views...")
mv_id = client.gen_360(main_view="character.png", rtx="caller_rtx")
mv = client.wait_model(mv_id, interval=3, timeout=300, rtx="caller_rtx")
views = mv.image_gen_360_output.output_view

# Step 2: High-poly model
print("Step 2: generating high-poly model...")
high_id = client.gen_high_model(
    main_view=views.main_view,
    back_view=views.back_view,
    left_view=views.left_view,
    right_view=views.right_view,
    face_type=FaceType.TRIANGLE,
    rtx="caller_rtx",
)
high_model = client.wait_model(high_id, timeout=900, rtx="caller_rtx")
print("High-poly download URL:", high_model.output_model)
```

---

### Example 2: Animation pipeline (Rigging → Skinning → Animation)

```python
from visvise import VisviseClient, OutputModelFormat

client = VisviseClient(app_id="...", secret_key="...")

# Step 1: Rigging (pass raw model — SDK auto-zips)
rig_id = client.gen_rigging(
    model_path="character.fbx",
    mesh_category="humanoid",
    rtx="caller_rtx",
)
rig = client.wait_model(rig_id, timeout=600, rtx="caller_rtx")
print("Rigged model:", rig.output_model)

# Step 2: Skinning (pass rigged model)
skin_id = client.gen_skinning(
    model_path="rigged_character.fbx",
    mesh_names=["Body_Mesh"],
    joint_names=["Bip001", "Bip001 Pelvis"],
    rtx="caller_rtx",
)
skin = client.wait_model(skin_id, timeout=600, rtx="caller_rtx")

# Step 3: Video-to-animation
anim_id = client.gen_video_motion(
    model_path="skinned_model.zip",
    video_path="dance.mp4",
    output_model_format=OutputModelFormat.FBX,
    with_hand=True,
    rtx="caller_rtx",
)
anim = client.wait_model(anim_id, timeout=900, rtx="caller_rtx")
print("Animation download URL:", anim.output_model)
```

---

### Example 3: LOD generation (with multi-shot)

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

# Wait for all variants
results = [client.wait_model(mid, timeout=300, rtx="caller_rtx") for mid in model_ids]
for r in results:
    print(r.model_id, r.output_model)
```

---

### Example 4: Nude model split → Model auto merge

Both interfaces are synchronous and return the processed model directly — no model asset is
created and `wait_model()` is not needed.

```python
from visvise import VisviseClient

# The server-side algorithm runs for up to 5 minutes → widen the client timeout
client = VisviseClient(app_id="...", secret_key="...", timeout=330)

# Step 1: Nude model split — replace the given parts with the nude models
nude = client.cond_part_autofit(
    original_part_mesh_path="original_model.obj",              # local path, uploaded automatically
    ref_mesh_path="ref_model.obj",                             # local path, uploaded automatically
    replace_part_names={"无头身体裸模": "female_headless.obj"}, # part name → nude model file name
    rtx="caller_rtx",
)
print("Split result:", nude.output_obj_path)
print("Background color:", nude.background_color)

# Step 2: Model auto merge — merge the part meshes, filling in missing parts from the reference
merged = client.model_auto_merge(
    original_part_mesh_path="parts.zip",      # zipped part meshes, uploaded automatically
    ref_mesh_path="ref_model.obj",            # optional reference model
    support_rotate=False,
    rtx="caller_rtx",
)
print("Merged model:", merged.output_obj_path)
print("Elapsed:", merged.elapsed_time, "s")
print("Parts filled from reference:", merged.ref_filled_parts)
print("Mean bbox IoU:", merged.mean_bbox_iou)
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
