"""
Example: gen_uv —— UV 展开（node_type=9）
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from visvise import Environment, VisviseClient

APP_ID     = os.environ["VISVISE_APP_ID"]
SECRET_KEY = os.environ["VISVISE_SECRET_KEY"]
RTX        = os.environ["VISVISE_RTX"]
ENV        = os.environ.get("VISVISE_ENV", "prod")
ENV_MAP    = {"prod": Environment.PROD, "test": Environment.TEST, "dev": Environment.DEV}

ASSETS = Path(__file__).parent / "assets"


def main():
    client = VisviseClient(APP_ID, SECRET_KEY, env=ENV_MAP[ENV])  # noqa

    print("[gen_uv] 开始 UV 展开...")

    model_id = client.gen_uv(
        model_path=str(ASSETS / "tex_model.obj"),
        algorithm_model="hunyuan3D-UV-v2.0",
        enable_auto_smoothing=True,
        name="example_gen_uv",
        rtx=RTX,
    )
    print(f"[gen_uv] 任务已创建，model_id={model_id}")

    model = client.wait_model(model_id, interval=5, timeout=600, rtx=RTX)
    print(f"[gen_uv] 生成成功！耗时 {model.time_cost}s")
    print(f"  output_model : {model.output_model}")


if __name__ == "__main__":
    main()
