"""
Example: gen_pose —— 批量图生 Pose（node_type=12）

从参考图片中提取姿态，驱动 3D 模型生成对应 Pose。
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from visvise import Environment, VisviseClient, OutputModelFormat

APP_ID     = os.environ["VISVISE_APP_ID"]
SECRET_KEY = os.environ["VISVISE_SECRET_KEY"]
RTX        = os.environ["VISVISE_RTX"]
ENV        = os.environ.get("VISVISE_ENV", "prod")
ENV_MAP    = {"prod": Environment.PROD, "test": Environment.TEST, "dev": Environment.DEV}

ASSETS = Path(__file__).parent / "assets"


def main():
    client = VisviseClient(APP_ID, SECRET_KEY, env=ENV_MAP[ENV])  # noqa

    print("[gen_pose] 开始图生 Pose...")

    model_ids = client.gen_pose(
        model_path=str(ASSETS / "animation_model.fbx"),
        input_images=[
            str(ASSETS / "pose_ref.png"),
        ],
        algorithm_model="VISVISE-PosingAI-V1.0.0",
        output_model_format=OutputModelFormat.FBX,
        name="example_gen_pose",
        rtx=RTX,
    )
    print(f"[gen_pose] 任务已创建，model_ids={model_ids}")

    for mid in model_ids:
        model = client.wait_model(mid, interval=3, timeout=600, rtx=RTX)
        print(f"[gen_pose] {mid} 生成成功！耗时 {model.time_cost}s")
        print(f"  output_model : {model.output_model}")


if __name__ == "__main__":
    main()
