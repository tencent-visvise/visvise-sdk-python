# VISVISE Weaver SDK - Examples

中文 | **[English](README_EN.md)**

Each file corresponds to a complete usage example for a `gen_xxx` method, and can also serve as integration tests.

## Prerequisites

```bash
pip install git+https://github.com/tencent-visvise/visvise-sdk-python.git
```

Set environment variables:

```bash
export VISVISE_APP_ID="your_app_id"
export VISVISE_SECRET_KEY="your_secret_key"
export VISVISE_RTX="your_rtx"
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

## 2D Preprocess Example

`gen_preprocess.py` synchronously runs style transfer (via ``client.gen_style_transfer()``) or automatic pattern removal (via ``client.gen_patter_auto_remove()``) and saves an asset. It can take up to 120 seconds; the example uses a 180-second client timeout.

| Environment variable | Required | Description |
|---|---|---|
| `VISVISE_PREPROCESS_INPUT` | Yes | Local image path or VISVISE platform COS URL |
| `VISVISE_PREPROCESS_MODE` | No | `stylized` (default) or `auto-remove` |
| `VISVISE_PREPROCESS_STYLE` | `stylized` only | `grayscale` (default), `pixel`, `realistic`, or `cartoon` |
| `VISVISE_PREPROCESS_NAME` | No | Asset name; defaults to `example_gen_preprocess` |
| `VISVISE_PREPROCESS_ALGORITHM_MODEL` | No | Explicit 2D preprocess model; auto-selects the first available model when omitted |
| `VISVISE_ENV` | No | `prod` (default), `test`, or `dev` |

```bash
cd examples
python gen_preprocess.py
```

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
