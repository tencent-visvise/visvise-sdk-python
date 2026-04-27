"""批次1：gen_360 / gen_high_model / gen_low_model / gen_lod"""
import sys, os, json; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
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

results = []
def check(name, mid, expected):
    m = client.wait_model(mid, interval=3, timeout=600)
    actual = m.params or {}
    ok, issues = True, []
    for kp, ev in expected.items():
        v = actual
        for p in kp.split("."): v = v.get(p) if isinstance(v, dict) else None
        if v is None and ev is False:
            issues.append(f"  SKIP {kp}: False not returned by server")
        elif v != ev:
            ok = False; issues.append(f"  FAIL {kp}: expected={ev!r} actual={v!r}")
    status = "PASS" if ok else "FAIL"
    results.append((status, name, mid, m.time_cost, issues))
    print(f"{'✅' if ok else '❌'} {status} [{name}] {mid} {m.time_cost}s")
    print(f"  params: {json.dumps(actual, ensure_ascii=False)}")
    for i in issues: print(i)

def run(label, fn):
    try: fn()
    except Exception as e:
        results.append(("ERROR", label, "N/A", 0, [str(e)]))
        print(f"❌ ERROR [{label}]: {e}")

# gen_360: enable_a_pose=True / False
run("gen_360 a_pose=True",  lambda: check("gen_360 a_pose=True",
    client.gen_360(str(ASSETS/"main_view.png"), "VISVISE-MultiView-V1.0.0", name="opt_360a", enable_a_pose=True),
    {"image_gen_360_params.enable_a_pose": True}))
run("gen_360 a_pose=False", lambda: check("gen_360 a_pose=False",
    client.gen_360(str(ASSETS/"main_view.png"), "VISVISE-MultiView-V1.0.0", name="opt_360b", enable_a_pose=False),
    {"image_gen_360_params.enable_a_pose": False}))

# gen_high_model: face_num / face_type+format
run("high face_num=100000", lambda: check("high face_num=100000",
    client.gen_high_model(MV["main"], "Tripo-v3.1-ultra", face_type=1, name="opt_hm_a", face_num=100000),
    {"image_gen_model_params.face_num": 100000, "image_gen_model_params.face_type": 1}))
run("high face_type=2 glb", lambda: check("high face_type=2 glb",
    client.gen_high_model(MV["main"], "Tripo-v3.1-ultra", face_type=2, output_model_format="glb", name="opt_hm_b"),
    {"image_gen_model_params.face_type": 2, "image_gen_model_params.output_model_format": "glb"}))

# gen_low_model: face_type + back_view
run("low face_type=1 back", lambda: check("low face_type=1 back",
    client.gen_low_model(MV["main"], "Tripo-v1.0-快速生成", face_type=1, back_view=MV["back"], name="opt_lm_a"),
    {"image_gen_model_params.face_type": 1}))
run("low face_type=2 fbx",  lambda: check("low face_type=2 fbx",
    client.gen_low_model(MV["main"], "Tripo-v1.0-快速生成", face_type=2, output_model_format="fbx", name="opt_lm_b"),
    {"image_gen_model_params.face_type": 2, "image_gen_model_params.output_model_format": "fbx"}))

# gen_lod: gen_times
run("lod gen_times=1", lambda: check("lod gen_times=1",
    client.gen_lod(str(ASSETS/"tex_model.obj"), "VISVISE-LOD-V1.0.0",
        [ReduceFace(1,50,2)], output_model_format="fbx", gen_times=1, name="opt_lod_a")[0],
    {"lod_params.output_model_format": "fbx"}))

print("\n=== BATCH1 SUMMARY ===")
for s,n,m,t,issues in results:
    mark = "✅" if s=="PASS" else "❌"
    print(f"  {mark} {s} {n} ({t}s)")
    for i in issues: print(f"      {i}")
