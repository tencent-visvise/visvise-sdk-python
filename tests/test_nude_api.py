"""
裸模拆分 / 模型自动合并 接口测试

覆盖：cond_part_autofit（裸模拆分）
      model_auto_merge（模型自动合并）

两者均为同步接口，不创建模型资产；服务端算法最长执行 5 分钟。
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path
from visvise import VisviseClient

APP_ID     = os.environ["VISVISE_APP_ID"]
SECRET_KEY = os.environ["VISVISE_SECRET_KEY"]
RTX        = os.environ["VISVISE_RTX"]
ASSETS     = Path(__file__).parent / "assets"

# 同步接口最长 5 分钟，客户端超时需放宽
client = VisviseClient(APP_ID, SECRET_KEY, timeout=330)
results = []

def ok(name, detail=""):
    results.append(("PASS", name, detail))
    print(f"PASS [{name}]", flush=True)
    if detail: print(f"  {detail}", flush=True)

def fail(name, reason):
    results.append(("FAIL", name, reason))
    print(f"FAIL [{name}]: {reason}", flush=True)

def run(name, fn):
    try: fn()
    except Exception as e: fail(name, str(e))

# 1. 裸模拆分
def t_cond_part_autofit():
    r = client.cond_part_autofit(
        original_part_mesh_path=str(ASSETS / "tex_model.obj"),      # 原始模型
        ref_mesh_path=str(ASSETS / "tex_model.obj"),                 # 参考模型
        replace_part_names={"无头身体裸模": "female_headless.obj"},  # 部件名 → 裸模文件名
        rtx=RTX,
    )
    assert r.output_obj_path.startswith("http"), f"output_obj_path 异常：{r.output_obj_path!r}"
    assert r["output_obj_path"] == r.output_obj_path, "dict 风格访问不一致"
    ok("cond_part_autofit",
       f"output_obj_path={r.output_obj_path[:80]}...  background_color={r.background_color!r}")
run("cond_part_autofit", t_cond_part_autofit)

# 2. 模型自动合并
def t_model_auto_merge():
    r = client.model_auto_merge(
        original_part_mesh_path=str(ASSETS / "parts.zip"),   # 部件 mesh 压缩包
        ref_mesh_path=str(ASSETS / "tex_model.obj"),         # 参考模型（补齐缺失部件）
        support_rotate=False,
        rtx=RTX,
    )
    assert r.output_obj_path.startswith("http"), f"output_obj_path 异常：{r.output_obj_path!r}"
    ok("model_auto_merge",
       f"output_obj_path={r.output_obj_path[:80]}...  elapsed={r.elapsed_time}s  "
       f"mean_iou={r.mean_bbox_iou}  ref_filled={r.ref_filled_parts}")
run("model_auto_merge", t_model_auto_merge)

# SUMMARY
print("\n" + "="*60, flush=True)
print("NUDE API TEST SUMMARY", flush=True)
print("="*60, flush=True)
passed = sum(1 for s,*_ in results if s == "PASS")
failed = sum(1 for s,*_ in results if s == "FAIL")
print(f"Total: {len(results)}  PASS: {passed}  FAIL: {failed}", flush=True)
for s, n, d in results:
    mark = "OK" if s == "PASS" else "XX"
    print(f"  [{mark}] {n}", flush=True)
    if s == "FAIL": print(f"       {d}", flush=True)
