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
export VISVISE_UID="your_uid"
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
