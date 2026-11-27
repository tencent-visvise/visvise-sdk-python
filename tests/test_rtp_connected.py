"""重拓扑-连通体（node_type=19）在线测试脚本。

对齐 Go SDK 的 ``tests/rtp_connected_test.go``，覆盖两段式自研（VV）重拓扑链路：

1. ``gen_rtp_connected``  创建连通体分组任务（node_type=19）并等待完成
2. ``save_rtp_connected`` 保存前端编辑后的连通体产物，得到新的连通体资产 ID
3. ``gen_retopology``     以保存得到的 model_id 作为 parent_model_id 发起第二段重拓扑

前置环境变量：

* ``VISVISE_APP_ID`` / ``VISVISE_SECRET_KEY`` / ``VISVISE_RTX``  必填
* ``VISVISE_RTP_CONNECTED_MODEL_ID``  可选，已有的第一段连通体资产 ID（用于跳过步骤 1）
* ``VISVISE_RTP_CONNECTED_ZIP``        可选，前端编辑后重新打包的连通体产物 zip
                                         （本地路径或 VISVISE 平台 COS URL）

运行::

    python tests/test_rtp_connected.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from visvise import Environment, FaceType, OutputModelFormat, VisviseClient  # noqa: E402

APP_ID = os.environ.get("VISVISE_APP_ID", "")
SECRET_KEY = os.environ.get("VISVISE_SECRET_KEY", "")
RTX = os.environ.get("VISVISE_RTX", "")
ENV = os.environ.get("VISVISE_ENV", "prod")
ENV_MAP = {"prod": Environment.PROD, "test": Environment.TEST, "dev": Environment.DEV}

ASSETS = Path(__file__).parent / "assets"
# 素材可能放在 tests/assets 或 examples/assets，两者取先存在者
if not (ASSETS / "high_model.fbx").is_file():
    _alt = Path(__file__).parent.parent / "examples" / "assets"
    if (_alt / "high_model.fbx").is_file():
        ASSETS = _alt

results: list[tuple[str, str, str]] = []


def ok(name: str, detail: str = "") -> None:
    results.append(("PASS", name, detail))
    print(f"PASS [{name}]", flush=True)
    if detail:
        print(f"  {detail}", flush=True)


def fail(name: str, reason: str) -> None:
    results.append(("FAIL", name, reason))
    print(f"FAIL [{name}]: {reason}", flush=True)


def run(name: str, fn) -> None:
    """run 执行单个测试用例，异常统一记为 FAIL。"""
    try:
        fn()
    except Exception as e:  # noqa: BLE001
        fail(name, f"{type(e).__name__}: {e}")


def t_gen_rtp_connected(client: VisviseClient) -> None:
    """t_gen_rtp_connected 创建连通体分组任务（node_type=19）。"""
    model_path = ASSETS / "high_model.fbx"
    if not model_path.is_file():
        fail("gen_rtp_connected", f"素材不存在: {model_path}")
        return

    model_id = client.gen_rtp_connected(
        model_path=str(model_path),
        name="test_gen_rtp_connected",
        rtx=RTX,
    )
    assert model_id, "gen_rtp_connected 返回空 model_id"
    ok("gen_rtp_connected", f"model_id={model_id}")

    print("  等待连通体分组完成...", flush=True)
    try:
        model = client.wait_model(model_id, interval=5, timeout=900, rtx=RTX)
    except Exception as e:  # noqa: BLE001
        fail("gen_rtp_connected 等待完成", f"{type(e).__name__}: {e}")
        return
    ok("gen_rtp_connected 等待完成", f"output_model={model.output_model}")


def t_save_rtp_connected(client: VisviseClient) -> None:
    """t_save_rtp_connected 保存前端编辑后的连通体产物。"""
    source_model_id = os.environ.get("VISVISE_RTP_CONNECTED_MODEL_ID", "")
    edited_zip = os.environ.get("VISVISE_RTP_CONNECTED_ZIP", "")
    if not source_model_id or not edited_zip:
        fail(
            "save_rtp_connected",
            "需要 VISVISE_RTP_CONNECTED_MODEL_ID / VISVISE_RTP_CONNECTED_ZIP 环境变量",
        )
        return

    saved_id = client.save_rtp_connected(
        source_model_id,
        edited_zip,
        "test_rtp_connected_saved",
        rtx=RTX,
    )
    assert saved_id, "save_rtp_connected 返回空 model_id"
    ok("save_rtp_connected", f"model_id={saved_id}")


def t_gen_retopology_with_parent(client: VisviseClient) -> None:
    """t_gen_retopology_with_parent 第二段重拓扑（parent_model_id 指向连通体资产）。"""
    parent_model_id = os.environ.get("VISVISE_RTP_CONNECTED_MODEL_ID", "")
    edited_zip = os.environ.get("VISVISE_RTP_CONNECTED_ZIP", "")
    if not parent_model_id or not edited_zip:
        fail(
            "gen_retopology (parent_model_id)",
            "需要 VISVISE_RTP_CONNECTED_MODEL_ID / VISVISE_RTP_CONNECTED_ZIP 环境变量",
        )
        return

    model_id = client.gen_retopology(
        edited_zip,
        algorithm_model="VV-RTP-V1.5.0",
        output_model_format=OutputModelFormat.FBX,
        face_type=FaceType.QUAD,
        face_num=10000,
        smooth_strength=1.0,
        parent_model_id=parent_model_id,
        name="test_gen_retopology_vv",
        rtx=RTX,
    )
    assert model_id, "gen_retopology 返回空 model_id"
    ok("gen_retopology (parent_model_id)", f"parent={parent_model_id} model_id={model_id}")


def main() -> int:
    """main 入口：逐个执行用例并输出汇总。"""
    if not APP_ID or not SECRET_KEY or not RTX:
        print("需要环境变量 VISVISE_APP_ID / VISVISE_SECRET_KEY / VISVISE_RTX")
        return 2

    client = VisviseClient(APP_ID, SECRET_KEY, env=ENV_MAP.get(ENV, Environment.PROD))

    print("\n=== gen_rtp_connected (node_type=19) ===", flush=True)
    run("gen_rtp_connected", lambda: t_gen_rtp_connected(client))

    print("\n=== save_rtp_connected ===", flush=True)
    run("save_rtp_connected", lambda: t_save_rtp_connected(client))

    print("\n=== gen_retopology (parent_model_id) ===", flush=True)
    run("gen_retopology (parent_model_id)", lambda: t_gen_retopology_with_parent(client))

    print("\n" + "=" * 60, flush=True)
    print("RTP CONNECTED TEST SUMMARY", flush=True)
    print("=" * 60, flush=True)
    passed = sum(1 for s, _, _ in results if s == "PASS")
    failed = sum(1 for s, _, _ in results if s == "FAIL")
    print(f"Total: {len(results)}  PASS: {passed}  FAIL: {failed}", flush=True)
    for s, n, d in results:
        mark = "OK" if s == "PASS" else "XX"
        print(f"  [{mark}] {n}", flush=True)
        if s == "FAIL":
            print(f"       {d}", flush=True)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
