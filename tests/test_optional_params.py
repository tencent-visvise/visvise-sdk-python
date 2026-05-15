"""
可选参数测试脚本（续跑版）

跳过已完成的测试，继续测试剩余部分。
"""

import sys, os, json, time, traceback
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path
from visvise import VisviseClient
from visvise.models import View, ReduceFace

APP_ID     = os.environ["VISVISE_APP_ID"]
SECRET_KEY = os.environ["VISVISE_SECRET_KEY"]
RTX        = os.environ["VISVISE_RTX"]
ASSETS     = Path(__file__).parent / "assets"

client = VisviseClient(APP_ID, SECRET_KEY)

MV_BASE = "https://visvise-weaver-bj-rel-1311802504.cos.accelerate.myqcloud.com/weaver/user-p_5sxfmuvwtfj58ssbt97q2k2kc83697p/Model2026042300225069"
MV = {
    "main":  f"{MV_BASE}/example_gen_360_MultiView(2)_MainView.png",
    "back":  f"{MV_BASE}/example_gen_360_MultiView(2)_BackView.png",
    "left":  f"{MV_BASE}/example_gen_360_MultiView(2)_LeftView.png",
    "right": f"{MV_BASE}/example_gen_360_MultiView(2)_RightView.png",
}

results = []

def check(name, model_id, expected_params: dict):
    model = client.wait_model(model_id, interval=5, timeout=900, rtx=RTX)
    actual = model.params or {}
    ok = True
    mismatches = []
    for key_path, expected_val in expected_params.items():
        parts = key_path.split(".")
        val = actual
        for p in parts:
            val = val.get(p) if isinstance(val, dict) else None
        # 服务端对 False/0 等默认值不回传，跳过 None 的情况（标记为 SKIP）
        if val is None and expected_val is False:
            mismatches.append(f"  {key_path}: expected={expected_val!r}, actual=None (服务端不回传默认False，视为SKIP)")
        elif val != expected_val:
            ok = False
            mismatches.append(f"  {key_path}: expected={expected_val!r}, actual={val!r}")

    status = "✅ PASS" if ok else "❌ FAIL"
    results.append({"name": name, "model_id": model_id, "status": status,
                    "mismatches": mismatches, "params": actual, "time_cost": model.time_cost})
    print(f"\n{status} [{name}] model_id={model_id} time={model.time_cost}s")
    print(f"  actual params : {json.dumps(actual, ensure_ascii=False)}")
    if mismatches:
        for m in mismatches:
            print(m)

def run(label, fn):
    try:
        fn()
    except Exception as e:
        print(f"\n❌ ERROR [{label}]: {e}")
        results.append({"name": label, "model_id": "N/A", "status": "❌ ERROR",
                        "mismatches": [str(e)], "params": {}, "time_cost": 0})

# ── gen_low_model (第2组，换 obj 格式) ──────────────────────────────────
print("\n=== gen_low_model (2nd group) ===")
def t_low_b():
    mid = client.gen_low_model(MV["main"], "Tripo-v1.0-快速生成",
                                face_type=2, output_model_format="obj",
                                name="opt_low_b2",
        rtx=RTX,)
    check("gen_low_model face_type=2 obj", mid,
          {"image_gen_model_params.face_type": 2,
           "image_gen_model_params.output_model_format": "obj"})
run("gen_low_model face_type=2 obj", t_low_b)

# ── gen_retopology ──────────────────────────────────────────────────────
print("\n=== gen_retopology ===")
def t_rtp_a():
    mid = client.gen_retopology(str(ASSETS/"tex_model.obj"), "hunyuan3D-RTP-v1.5",
                                 face_type=2, detail_level=2, output_model_format="fbx",
                                 name="opt_rtp_a",
        rtx=RTX,)
    check("gen_retopology detail_level=2", mid,
          {"re_topology_params.detail_level": 2, "re_topology_params.face_type": 2})
def t_rtp_b():
    mid = client.gen_retopology(str(ASSETS/"tex_model.obj"), "hunyuan3D-RTP-v1.5",
                                 face_type=1, detail_level=3, output_model_format="fbx",
                                 name="opt_rtp_b",
        rtx=RTX,)
    check("gen_retopology detail_level=3 face_type=1", mid,
          {"re_topology_params.detail_level": 3, "re_topology_params.face_type": 1})
run("gen_retopology a", t_rtp_a)
run("gen_retopology b", t_rtp_b)

# ── gen_mesh_refine ─────────────────────────────────────────────────────
print("\n=== gen_mesh_refine ===")
def t_mr_a():
    mid = client.gen_mesh_refine(str(ASSETS/"tex_model.obj"), "VISVISE-MeshRefine-V1.0.0",
                                  input_model_format="obj", enable_detail_preserve=True,
                                  name="opt_mr_a",
        rtx=RTX,)
    check("gen_mesh_refine enable_detail_preserve=True", mid,
          {"mesh_refine_params.enable_detail_preserve": True})
def t_mr_b():
    mid = client.gen_mesh_refine(str(ASSETS/"tex_model.obj"), "VISVISE-MeshRefine-V1.0.0",
                                  input_model_format="obj", enable_detail_preserve=False,
                                  name="opt_mr_b",
        rtx=RTX,)
    check("gen_mesh_refine enable_detail_preserve=False", mid,
          {"mesh_refine_params.enable_detail_preserve": False})
run("gen_mesh_refine a", t_mr_a)
run("gen_mesh_refine b", t_mr_b)

