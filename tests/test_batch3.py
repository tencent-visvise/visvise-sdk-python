"""批次3：gen_video_motion / gen_text_motion"""
import sys, os, json; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pathlib import Path
from visvise import VisviseClient

APP_ID = os.environ["VISVISE_APP_ID"]
SECRET_KEY = os.environ["VISVISE_SECRET_KEY"]
UID        = os.environ["VISVISE_UID"]
ASSETS = Path(__file__).parent / "assets"
client = VisviseClient(APP_ID, SECRET_KEY, UID)

results = []
def check(name, mid, expected):
    m = client.wait_model(mid, interval=5, timeout=900)
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

# gen_video_motion: with_hand / multiple_track
run("vm with_hand=True", lambda: check("vm with_hand=True",
    client.gen_video_motion(str(ASSETS/"animation_model.fbx"), str(ASSETS/"animation_video.mp4"),
        "VISVISE-FramingAI-Base-V1.5.0", with_hand=True, name="opt_vm_a"),
    {"framing_ai_params.with_hand": True}))
run("vm hand=False multi=False", lambda: check("vm hand=False multi=False",
    client.gen_video_motion(str(ASSETS/"animation_model.fbx"), str(ASSETS/"animation_video.mp4"),
        "VISVISE-FramingAI-Base-V1.5.0", with_hand=False, multiple_track=False, name="opt_vm_b"),
    {"framing_ai_params.with_hand": False, "framing_ai_params.multiple_track": False}))

# gen_text_motion: prompt content
run("tm prompt=挥手", lambda: check("tm prompt=挥手",
    client.gen_text_motion(str(ASSETS/"animation_model.fbx"), "一个人在挥手打招呼",
        "VISVISE-TextMotion-V1.1.0", name="opt_tm_a")[0],
    {"framing_ai_params.prompt": "一个人在挥手打招呼"}))
run("tm prompt=踏步 glb", lambda: check("tm prompt=踏步 glb",
    client.gen_text_motion(str(ASSETS/"animation_model.fbx"), "一个人在原地踏步",
        "VISVISE-TextMotion-V1.1.0", output_model_format="glb", name="opt_tm_b")[0],
    {"framing_ai_params.prompt": "一个人在原地踏步",
     "framing_ai_params.output_model_format": "glb"}))

print("\n=== BATCH3 SUMMARY ===")
for s,n,m,t,issues in results:
    mark = "✅" if s=="PASS" else "❌"
    print(f"  {mark} {s} {n} ({t}s)")
    for i in issues: print(f"      {i}")
