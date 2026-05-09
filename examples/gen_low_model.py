"""
Example: gen_low_model —— 图生低模（node_type=13）

仅需主视图，其余视图可选。
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from visvise import Environment, VisviseClient

APP_ID     = os.environ["VISVISE_APP_ID"]
SECRET_KEY = os.environ["VISVISE_SECRET_KEY"]
UID        = os.environ["VISVISE_UID"]
ENV        = os.environ.get("VISVISE_ENV", "prod")
ENV_MAP    = {"prod": Environment.PROD, "test": Environment.TEST, "dev": Environment.DEV}

ASSETS = Path(__file__).parent / "assets"


def main():
    client = VisviseClient(APP_ID, SECRET_KEY, UID, env=ENV_MAP[ENV])  # noqa

    print("[gen_low_model] 开始生成低模...")

    model_id = client.gen_low_model(
        main_view=str(ASSETS / "main_view.png"),
        algorithm_model="Tripo-v1.0-快速生成",
        output_model_format="fbx",
        face_type=1,
        name="example_gen_low_model",
    )
    print(f"[gen_low_model] 任务已创建，model_id={model_id}")

    model = client.wait_model(model_id, interval=3, timeout=600)
    print(f"[gen_low_model] 生成成功！耗时 {model.time_cost}s")
    print(f"  output_model : {model.output_model}")


if __name__ == "__main__":
    main()
