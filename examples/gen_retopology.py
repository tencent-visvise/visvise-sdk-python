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


if __name__ == "__main__":
    main()
