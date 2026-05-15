"""
Example: gen_mid_model —— 图生中模（node_type=3）

中模要求四视图全部必传。
优先从环境变量 MV_360_MODEL_ID 读取 gen_360 的输出，自动提取四视图。
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from visvise import Environment, VisviseClient, FaceType, OutputModelFormat

APP_ID     = os.environ["VISVISE_APP_ID"]
SECRET_KEY = os.environ["VISVISE_SECRET_KEY"]
RTX        = os.environ["VISVISE_RTX"]
ENV        = os.environ.get("VISVISE_ENV", "prod")
ENV_MAP    = {"prod": Environment.PROD, "test": Environment.TEST, "dev": Environment.DEV}

ASSETS = Path(__file__).parent / "assets"


def strip_sign(url: str) -> str:
    return url.split("?")[0] if url else url


def main():
    client = VisviseClient(APP_ID, SECRET_KEY, env=ENV_MAP[ENV])  # noqa

    mv_model_id = os.environ.get("MV_360_MODEL_ID")
    if mv_model_id:
        print(f"[gen_mid_model] 从 gen_360 输出提取四视图 (model_id={mv_model_id})")
        models, _ = client.api.get_model_list(model_id_list=[mv_model_id], limit=10, rtx=RTX)
        out = models[0].image_gen_360_output.output_view
        main_view  = strip_sign(out.main_view)
        back_view  = strip_sign(out.back_view)
        left_view  = strip_sign(out.left_view)
        right_view = strip_sign(out.right_view)
    else:
        main_view  = os.environ.get("MV_MAIN",  str(ASSETS / "main_view.png"))
        back_view  = os.environ.get("MV_BACK",  str(ASSETS / "back_view.png"))
        left_view  = os.environ.get("MV_LEFT",  str(ASSETS / "left_view.png"))
        right_view = os.environ.get("MV_RIGHT", str(ASSETS / "right_view.png"))

    print("[gen_mid_model] 开始生成中模...")
    model_id = client.gen_mid_model(
        main_view=main_view,
        back_view=back_view,
        left_view=left_view,
        right_view=right_view,
        algorithm_model="VISVISE-MeshGen-V1.0.0",
        output_model_format=OutputModelFormat.FBX,
        face_type=FaceType.TRIANGLE,
        name="example_gen_mid_model",
        rtx=RTX,
    )
    print(f"[gen_mid_model] 任务已创建，model_id={model_id}")

    model = client.wait_model(model_id, interval=5, timeout=900, rtx=RTX)
    print(f"[gen_mid_model] 生成成功！耗时 {model.time_cost}s")
    print(f"  output_model : {model.output_model}")


if __name__ == "__main__":
    main()
