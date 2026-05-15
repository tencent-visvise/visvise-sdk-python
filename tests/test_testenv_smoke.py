"""TEST 环境冒烟：跑几个 gen_xxx 实测。鉴权信息从环境变量读取。"""

import logging, os, sys
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from visvise import VisviseClient, Environment, OutputModelFormat, FaceType, DetailLevel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s %(message)s")

APP_ID = os.environ["VISVISE_APP_ID"]
KEY    = os.environ["VISVISE_SECRET_KEY"]
RTX = os.environ["VISVISE_RTX"]
ASSETS=Path(__file__).parent/"assets"

client = VisviseClient(APP_ID, KEY, env=Environment.TEST)

def read(p): return (ASSETS/p).read_bytes()

results=[]
def run(name, fn):
    print(f"\n━━━ {name} ━━━")
    try:
        r = fn()
        results.append(("PASS", name, str(r)))
        print(f"✅ PASS [{name}] → {r}")
    except Exception as e:
        results.append(("FAIL", name, f"{type(e).__name__}: {e}"))
        print(f"❌ FAIL [{name}]: {type(e).__name__}: {e}")

print("="*70)
print(f" {APP_ID} @ TEST 环境冒烟")
print("="*70)

try:
    q = client.api.get_user_quota(rtx=RTX)
    print(f"\n剩余配额: {q.quota}\n")
except Exception as e:
    print(f"⚠️  查配额: {e}\n")

run("gen_360 (PNG bytes)", lambda: client.gen_360(
    main_view=read("main_view.png"), name="testenv_gen_360",
    rtx=RTX,))

run("gen_high_model (path)", lambda: client.gen_high_model(
    main_view=str(ASSETS/"main_view.png"),
    output_model_format=OutputModelFormat.FBX,
    face_type=FaceType.TRIANGLE,
    name="testenv_gen_high",
    rtx=RTX,))

run("gen_uv (OBJ bytes)", lambda: client.gen_uv(
    model_path=read("tex_model.obj"), name="testenv_gen_uv",
    rtx=RTX,))

run("gen_text_motion (FBX bytes + prompt)", lambda: client.gen_text_motion(
    model_path=read("animation_model.fbx"),
    prompt="一个人在跳街舞",
    output_model_format=OutputModelFormat.FBX,
    name="testenv_gen_text_motion",
    rtx=RTX,))

print("\n"+"="*70)
ps=sum(1 for r in results if r[0]=="PASS")
fs=sum(1 for r in results if r[0]=="FAIL")
for st,nm,dt in results:
    print(f"  {'✅' if st=='PASS' else '❌'} {nm:36s}  {dt}")
print(f"\n通过 {ps} / 失败 {fs} / 总计 {len(results)}")
