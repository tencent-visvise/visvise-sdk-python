"""
Example: gen_texture —— 贴图纹理生成（node_type=8）

input_view 中的本地图片路径会被 SDK 自动上传到 COS。
input_view.main_view 和 prompt 必须传其中一个。
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
    client = VisviseClient(APP_ID, SECRET_KEY, env=ENV_MAP[ENV])  # noqa

    print("[gen_texture] 开始贴图纹理生成...")

    # 本地图片路径，SDK 内部自动上传到 COS
    input_view = View(
        main_view=str(ASSETS / "tex_ref_front.jpg"),
        back_view=str(ASSETS / "tex_ref_back.jpg"),
        left_view=str(ASSETS / "tex_ref_left.jpg"),
    )

    model_id = client.gen_texture(
        model_path=str(ASSETS / "tex_model.obj"),
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
