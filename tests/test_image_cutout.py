"""
图片抠图（image_cutout）集成测试。

覆盖：client.image_cutout（本地图片自动上传）
      client.api.image_cutout（原子接口，传入已上传的 COS URL）
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path
from visvise import ImageCutoutMode, VisviseClient, Environment

APP_ID     = os.environ["VISVISE_APP_ID"]
SECRET_KEY = os.environ["VISVISE_SECRET_KEY"]
RTX        = os.environ["VISVISE_RTX"]
ASSETS     = Path(__file__).parent / "assets"

# 抠图为同步接口，服务端算法最长可能耗时数分钟，超时需放大
client = VisviseClient(APP_ID, SECRET_KEY, env=Environment.TEST)
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


# 1. 高阶接口：本地图片自动上传 → 抠图（默认 mode=1，直接抠图）
def t_client_cutout():
    result = client.image_cutout(
        [str(ASSETS / "main_view.png")],
        background_color="white",
        rtx=RTX,
    )
    assert len(result.image_list) == 1, f"期望 1 张结果图，实际：{len(result.image_list)}"
    assert result.image_list[0].startswith("http"), f"URL 格式异常：{result.image_list[0]!r}"
    assert result.background_color, "background_color 不应为空"
    ok("client.image_cutout (mode=1)",
       f"background_color={result.background_color} url={result.image_list[0][:80]}...")
run("client.image_cutout (mode=1)", t_client_cutout)

# 2. 纯色底抠图（mode=2）
def t_solid_color():
    result = client.image_cutout(
        [str(ASSETS / "main_view.png")],
        mode=ImageCutoutMode.SOLID_COLOR,
        background_color="red",
        rtx=RTX,
    )
    assert len(result.image_list) == 1, f"期望 1 张结果图，实际：{len(result.image_list)}"
    ok("client.image_cutout (mode=2)",
       f"background_color={result.background_color} url={result.image_list[0][:80]}...")
run("client.image_cutout (mode=2)", t_solid_color)

# 3. 原子接口：传入已上传的 COS URL
def t_api_cutout():
    cos_url = client._resolve_file(str(ASSETS / "main_view.png"), rtx=RTX)
    result = client.api.image_cutout(
        [cos_url],
        ImageCutoutMode.DIRECT,
        "white",
        rtx=RTX,
    )
    assert len(result.image_list) == 1, f"期望 1 张结果图，实际：{len(result.image_list)}"
    # 兼容文档示例的字典式取值
    assert result["image_list"] == result.image_list
    ok("api.image_cutout",
       f"background_color={result['background_color']} url={result['image_list'][0][:80]}...")
run("api.image_cutout", t_api_cutout)

# 4. 非法 mode 本地拦截，不发起请求
def t_invalid_mode():
    try:
        client.api.image_cutout(["https://x"], 9, "white", rtx=RTX)
    except ValueError as e:
        ok("api.image_cutout 非法 mode 校验", str(e))
        return
    raise AssertionError("非法 mode 未被拦截")
run("api.image_cutout 非法 mode 校验", t_invalid_mode)

# SUMMARY
print("\n" + "="*60, flush=True)
print("IMAGE CUTOUT TEST SUMMARY", flush=True)
print("="*60, flush=True)
passed = sum(1 for s,*_ in results if s == "PASS")
failed = sum(1 for s,*_ in results if s == "FAIL")
print(f"Total: {len(results)}  PASS: {passed}  FAIL: {failed}", flush=True)
for s, n, d in results:
    mark = "OK" if s == "PASS" else "XX"
    print(f"  [{mark}] {n}", flush=True)
    if s == "FAIL": print(f"       {d}", flush=True)
