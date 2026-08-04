# VISVISE Weaver SDK - Examples

**[English](README_EN.md)** | 中文

每个文件对应一个 `gen_xxx` 方法的完整调用示例，同时可用作集成测试。

## 前置条件

```bash
pip install git+https://github.com/tencent-visvise/visvise-sdk-python.git
```

设置环境变量：

```bash
export VISVISE_APP_ID="your_app_id"
export VISVISE_SECRET_KEY="your_secret_key"
export VISVISE_RTX="your_rtx"
# 可选，默认线上生产环境
export VISVISE_ENV="prod"   # prod / test / dev
```

## 素材文件（assets/）

| 文件 | 用途 |
|---|---|
| `main_view.png` | 主视图图片（图生360/高模/中模/低模） |
| `back_view.png` | 背视图图片 |
| `left_view.png` | 左视图图片 |
| `right_view.png` | 右视图图片 |
| `high_model.fbx` | 高模 FBX（重拓扑/LOD/重布线/UV/贴图输入） |
| `rigging_model.fbx` | 骨骼架设输入模型 |
| `rigging_model.json` | 骨骼架设参数文件（参考，SDK 自动生成） |
| `skinning_model.fbx` | 蒙皮输入模型（带骨骼） |
| `skinning_model.json` | 蒙皮参数文件（参考，SDK 自动生成） |
| `animation_model.fbx` | 动画生成 / 图生Pose 输入模型 |
| `animation_video.mp4` | 视频生动画输入视频 |
| `pose_ref.png` | 图生Pose 参考图片 |

## 2D 预处理示例

`gen_preprocess.py` 分别通过 ``client.gen_style_transfer()`` 和 ``client.gen_patter_auto_remove()`` 同步执行风格化或智能去花纹并保存资产；最长可能需要 120 秒，示例使用 180 秒客户端超时。

| 环境变量 | 必填 | 说明 |
|---|---|---|
| `VISVISE_PREPROCESS_INPUT` | 是 | 本地图片路径或 VISVISE 平台 COS URL |
| `VISVISE_PREPROCESS_MODE` | 否 | `stylized`（默认）或 `auto-remove` |
| `VISVISE_PREPROCESS_STYLE` | 仅 `stylized` | `grayscale`（默认）、`pixel`、`realistic` 或 `cartoon` |
| `VISVISE_PREPROCESS_NAME` | 否 | 保存资产名称，默认 `example_gen_preprocess` |
| `VISVISE_PREPROCESS_ALGORITHM_MODEL` | 否 | 指定 2D 预处理模型；不传时自动选择首个可用模型 |
| `VISVISE_ENV` | 否 | `prod`（默认）、`test` 或 `dev` |

```bash
cd examples
python gen_preprocess.py
```

## 运行示例

```bash
cd examples

# 图生360
python gen_360.py

# 图生高模（需要先运行 gen_360.py 获取多视图输出）
python gen_high_model.py

# 重拓扑
python gen_retopology.py
```
