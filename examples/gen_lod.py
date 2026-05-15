"""
Example: gen_lod —— LOD 减面（node_type=2）

gen_times=1 表示不抽卡，生成单个版本。
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from visvise import Environment, VisviseClient, FaceType, OutputModelFormat
from visvise.models import ReduceFace

APP_ID     = os.environ["VISVISE_APP_ID"]
SECRET_KEY = os.environ["VISVISE_SECRET_KEY"]
RTX        = os.environ["VISVISE_RTX"]
ENV        = os.environ.get("VISVISE_ENV", "prod")
ENV_MAP    = {"prod": Environment.PROD, "test": Environment.TEST, "dev": Environment.DEV}

ASSETS = Path(__file__).parent / "assets"


def main():
    client = VisviseClient(APP_ID, SECRET_KEY, env=ENV_MAP[ENV])  # noqa

    print("[gen_lod] 开始 LOD 减面...")

    model_ids = client.gen_lod(
        model_path=str(ASSETS / "tex_model.obj"),
        algorithm_model="VISVISE-LOD-V1.0.0",
        reduce_faces=[
            ReduceFace(reduce_level=1, reduce_percent=50, face_type=FaceType.QUAD),
            ReduceFace(reduce_level=2, reduce_percent=25, face_type=FaceType.QUAD),
            ReduceFace(reduce_level=3, reduce_percent=13, face_type=FaceType.QUAD),
        ],
        output_model_format=OutputModelFormat.FBX,
        gen_times=1,
        name="example_gen_lod",
        rtx=RTX,
    )
    print(f"[gen_lod] 任务已创建，model_ids={model_ids}")

    for mid in model_ids:
        model = client.wait_model(mid, interval=5, timeout=600, rtx=RTX)
        print(f"[gen_lod] {mid} 生成成功！耗时 {model.time_cost}s")
        if model.lod_output:
            for lf in model.lod_output.lod_files:
                print(f"  LOD{lf.reduce_level}: {lf.download_url}")
        else:
            print(f"  output_model: {model.output_model}")


if __name__ == "__main__":
    main()
