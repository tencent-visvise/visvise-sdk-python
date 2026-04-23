"""
Example: gen_high_model —— 图生高模（node_type=11）

使用四视图生成高精度 3D 模型。
四视图通常由 gen_360.py 的输出获取，此处直接使用本地素材演示。
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from visvise import Environment, VisviseClient
from visvise.models import View

APP_ID     = os.environ["VISVISE_APP_ID"]
SECRET_KEY = os.environ["VISVISE_SECRET_KEY"]
ENV        = os.environ.get("VISVISE_ENV", "prod")
ENV_MAP    = {"prod": Environment.PROD, "test": Environment.TEST, "dev": Environment.DEV}

ASSETS = Path(__file__).parent / "assets"


def main():
    client = VisviseClient(APP_ID, SECRET_KEY, env=ENV_MAP[ENV])

    print("[gen_high_model] 开始生成高模...")

    model_id = client.gen_high_model(
        main_view=str(ASSETS / "main_view.png"),
        back_view=str(ASSETS / "back_view.png"),
        left_view=str(ASSETS / "left_view.png"),
        right_view=str(ASSETS / "right_view.png"),
        algorithm_model="hunyuan3D-v3.1",
        output_model_format="fbx",
        face_type=1,
        name="example_gen_high_model",
    )
    print(f"[gen_high_model] 任务已创建，model_id={model_id}")

    model = client.wait_model(model_id, interval=5, timeout=900)
    print(f"[gen_high_model] 生成成功！耗时 {model.time_cost}s")
    print(f"  output_model : {model.output_model}")


if __name__ == "__main__":
    main()
