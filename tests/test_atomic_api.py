"""
原子 API 单元测试 —— client 未覆盖的接口

覆盖：get_user_quota / list_algorithm_model / get_text2motion_prompt_list
      remove_bg / download_model / delete_model / batch_delete_model
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path
from visvise import VisviseClient

APP_ID     = os.environ["VISVISE_APP_ID"]
SECRET_KEY = os.environ["VISVISE_SECRET_KEY"]
RTX        = os.environ["VISVISE_RTX"]
ASSETS     = Path(__file__).parent / "assets"

client = VisviseClient(APP_ID, SECRET_KEY)
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

# 1. get_user_quota
def t_quota():
    q = client.api.get_user_quota(rtx=RTX)
    assert isinstance(q.quota, int) and q.quota >= 0
    ok("get_user_quota", f"quota={q.quota}  server_ts={q.server_ts}")
run("get_user_quota", t_quota)

# 2. list_algorithm_model — 覆盖 6 个节点类型
def t_list_alg():
    for node_type, sub_type, label in [
        (7, None, "图生360"), (3, None, "图生高模"),
        (4, 1, "视频生动画"), (4, 2, "文生动画"),
        (5, None, "骨骼架设"), (2, None, "LOD"),
    ]:
        models = client.api.list_algorithm_model(node_type, sub_type, rtx=RTX)
        assert isinstance(models, list) and len(models) > 0, f"{label} 返回空列表"
        ok(f"list_algorithm_model {label}", f"first={models[0]}  count={len(models)}")
run("list_algorithm_model", t_list_alg)

# 3. get_text2motion_prompt_list — zh / en
def t_prompts():
    for lang in ["zh", "en"]:
        prompts = client.api.get_text2motion_prompt_list(language=lang, rtx=RTX)
        assert isinstance(prompts, list) and len(prompts) > 0
        ok(f"get_text2motion_prompt_list lang={lang}",
           f"count={len(prompts)}  first={prompts[0]!r}")
run("get_text2motion_prompt_list", t_prompts)

# 4. remove_bg — 上传本地图片后调用
def t_remove_bg():
    cos_url = client._resolve_file(str(ASSETS / "main_view.png"))
    result_url = client.api.remove_bg(cos_url, rtx=RTX)
    assert result_url.startswith("http"), f"URL 格式异常：{result_url!r}"
    ok("remove_bg", f"output_url={result_url[:80]}...")
run("remove_bg", t_remove_bg)

# 5. download_model — 用已有成功模型
KNOWN_MODEL_ID = "Model2026042300226056"
def t_download():
    url = client.api.download_model(KNOWN_MODEL_ID, rtx=RTX)
    assert url.startswith("http"), f"URL 格式异常：{url!r}"
    ok("download_model", f"url={url[:80]}...")
run("download_model", t_download)

# 6. delete_model + batch_delete_model — 先建临时任务再删
def t_delete():
    print("  创建 2 个临时任务...", flush=True)
    ids = client.api.batch_gen_pose(
        name="delete_test",
        input_model=client._resolve_file(str(ASSETS / "animation_model.fbx")),
        input_images=[
            client._resolve_file(str(ASSETS / "pose_ref.png")),
            client._resolve_file(str(ASSETS / "main_view.png")),
        ],
        params={"algorithm_model": "VISVISE-PosingAI-V1.0.0", "output_model_format": "fbx"},
        rtx=RTX,
    )
    assert len(ids) == 2, f"期望 2 个 id，实际：{ids}"
    print(f"  ids={ids}", flush=True)

    client.api.delete_model(ids[0], rtx=RTX)
    ok("delete_model", f"deleted {ids[0]}")

    client.api.batch_delete_model([ids[1]], rtx=RTX)
    ok("batch_delete_model", f"batch deleted {ids[1]}")

    # 验证已删除（查询不到）
    models, _ = client.api.get_model_list(model_id_list=ids, limit=10, rtx=RTX)
    remaining = {m.model_id for m in models}
    for mid in ids:
        assert mid not in remaining, f"{mid} 删除后仍能查到"
    ok("delete 验证（查询已消失）", f"ids={ids}")
run("delete_model + batch_delete_model", t_delete)

# SUMMARY
print("\n" + "="*60, flush=True)
print("ATOMIC API TEST SUMMARY", flush=True)
print("="*60, flush=True)
passed = sum(1 for s,*_ in results if s == "PASS")
failed = sum(1 for s,*_ in results if s == "FAIL")
print(f"Total: {len(results)}  PASS: {passed}  FAIL: {failed}", flush=True)
for s, n, d in results:
    mark = "OK" if s == "PASS" else "XX"
    print(f"  [{mark}] {n}", flush=True)
    if s == "FAIL": print(f"       {d}", flush=True)
