"""
Example: gen_video_motion —— 视频生动画（node_type=4）

从视频中提取动作数据，驱动 3D 模型生成动画。
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from visvise import Environment, VisviseClient, OutputModelFormat

APP_ID     = os.environ["VISVISE_APP_ID"]
SECRET_KEY = os.environ["VISVISE_SECRET_KEY"]
UID        = os.environ["VISVISE_UID"]
ENV        = os.environ.get("VISVISE_ENV", "prod")
ENV_MAP    = {"prod": Environment.PROD, "test": Environment.TEST, "dev": Environment.DEV}

ASSETS = Path(__file__).parent / "assets"


def main():
    client = VisviseClient(APP_ID, SECRET_KEY, UID, env=ENV_MAP[ENV])  # noqa

    print("[gen_video_motion] 开始视频生动画...")

    model_id = client.gen_video_motion(
        model_path=str(ASSETS / "animation_model.fbx"),
        video_path=str(ASSETS / "animation_video.mp4"),
        algorithm_model="VISVISE-FramingAI-Base-V1.5.0",
        output_model_format=OutputModelFormat.FBX,
        with_hand=True,
        name="example_gen_video_motion",
    )
    print(f"[gen_video_motion] 任务已创建，model_id={model_id}")

    model = client.wait_model(model_id, interval=5, timeout=900)
    print(f"[gen_video_motion] 生成成功！耗时 {model.time_cost}s")
    print(f"  output_model : {model.output_model}")


if __name__ == "__main__":
    main()
