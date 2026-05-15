"""
Example: gen_rigging —— 骨骼架设（node_type=5）

为输入的 3D 模型自动生成骨骼结构。
SDK 内部自动构建 JSON 参数文件并打包成 zip 上传。
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

    print("[gen_rigging] 开始骨骼架设...")

    # SDK 自动将 rigging_model.fbx + 参数 JSON 打包成 zip 上传
    # 无需手动准备 zip 包
    model_id = client.gen_rigging(
        model_path=str(ASSETS / "rigging_model.fbx"),
        algorithm_model="VISVISE-GoRigging-V1.0.0",
        mesh_category="humanoid",           # humanoid（人形）或 tetrapod（四足）
        name="example_gen_rigging",
        rtx=RTX,
    )
    print(f"[gen_rigging] 任务已创建，model_id={model_id}")

    model = client.wait_model(model_id, interval=5, timeout=600, rtx=RTX)
    print(f"[gen_rigging] 生成成功！耗时 {model.time_cost}s")
    print(f"  output_model : {model.output_model}")


if __name__ == "__main__":
    main()
