"""批次2：gen_mid_model / gen_retopology / gen_mesh_refine / gen_uv / gen_texture"""
import sys, os, json; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pathlib import Path
from visvise import VisviseClient
from visvise.models import View

APP_ID = os.environ["VISVISE_APP_ID"]
SECRET_KEY = os.environ["VISVISE_SECRET_KEY"]
RTX        = os.environ["VISVISE_RTX"]
ASSETS = Path(__file__).parent / "assets"
client = VisviseClient(APP_ID, SECRET_KEY)

MV_BASE = "https://visvise-weaver-bj-rel-1311802504.cos.accelerate.myqcloud.com/weaver/user-p_5sxfmuvwtfj58ssbt97q2k2kc83697p/Model2026042300225069"
MV = {k: f"{MV_BASE}/example_gen_360_MultiView(2)_{v}.png"
      for k, v in [("main","MainView"),("back","BackView"),("left","LeftView"),("right","RightView")]}

results = []
def check(name, mid, expected):
    m = client.wait_model(mid, interval=5, timeout=900, rtx=RTX)
    actual = m.params or {}
    ok, issues = True, []
    for kp, ev in expected.items():
        v = actual
        for p in kp.split("."): v = v.get(p) if isinstance(v, dict) else None
        if v is None and ev is False:
            issues.append(f"  SKIP {kp}: False not returned by server")
        elif v != ev:
            ok = False; issues.append(f"  FAIL {kp}: expected={ev!r} actual={v!r}")
    s = "PASS" if ok else "FAIL"
    results.append((s, name, mid, m.time_cost, issues))
    print(f"{'✅' if ok else '❌'} {s} [{name}] {mid} {m.time_cost}s")
    print(f"  params: {json.dumps(actual, ensure_ascii=False)}")
    for i in issues: print(i)

def run(label, fn):
    try: fn()
    except Exception as e:
        results.append(("ERROR", label, "N/A", 0, [str(e)]))
        print(f"❌ ERROR [{label}]: {e}")

# gen_mid_model: face_type / output_format（中模算法不支持 glb，仅测试 fbx）
run("mid face_type=1 fbx", lambda: check("mid face_type=1 fbx",
    client.gen_mid_model(MV["main"],MV["back"],MV["left"],MV["right"],
        "VISVISE-MeshGen-V1.0.0", face_type=1, output_model_format="fbx", name="opt_mid_a",
        rtx=RTX,),
    {"image_gen_model_params.face_type": 1, "image_gen_model_params.output_model_format": "fbx"}))
run("mid face_type=2 fbx", lambda: check("mid face_type=2 fbx",
    client.gen_mid_model(MV["main"],MV["back"],MV["left"],MV["right"],
        "VISVISE-MeshGen-V1.0.0", face_type=2, output_model_format="fbx", name="opt_mid_b",
        rtx=RTX,),
    {"image_gen_model_params.face_type": 2, "image_gen_model_params.output_model_format": "fbx"}))

# gen_retopology: detail_level variations
run("rtp detail=2 face=2", lambda: check("rtp detail=2 face=2",
    client.gen_retopology(str(ASSETS/"tex_model.obj"), "hunyuan3D-RTP-v1.5",
        face_type=2, detail_level=2, output_model_format="fbx", name="opt_rtp_a",
        rtx=RTX,),
    {"re_topology_params.detail_level": 2, "re_topology_params.face_type": 2}))
run("rtp detail=3 face=1", lambda: check("rtp detail=3 face=1",
    client.gen_retopology(str(ASSETS/"tex_model.obj"), "hunyuan3D-RTP-v1.5",
        face_type=1, detail_level=3, output_model_format="fbx", name="opt_rtp_b",
        rtx=RTX,),
    {"re_topology_params.detail_level": 3, "re_topology_params.face_type": 1}))

# gen_mesh_refine: enable_detail_preserve
run("mr preserve=True", lambda: check("mr preserve=True",
    client.gen_mesh_refine(str(ASSETS/"tex_model.obj"), "VISVISE-MeshRefine-V1.0.0",
        input_model_format="obj", enable_detail_preserve=True, name="opt_mr_a",
        rtx=RTX,),
    {"mesh_refine_params.enable_detail_preserve": True}))
run("mr preserve=False", lambda: check("mr preserve=False",
    client.gen_mesh_refine(str(ASSETS/"tex_model.obj"), "VISVISE-MeshRefine-V1.0.0",
        input_model_format="obj", enable_detail_preserve=False, name="opt_mr_b",
        rtx=RTX,),
    {"mesh_refine_params.enable_detail_preserve": False}))

# gen_uv: enable_auto_smoothing
run("uv smooth=True", lambda: check("uv smooth=True",
    client.gen_uv(str(ASSETS/"tex_model.obj"), "hunyuan3D-UV-v2.0",
        enable_auto_smoothing=True, name="opt_uv_a",
        rtx=RTX,),
    {"uv_params.enable_auto_smoothing": True}))
run("uv smooth=False", lambda: check("uv smooth=False",
    client.gen_uv(str(ASSETS/"tex_model.obj"), "hunyuan3D-UV-v2.0",
        enable_auto_smoothing=False, name="opt_uv_b",
        rtx=RTX,),
    {"uv_params.enable_auto_smoothing": False}))

# gen_texture: resolution / unwarp_uv
run("tex res=1024", lambda: check("tex res=1024",
    client.gen_texture(str(ASSETS/"tex_model.obj"), "hunyuan3D-TEX-v2.0",
        input_view=View(main_view=str(ASSETS/"tex_ref_front.jpg")),
        resolution=1024, unwarp_uv=False, name="opt_tex_a",
        rtx=RTX,),
    {"tex_params.resolution": 1024, "tex_params.unwarp_uv": False}))
run("tex res=2048 uv=True", lambda: check("tex res=2048 uv=True",
    client.gen_texture(str(ASSETS/"tex_model.obj"), "hunyuan3D-TEX-v2.0",
        input_view=View(main_view=str(ASSETS/"tex_ref_front.jpg")),
        resolution=2048, unwarp_uv=True, name="opt_tex_b",
        rtx=RTX,),
    {"tex_params.resolution": 2048, "tex_params.unwarp_uv": True}))

print("\n=== BATCH2 SUMMARY ===")
for s,n,m,t,issues in results:
    mark = "✅" if s=="PASS" else "❌"
    print(f"  {mark} {s} {n} ({t}s)")
    for i in issues: print(f"      {i}")
