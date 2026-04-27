"""
可选参数测试 - 最终收尾脚本

1. 查询昨天已提交的 batch2 model_id 结果
2. 新提交并等待 batch3（动画）和剩余任务
"""
import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path
from visvise import VisviseClient
from visvise.models import View, ReduceFace

APP_ID = os.environ["VISVISE_APP_ID"]
SECRET_KEY = os.environ["VISVISE_SECRET_KEY"]
ASSETS = Path(__file__).parent / "assets"
client = VisviseClient(APP_ID, SECRET_KEY)

MV_BASE = "https://visvise-weaver-bj-rel-1311802504.cos.accelerate.myqcloud.com/weaver/user-p_5sxfmuvwtfj58ssbt97q2k2kc83697p/Model2026042300225069"
MV = {k: f"{MV_BASE}/example_gen_360_MultiView(2)_{v}.png"
      for k, v in [("main","MainView"),("back","BackView"),("left","LeftView"),("right","RightView")]}

all_results = []

def check(name, mid, expected, timeout=3600):
    print(f"  Checking [{name}] {mid}...", flush=True)
    try:
        m = client.wait_model(mid, interval=10, timeout=timeout)
        actual = m.params or {}
        ok, issues = True, []
        for kp, ev in expected.items():
            v = actual
            for p in kp.split("."): v = v.get(p) if isinstance(v, dict) else None
            if v is None and ev is False:
                issues.append(f"  SKIP {kp}: False不被服务端回传，视为正常")
            elif v != ev:
                ok = False; issues.append(f"  ❌ MISMATCH {kp}: expected={ev!r} actual={v!r}")
        status = "✅ PASS" if ok else "❌ FAIL"
        all_results.append((status, name, mid, m.time_cost, issues))
        print(f"{status} [{name}] {mid} {m.time_cost}s", flush=True)
        print(f"  params: {json.dumps(actual, ensure_ascii=False)}", flush=True)
        for i in issues: print(i, flush=True)
    except Exception as e:
        all_results.append(("❌ ERROR", name, mid, 0, [str(e)]))
        print(f"❌ ERROR [{name}] {mid}: {e}", flush=True)

def submit_and_check(name, fn, expected, timeout=3600):
    try:
        mid = fn()
        print(f"  Submitted [{name}] → {mid}", flush=True)
        check(name, mid, expected, timeout)
    except Exception as e:
        all_results.append(("❌ ERROR", name, "N/A", 0, [str(e)]))
        print(f"❌ ERROR submit [{name}]: {e}", flush=True)

# ─── Step1: 用昨天 batch2 的 model_id 直接查 ───────────────────────────
print("\n=== Step1: 查询昨天 batch2 的已提交任务 ===", flush=True)
yesterday = [
    ("mid face_type=1 fbx",   "Model2026042300225326", {"image_gen_model_params.face_type":1,"image_gen_model_params.output_model_format":"fbx"}),
    ("rtp detail=2 face=2",   "Model2026042300225337", {"re_topology_params.detail_level":2,"re_topology_params.face_type":2}),
    ("mr preserve=True",      "Model2026042300225347", {"mesh_refine_params.enable_detail_preserve":True}),
    ("uv smooth=True",        "Model2026042300226324", {"uv_params.enable_auto_smoothing":True}),
    ("tex res=1024",          "Model2026042300225360", {"tex_params.resolution":1024}),
]
for name, mid, exp in yesterday:
    check(name, mid, exp, timeout=60)  # 已完成的，短超时即可

# ─── Step2: 补交 batch2 第2组 ─────────────────────────────────────────
print("\n=== Step2: 补提交 batch2 第2组 ===", flush=True)
submit_and_check("mid face_type=2 fbx",
    lambda: client.gen_mid_model(MV["main"],MV["back"],MV["left"],MV["right"],
        "VISVISE-MeshGen-V1.0.0", face_type=2, output_model_format="fbx", name="opt_mid_b"),
    {"image_gen_model_params.face_type":2,"image_gen_model_params.output_model_format":"fbx"})

