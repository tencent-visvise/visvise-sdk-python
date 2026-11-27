"""
Example: gen_retopology —— 重拓扑（node_type=1）

对高面数模型进行拓扑优化。
混元模型传 detail_level，VISVISE 自研模型传 face_num，二选一。
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from visvise import Environment, VisviseClient, FaceType, DetailLevel, OutputModelFormat

APP_ID     = os.environ["VISVISE_APP_ID"]
SECRET_KEY = os.environ["VISVISE_SECRET_KEY"]
RTX        = os.environ["VISVISE_RTX"]
ENV        = os.environ.get("VISVISE_ENV", "prod")
ENV_MAP    = {"prod": Environment.PROD, "test": Environment.TEST, "dev": Environment.DEV}

ASSETS = Path(__file__).parent / "assets"


def main():
    client = VisviseClient(APP_ID, SECRET_KEY, env=ENV_MAP[ENV])  # noqa

    print("[gen_retopology] 开始重拓扑...")

    model_id = client.gen_retopology(
        model_path=str(ASSETS / "high_model.fbx"),
        algorithm_model="hunyuan3D-RTP-v1.5",
        output_model_format=OutputModelFormat.FBX,
        face_type=FaceType.QUAD,
        detail_level=DetailLevel.HIGH,     # 混元模型用 detail_level
        name="example_gen_retopology",
        rtx=RTX,
    )
    print(f"[gen_retopology] 任务已创建，model_id={model_id}")

    model = client.wait_model(model_id, interval=5, timeout=900, rtx=RTX)
    print(f"[gen_retopology] 生成成功！耗时 {model.time_cost}s")
    print(f"  output_model : {model.output_model}")


# VISVISE 自研（VV）模型为两段式：先用 gen_rtp_connected 生成连通体分组产物，
# 前端编辑并通过 save_rtp_connected 保存后，以保存得到的 model_id 作为 parent_model_id：
#
#   connected_id = client.gen_rtp_connected(str(ASSETS / "high_model.fbx"), rtx=RTX)
#   saved_id = client.save_rtp_connected(connected_id, "edited_connected.zip",
#                                       "example_rtp_connected_saved", rtx=RTX)
#   model_id = client.gen_retopology(
#       "edited_connected.zip",
#       algorithm_model="VV-RTP-V1.5.0",
#       face_num=10000,             # VISVISE 自研模型用 face_num
#       smooth_strength=1.0,        # 平滑强度
#       parent_model_id=saved_id,   # 第一段保存后的连通体资产 ID
#       name="example_gen_retopology_vv",
#       rtx=RTX,
#   )
#
# 完整示例见 gen_rtp_connected.py


if __name__ == "__main__":
    main()
