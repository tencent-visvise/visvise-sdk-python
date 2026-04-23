"""
Example: gen_mesh_refine —— 重布线/布线优化（node_type=10）

对模型网格进行布线重建优化。
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from visvise import Environment, VisviseClient

APP_ID     = os.environ["VISVISE_APP_ID"]
SECRET_KEY = os.environ["VISVISE_SECRET_KEY"]
ENV        = os.environ.get("VISVISE_ENV", "prod")
ENV_MAP    = {"prod": Environment.PROD, "test": Environment.TEST, "dev": Environment.DEV}

ASSETS = Path(__file__).parent / "assets"


def main():
    client = VisviseClient(APP_ID, SECRET_KEY, env=ENV_MAP[ENV])

    print("[gen_mesh_refine] 开始重布线...")

    model_id = client.gen_mesh_refine(
        model_path=str(ASSETS / "high_model.fbx"),
        algorithm_model="VISVISE-MeshRefine-V1.0.0",
        input_model_format="fbx",
        name="example_gen_mesh_refine",
    )
    print(f"[gen_mesh_refine] 任务已创建，model_id={model_id}")

    model = client.wait_model(model_id, interval=5, timeout=900)
    print(f"[gen_mesh_refine] 生成成功！耗时 {model.time_cost}s")
    print(f"  output_model : {model.output_model}")


if __name__ == "__main__":
    main()