# ── gen_uv ──────────────────────────────────────────────────────────────
print("\n=== gen_uv ===")
def t_uv_a():
    mid = client.gen_uv(str(ASSETS/"tex_model.obj"), "hunyuan3D-UV-v2.0",
                        enable_auto_smoothing=True, name="opt_uv_a",
        rtx=RTX,)
    check("gen_uv enable_auto_smoothing=True", mid,
          {"uv_params.enable_auto_smoothing": True})
def t_uv_b():
    mid = client.gen_uv(str(ASSETS/"tex_model.obj"), "hunyuan3D-UV-v2.0",
                        enable_auto_smoothing=False, name="opt_uv_b",
        rtx=RTX,)
    check("gen_uv enable_auto_smoothing=False", mid,
          {"uv_params.enable_auto_smoothing": False})
run("gen_uv a", t_uv_a)
run("gen_uv b", t_uv_b)

# ── gen_texture ─────────────────────────────────────────────────────────
print("\n=== gen_texture ===")
def t_tex_a():
    mid = client.gen_texture(
        str(ASSETS/"tex_model.obj"), "hunyuan3D-TEX-v2.0",
        input_view=View(main_view=str(ASSETS/"tex_ref_front.jpg")),
        resolution=1024, unwarp_uv=False, name="opt_tex_a",
        rtx=RTX,)
    check("gen_texture resolution=1024 unwarp_uv=False", mid,
          {"tex_params.resolution": 1024, "tex_params.unwarp_uv": False})
def t_tex_b():
    mid = client.gen_texture(
        str(ASSETS/"tex_model.obj"), "hunyuan3D-TEX-v2.0",
        input_view=View(main_view=str(ASSETS/"tex_ref_front.jpg")),
        resolution=2048, unwarp_uv=True, name="opt_tex_b",
        rtx=RTX,)
    check("gen_texture resolution=2048 unwarp_uv=True", mid,
          {"tex_params.resolution": 2048, "tex_params.unwarp_uv": True})
run("gen_texture a", t_tex_a)
run("gen_texture b", t_tex_b)

# ── gen_lod ─────────────────────────────────────────────────────────────
print("\n=== gen_lod ===")
def t_lod_a():
    mids = client.gen_lod(
        str(ASSETS/"tex_model.obj"), "VISVISE-LOD-V1.0.0",
        reduce_faces=[ReduceFace(1, 50, 2)],
        output_model_format="fbx", gen_times=1, name="opt_lod_a",
        rtx=RTX,)
    check("gen_lod gen_times=1 fbx", mids[0],
          {"lod_params.output_model_format": "fbx"})
run("gen_lod a", t_lod_a)

# ── gen_video_motion ─────────────────────────────────────────────────────
print("\n=== gen_video_motion ===")
def t_vm_a():
    mid = client.gen_video_motion(
        str(ASSETS/"animation_model.fbx"), str(ASSETS/"animation_video.mp4"),
        "VISVISE-FramingAI-Base-V1.5.0", with_hand=True, name="opt_vm_a",
        rtx=RTX,)
    check("gen_video_motion with_hand=True", mid,
          {"framing_ai_params.with_hand": True})
def t_vm_b():
    mid = client.gen_video_motion(
        str(ASSETS/"animation_model.fbx"), str(ASSETS/"animation_video.mp4"),
        "VISVISE-FramingAI-Base-V1.5.0", with_hand=False, multiple_track=False,
        name="opt_vm_b",
        rtx=RTX,)
    check("gen_video_motion with_hand=False multiple_track=False", mid,
          {"framing_ai_params.with_hand": False,
           "framing_ai_params.multiple_track": False})
run("gen_video_motion a", t_vm_a)
run("gen_video_motion b", t_vm_b)

# ── gen_text_motion ──────────────────────────────────────────────────────
print("\n=== gen_text_motion ===")
def t_tm_a():
    mids = client.gen_text_motion(
        str(ASSETS/"animation_model.fbx"), "一个人在挥手打招呼",
        "VISVISE-TextMotion-V1.1.0", name="opt_tm_a",
        rtx=RTX,)
    check("gen_text_motion prompt=挥手", mids[0],
          {"framing_ai_params.prompt": "一个人在挥手打招呼"})
def t_tm_b():
    mids = client.gen_text_motion(
        str(ASSETS/"animation_model.fbx"), "一个人在原地踏步",
        "VISVISE-TextMotion-V1.1.0", output_model_format="fbx", name="opt_tm_b",
        rtx=RTX,)
    check("gen_text_motion prompt=踏步", mids[0],
          {"framing_ai_params.prompt": "一个人在原地踏步"})
run("gen_text_motion a", t_tm_a)
run("gen_text_motion b", t_tm_b)

# ── 汇总 ────────────────────────────────────────────────────────────────
print("\n\n" + "="*60)
print("FINAL SUMMARY")
print("="*60)
passed = sum(1 for r in results if "PASS" in r["status"])
failed = sum(1 for r in results if "FAIL" in r["status"])
errors = sum(1 for r in results if "ERROR" in r["status"])
print(f"Total: {len(results)}  ✅PASS: {passed}  ❌FAIL: {failed}  ❌ERROR: {errors}")
for r in results:
    print(f"  {r['status']} {r['name']} ({r['time_cost']}s)")
    if r["mismatches"]:
        for m in r["mismatches"]:
            print(f"      {m}")
