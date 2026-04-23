"""
Example: gen_texture —— 贴图纹理生成（node_type=8）

为 3D 模型生成贴图纹理。
input_view.main_view 和 prompt 必须传其中一个，可同时传入。
本示例同时传入四视图和 prompt 以获得最佳效果。
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

    print("[gen_texture] 开始贴图纹理生成...")

    # 上传四视图，获取 COS URL（SDK 自动处理上传）
    # 此处演示先用 gen_360 上传图片，再传入 COS URL；
    # 也可直接传本地路径，SDK 会自动上传。
    input_view = View(
        main_view=str(ASSETS / "main_view.png"),
        back_view=str(ASSETS / "back_view.png"),
        left_view=str(ASSETS / "left_view.png"),
        right_view=str(ASSETS / "right_view.png"),
    )

    model_id = client.gen_texture(
        model_path=str(ASSETS / "high_model.fbx"),
        algorithm_model="hunyuan3D-TEX-v2.0",
        input_view=input_view,
        resolution=2048,
        unwarp_uv=False,
        name="example_gen_texture",
    )
    print(f"[gen_texture] 任务已创建，model_id={model_id}")

    model = client.wait_model(model_id, interval=5, timeout=900)
    print(f"[gen_texture] 生成成功！耗时 {model.time_cost}s")
    print(f"  output_model : {model.output_model}")


if __name__ == "__main__":
    main()
