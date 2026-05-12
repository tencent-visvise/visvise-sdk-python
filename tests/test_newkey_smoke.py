"""使用新 key 在 DEV 环境随便跑几个 gen_xxx，验证账号可用。"""

import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from visvise import VisviseClient, Environment, OutputModelFormat, FaceType, DetailLevel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
)

APP_ID     = "vsa_0ba7a1ad201511d6"
SECRET_KEY = "vss_22667757bee57cbc88abf4d9c04cea716d81251def529779"
UID        = "p_ck6a498bch7dzu5xn98r8ietii7kwp47sv7mjefyhru283p2wr7pp"
ASSETS     = Path(__file__).parent / "assets"

client = VisviseClient(APP_ID, SECRET_KEY, UID, env=Environment.DEV)


def read(p): return (ASSETS / p).read_bytes()


results = []


def run(name, fn):
    print(f"\n━━━━━ {name} ━━━━━")
    try:
        r = fn()
        results.append(("PASS", name, str(r)))
        print(f"✅ PASS [{name}] → {r}")
    except Exception as e:
        results.append(("FAIL", name, f"{type(e).__name__}: {e}"))
        print(f"❌ FAIL [{name}]: {type(e).__name__}: {e}")


print("=" * 70)
print(f" 新账号 DEV 环境冒烟测试 (app_id={APP_ID})")
print("=" * 70)

# 0. 先看下账号配额
try:
    quota = client.api.get_user_quota()
    print(f"\n剩余配额: {quota.quota}, 服务器时间戳: {quota.server_ts}\n")
except Exception as e:
    print(f"\n⚠️  查配额失败: {e}\n")

# 1. 图生 360（PNG bytes）
run("gen_360 (bytes)", lambda: client.gen_360(
    main_view=read("main_view.png"),
    name="newkey_test_gen_360",
))

# 2. 图生高模（本地 path）
run("gen_high_model (path)", lambda: client.gen_high_model(
    main_view=str(ASSETS / "main_view.png"),
    output_model_format=OutputModelFormat.FBX,
    face_type=FaceType.TRIANGLE,
    name="newkey_test_gen_high",
))

# 3. 重拓扑（混元，必须 detail_level）
run("gen_retopology (path)", lambda: client.gen_retopology(
    model_path=str(ASSETS / "rigging_model.fbx"),
    output_model_format=OutputModelFormat.FBX,
    face_type=FaceType.QUAD,
    detail_level=DetailLevel.MEDIUM,
    name="newkey_test_gen_retop",
))

# 4. UV 展开（OBJ bytes）
run("gen_uv (bytes)", lambda: client.gen_uv(
    model_path=read("tex_model.obj"),
    name="newkey_test_gen_uv",
))

# 5. 文生动画（一次返回 4 个 ID）
run("gen_text_motion (bytes + prompt)", lambda: client.gen_text_motion(
    model_path=read("animation_model.fbx"),
    prompt="一个人在跳街舞",
    output_model_format=OutputModelFormat.FBX,
    name="newkey_test_gen_text_motion",
))

print("\n" + "=" * 70)
print(" 汇总")
print("=" * 70)
ps = sum(1 for r in results if r[0] == "PASS")
fs = sum(1 for r in results if r[0] == "FAIL")
for st, nm, dt in results:
    icon = "✅" if st == "PASS" else "❌"
    print(f"  {icon} {nm:36s}  {dt}")
print(f"\n通过 {ps} / 失败 {fs} / 总计 {len(results)}")
