"""
测试 algorithm_model 可选参数 —— 所有 gen_xxx 方法不传 algorithm_model

验证 SDK 自动调用 list_algorithm_model 获取第一个可用模型并正常提交任务。
对接开发环境。
"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path
from visvise import VisviseClient, Environment
from visvise.models import View, ReduceFace

APP_ID = os.environ["VISVISE_APP_ID"]
SECRET_KEY = os.environ["VISVISE_SECRET_KEY"]
RTX = os.environ["VISVISE_RTX"]
ASSETS     = Path(__file__).parent / "assets"

client = VisviseClient(APP_ID, SECRET_KEY, env=Environment.DEV)

results = []


def ok(name, detail=""):
    results.append(("PASS", name, detail))
    print(f"✅ PASS [{name}]", flush=True)
    if detail:
        print(f"  {detail}", flush=True)


def fail(name, reason):
    results.append(("FAIL", name, reason))
    print(f"❌ FAIL [{name}]: {reason}", flush=True)


def run(name, fn):
    """提交任务并验证返回 model_id"""
    try:
        result = fn()
        if isinstance(result, list):
            ok(name, f"model_ids={result}")
        else:
            ok(name, f"model_id={result}")
    except Exception as e:
        fail(name, str(e))


# ──────────────────────────────────────────────────────────────────────
# 测试用例：每个 gen_xxx 方法都不传 algorithm_model
# ──────────────────────────────────────────────────────────────────────

print("=" * 60)
print("测试：algorithm_model 可选（不传）- 自动获取首个可用模型")
print("=" * 60)

# 1. gen_360 - 图生360
run("gen_360 (no algorithm_model)", lambda: client.gen_360(
    main_view=str(ASSETS / "main_view.png"),
    name="test_auto_alg_360",
    rtx=RTX,
))

# 2. gen_high_model - 图生高模
run("gen_high_model (no algorithm_model)", lambda: client.gen_high_model(
    main_view=str(ASSETS / "main_view.png"),
    name="test_auto_alg_high",
    rtx=RTX,
))

# 3. gen_mid_model - 图生中模（需要四视图）
run("gen_mid_model (no algorithm_model)", lambda: client.gen_mid_model(
    main_view=str(ASSETS / "main_view.png"),
    back_view=str(ASSETS / "back_view.png"),
    left_view=str(ASSETS / "left_view.png"),
    right_view=str(ASSETS / "right_view.png"),
    name="test_auto_alg_mid",
    rtx=RTX,
))

# 4. gen_low_model - 图生低模
run("gen_low_model (no algorithm_model)", lambda: client.gen_low_model(
    main_view=str(ASSETS / "main_view.png"),
    name="test_auto_alg_low",
    rtx=RTX,
))

# 5. gen_mesh_refine - 重布线
run("gen_mesh_refine (no algorithm_model)", lambda: client.gen_mesh_refine(
    model_path=str(ASSETS / "high_model.fbx"),
    name="test_auto_alg_mesh_refine",
    rtx=RTX,
))

# 6. gen_retopology - 重拓扑
run("gen_retopology (no algorithm_model)", lambda: client.gen_retopology(
    model_path=str(ASSETS / "high_model.fbx"),
    detail_level=2,
    name="test_auto_alg_retopology",
    rtx=RTX,
))

# 7. gen_lod - LOD
run("gen_lod (no algorithm_model)", lambda: client.gen_lod(
    model_path=str(ASSETS / "high_model.fbx"),
    reduce_faces=[ReduceFace(1, 50, 2)],
    name="test_auto_alg_lod",
    rtx=RTX,
))

# 8. gen_uv - UV展开
run("gen_uv (no algorithm_model)", lambda: client.gen_uv(
    model_path=str(ASSETS / "high_model.fbx"),
    name="test_auto_alg_uv",
    rtx=RTX,
))

# 9. gen_texture - 贴图
run("gen_texture (no algorithm_model)", lambda: client.gen_texture(
    model_path=str(ASSETS / "high_model.fbx"),
    input_view=View(main_view=str(ASSETS / "main_view.png")),
    name="test_auto_alg_texture",
    rtx=RTX,
))

# 10. gen_rigging - 骨骼架设
run("gen_rigging (no algorithm_model)", lambda: client.gen_rigging(
    model_path=str(ASSETS / "high_model.fbx"),
    name="test_auto_alg_rigging",
    rtx=RTX,
))

# 11. gen_skinning - 蒙皮
run("gen_skinning (no algorithm_model)", lambda: client.gen_skinning(
    model_path=str(ASSETS / "skinning_model.fbx"),
    mesh_names=["Body_Mesh"],
    joint_names=["Bip001", "Bip001 Pelvis"],
    name="test_auto_alg_skinning",
    rtx=RTX,
))

# 12. gen_video_motion - 视频生动画
run("gen_video_motion (no algorithm_model)", lambda: client.gen_video_motion(
    model_path=str(ASSETS / "animation_model.fbx"),
    video_path=str(ASSETS / "animation_video.mp4"),
    name="test_auto_alg_video_motion",
    rtx=RTX,
))

# 13. gen_text_motion - 文本生动画
run("gen_text_motion (no algorithm_model)", lambda: client.gen_text_motion(
    model_path=str(ASSETS / "animation_model.fbx"),
    prompt="一个人在原地踏步",
    name="test_auto_alg_text_motion",
    rtx=RTX,
))

# 14. gen_pose - 图生Pose
run("gen_pose (no algorithm_model)", lambda: client.gen_pose(
    model_path=str(ASSETS / "animation_model.fbx"),
    input_images=[str(ASSETS / "main_view.png")],
    name="test_auto_alg_pose",
    rtx=RTX,
))

# ──────────────────────────────────────────────────────────────────────
# 汇总
# ──────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("测试结果汇总")
print("=" * 60)
passed = sum(1 for r in results if r[0] == "PASS")
failed = sum(1 for r in results if r[0] == "FAIL")
print(f"  总计: {len(results)} | 通过: {passed} | 失败: {failed}")
for status, name, detail in results:
    print(f"  [{status}] {name}")
    if detail and status == "FAIL":
        print(f"    → {detail}")

if failed > 0:
    sys.exit(1)
