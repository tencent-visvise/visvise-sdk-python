"""
Example: gen_rtp_connected —— 重拓扑-连通体（node_type=19）

两段式自研（VV）重拓扑的第一段：对高面数模型做连通体分组，
产出连通体网格与分组数据（产物在资产的 output_model zip 中）。

完整链路：
  1. gen_rtp_connected：创建连通体分组任务（node_type=19）
  2. 等待完成，下载 output_model（连通体分组产物 zip）并在前端编辑连通体分组
  3. 将编辑结果重新打包成 zip 并上传到当前账号的 COS 目录
  4. save_rtp_connected：保存该产物，得到新的连通体资产 ID（node_type=19，status=3）
  5. gen_retopology：以保存得到的 model_id 作为 parent_model_id 发起第二段重拓扑（node_type=1）

Usage::

    VISVISE_APP_ID=xxx VISVISE_SECRET_KEY=xxx VISVISE_RTX=xxx python gen_rtp_connected.py

可选环境变量：
    VISVISE_RTP_CONNECTED_ZIP  前端编辑后重新打包的连通体产物 zip 路径（本地文件或 COS URL）
                                传入后本示例会继续执行「保存产物 + 第二段重拓扑」
"""

import os
import sys
from pathlib import Path

# 将 SDK 根目录加入路径（开发模式运行时）
sys.path.insert(0, str(Path(__file__).parent.parent))

from visvise import (  # noqa: E402
    Environment,
    FaceType,
    OutputModelFormat,
    VisviseClient,
)

# ── 从环境变量读取鉴权信息 ──────────────────────────────────────────────
APP_ID     = os.environ["VISVISE_APP_ID"]
SECRET_KEY = os.environ["VISVISE_SECRET_KEY"]
RTX        = os.environ["VISVISE_RTX"]
ENV        = os.environ.get("VISVISE_ENV", "prod")

ENV_MAP = {"prod": Environment.PROD, "test": Environment.TEST, "dev": Environment.DEV}

# ── 素材路径 ────────────────────────────────────────────────────────────
ASSETS = Path(__file__).parent / "assets"
MODEL_PATH = ASSETS / "high_model.fbx"


def main():
    """main 执行重拓扑-连通体两段式流程示例。"""
    client = VisviseClient(APP_ID, SECRET_KEY, env=ENV_MAP[ENV])  # noqa

    # ── 第一段：重拓扑-连通体 ────────────────────────────────────────────
    print("[gen_rtp_connected] 创建重拓扑-连通体任务（node_type=19）...")

    connected_id = client.gen_rtp_connected(
        model_path=str(MODEL_PATH),
        name="example_gen_rtp_connected",
        rtx=RTX,
    )
    print(f"[gen_rtp_connected] 任务已创建，model_id={connected_id}")

    print("[gen_rtp_connected] 等待完成...")
    connected = client.wait_model(connected_id, interval=5, timeout=900, rtx=RTX)
    print(f"[gen_rtp_connected] 连通体分组产物: {connected.output_model}")
    print("  请下载该 zip，在前端编辑连通体分组后重新打包上传到当前账号的 COS 目录，")
    print("  然后调用 save_rtp_connected 保存产物，并以返回的 model_id 作为重拓扑的 parent_model_id。")

    # ── 保存产物 + 第二段重拓扑 ─────────────────────────────────────────
    edited_zip = os.environ.get("VISVISE_RTP_CONNECTED_ZIP", "")
    if not edited_zip:
        print("\n未设置 VISVISE_RTP_CONNECTED_ZIP，跳过「保存产物 + 第二段重拓扑」。")
        return

    print("\n[save_rtp_connected] 保存编辑后的连通体产物...")
    saved_id = client.save_rtp_connected(
        connected_id,
        edited_zip,
        "example_rtp_connected_saved",
        rtx=RTX,
    )
    print(f"[save_rtp_connected] 保存成功，新的连通体资产 ID={saved_id}")

    print("[gen_retopology] 发起第二段重拓扑（node_type=1）...")
    rtp_id = client.gen_retopology(
        edited_zip,
        algorithm_model="VV-RTP-V1.5.0",
        output_model_format=OutputModelFormat.FBX,
        face_type=FaceType.QUAD,
        face_num=10000,             # VISVISE 自研模型用 face_num
        smooth_strength=1.0,        # 平滑强度
        parent_model_id=saved_id,   # 第一段保存后的连通体资产 ID
        name="example_gen_retopology_vv",
        rtx=RTX,
    )
    print(f"[gen_retopology] 任务已创建，model_id={rtp_id}")

    rtp_model = client.wait_model(rtp_id, interval=5, timeout=900, rtx=RTX)
    print(f"[gen_retopology] 生成成功！耗时 {rtp_model.time_cost}s")
    print(f"  output_model : {rtp_model.output_model}")


if __name__ == "__main__":
    main()