submit_and_check("rtp detail=3 face=1",
    lambda: client.gen_retopology(str(ASSETS/"tex_model.obj"), "hunyuan3D-RTP-v1.5",
        face_type=1, detail_level=3, output_model_format="fbx", name="opt_rtp_b"),
    {"re_topology_params.detail_level":3,"re_topology_params.face_type":1})

submit_and_check("uv smooth=False",
    lambda: client.gen_uv(str(ASSETS/"tex_model.obj"), "hunyuan3D-UV-v2.0",
        enable_auto_smoothing=False, name="opt_uv_b"),
    {"uv_params.enable_auto_smoothing":False})

submit_and_check("tex res=2048 uv=True",
    lambda: client.gen_texture(str(ASSETS/"tex_model.obj"), "hunyuan3D-TEX-v2.0",
        input_view=View(main_view=str(ASSETS/"tex_ref_front.jpg")),
        resolution=2048, unwarp_uv=True, name="opt_tex_b"),
    {"tex_params.resolution":2048,"tex_params.unwarp_uv":True})

# LOD（延长超时）
submit_and_check("lod gen_times=1",
    lambda: client.gen_lod(str(ASSETS/"tex_model.obj"), "VISVISE-LOD-V1.0.0",
        [ReduceFace(1,50,2)], output_model_format="fbx", gen_times=1, name="opt_lod_a")[0],
    {"lod_params.output_model_format":"fbx"}, timeout=1200)

# ─── Step3: batch3 动画（串行，各自等待） ────────────────────────────────
print("\n=== Step3: 动画类测试 ===", flush=True)
submit_and_check("vm with_hand=True",
    lambda: client.gen_video_motion(str(ASSETS/"animation_model.fbx"),str(ASSETS/"animation_video.mp4"),
        "VISVISE-FramingAI-Base-V1.5.0", with_hand=True, name="opt_vm_a"),
    {"framing_ai_params.with_hand":True})

submit_and_check("vm hand=False multi=False",
    lambda: client.gen_video_motion(str(ASSETS/"animation_model.fbx"),str(ASSETS/"animation_video.mp4"),
        "VISVISE-FramingAI-Base-V1.5.0", with_hand=False, multiple_track=False, name="opt_vm_b"),
    {"framing_ai_params.with_hand":False,"framing_ai_params.multiple_track":False})

submit_and_check("tm prompt=挥手",
    lambda: client.gen_text_motion(str(ASSETS/"animation_model.fbx"), "一个人在挥手打招呼",
        "VISVISE-TextMotion-V1.1.0", name="opt_tm_a")[0],
    {"framing_ai_params.prompt":"一个人在挥手打招呼"})

submit_and_check("tm prompt=踏步 glb",
    lambda: client.gen_text_motion(str(ASSETS/"animation_model.fbx"), "一个人在原地踏步",
        "VISVISE-TextMotion-V1.1.0", output_model_format="glb", name="opt_tm_b")[0],
    {"framing_ai_params.prompt":"一个人在原地踏步","framing_ai_params.output_model_format":"glb"})

# ─── FINAL SUMMARY ──────────────────────────────────────────────────────
print("\n" + "="*60, flush=True)
print("FINAL SUMMARY", flush=True)
print("="*60, flush=True)
passed = sum(1 for s,*_ in all_results if "PASS" in s)
failed = sum(1 for s,*_ in all_results if "FAIL" in s or "ERROR" in s)
print(f"Total: {len(all_results)}  ✅PASS: {passed}  ❌FAIL/ERROR: {failed}", flush=True)
for s,n,m,t,issues in all_results:
    print(f"  {s} {n} ({t}s)", flush=True)
    for i in issues: print(f"      {i}", flush=True)
