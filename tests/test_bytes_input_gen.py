"""使用 bytes 二进制输入实际调用几个 gen_xxx 接口，验证：
1. SDK 自动嗅探后缀（不再用 .bin）
2. 任务能正常提交并返回 model_id
3. （可选）轮询任务状态直到 SUCCESS 或 RUNNING

对接开发环境（DEV）。
"""

import logging
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from visvise import VisviseClient, Environment, OutputModelFormat, FaceType, DetailLevel
from visvise.models import ReduceFace

# 调高日志方便观察 SDK 上传时使用的文件名
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
)

APP_ID     = "vsa_fca6bd1f7254476c"
SECRET_KEY = "vss_d375e248b3ecd3b4cd66d30a00492189cc997db97ad0edbb"
UID        = "willzhen"
ASSETS     = Path(__file__).parent / "assets"

client = VisviseClient(APP_ID, SECRET_KEY, UID, env=Environment.DEV)


def read_bytes(p: str) -> bytes:
    return (ASSETS / p).read_bytes()


results: list[tuple[str, str, str]] = []


def ok(name: str, detail: str = "") -> None:
    results.append(("PASS", name, detail))
    print(f"\n✅ PASS [{name}] {detail}\n")


def fail(name: str, reason: str) -> None:
    results.append(("FAIL", name, reason))
    print(f"\n❌ FAIL [{name}] {reason}\n")


def run(name: str, fn) -> None:
    print(f"\n━━━━━ {name} ━━━━━")
    try:
        result = fn()
        if isinstance(result, list):
            ok(name, f"model_ids={result}")
        else:
            ok(name, f"model_id={result}")
    except Exception as e:
        fail(name, f"{type(e).__name__}: {e}")


# ──────────────────────────────────────────────────────────────────────
# 测试用例：使用 bytes 输入
# ──────────────────────────────────────────────────────────────────────

print("=" * 70)
print(" 二进制输入 + 自动嗅探后缀，实际提交 gen_xxx 任务（DEV 环境）")
print("=" * 70)

# 1. gen_360：纯 bytes 输入 PNG → 应识别为 .png
run("gen_360 (PNG bytes)", lambda: client.gen_360(
    main_view=read_bytes("main_view.png"),
    name="sniff_test_gen_360",
))

# 2. gen_high_model：四视图（主视图必传，背/左/右可选），全用 bytes
run("gen_high_model (4×PNG bytes)", lambda: client.gen_high_model(
    main_view=read_bytes("main_view.png"),
    back_view=read_bytes("back_view.png"),
    left_view=read_bytes("left_view.png"),
    right_view=read_bytes("right_view.png"),
    output_model_format=OutputModelFormat.FBX,
    face_type=FaceType.TRIANGLE,
    name="sniff_test_gen_high",
))

# 3. gen_retopology：模型 bytes 输入 FBX → 应识别为 .fbx 并打包 zip
#    自动选到的是 hunyuan3D-RTP-v1.5（混元），必须用 detail_level（不是 face_num）
run("gen_retopology (FBX bytes)", lambda: client.gen_retopology(
    model_path=read_bytes("rigging_model.fbx"),  # 用小一点的 fbx
    output_model_format=OutputModelFormat.FBX,
    face_type=FaceType.QUAD,
    detail_level=DetailLevel.MEDIUM,
    name="sniff_test_gen_retop",
))

# 4. gen_uv：OBJ bytes 输入 → 应识别为 .obj 并打包 zip
run("gen_uv (OBJ bytes)", lambda: client.gen_uv(
    model_path=read_bytes("tex_model.obj"),
    name="sniff_test_gen_uv",
))

# 5. gen_video_motion：FBX 模型 + MP4 视频，全部 bytes
run("gen_video_motion (FBX + MP4 bytes)", lambda: client.gen_video_motion(
    model_path=read_bytes("animation_model.fbx"),
    video_path=read_bytes("animation_video.mp4"),
    output_model_format=OutputModelFormat.FBX,
    name="sniff_test_gen_video_motion",
))

# ──────────────────────────────────────────────────────────────────────
# 汇总
# ──────────────────────────────────────────────────────────────────────

print("\n" + "=" * 70)
print(" 测试汇总")
print("=" * 70)
pass_count = sum(1 for r in results if r[0] == "PASS")
fail_count = sum(1 for r in results if r[0] == "FAIL")
for status, name, detail in results:
    icon = "✅" if status == "PASS" else "❌"
    print(f"  {icon} {name:45s}  {detail}")
print(f"\n通过 {pass_count} / 失败 {fail_count} / 总计 {len(results)}")
sys.exit(0 if fail_count == 0 else 1)
