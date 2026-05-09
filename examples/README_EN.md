# VISVISE Weaver SDK - Examples

中文 | **[English](README_EN.md)**

Each file corresponds to a complete usage example for a `gen_xxx` method, and can also serve as integration tests.

## Prerequisites

```bash
pip install git+https://github.com/tencent-visvise/visvise-sdk-python.git@v1.0.1
```

Set environment variables:

```bash
export VISVISE_APP_ID="your_app_id"
export VISVISE_SECRET_KEY="your_secret_key"
export VISVISE_UID="your_uid"
# Optional, defaults to production
export VISVISE_ENV="prod"   # prod / test / dev
```

## Asset Files (assets/)

| File | Purpose |
|---|---|
| `main_view.png` | Main view image (gen_360 / high / mid / low model) |
| `back_view.png` | Back view image |
| `left_view.png` | Left view image |
| `right_view.png` | Right view image |
| `high_model.fbx` | High-poly FBX (retopology / LOD / mesh refine / UV / texture input) |
| `rigging_model.fbx` | Rigging input model |
| `skinning_model.fbx` | Skinning input model (with skeleton) |
| `animation_model.fbx` | Animation / Pose input model |
| `animation_video.mp4` | Video-to-animation input video |
| `pose_ref.png` | Pose reference image |

## Running Examples

```bash
cd examples

# Image to 360
python gen_360.py

# Image to high-poly (run gen_360.py first to get multi-view output)
python gen_high_model.py

# Retopology
python gen_retopology.py
```
