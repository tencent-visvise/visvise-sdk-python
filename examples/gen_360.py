"""
Example: gen_360 —— 图生360（生成多视图）

从单张图片生成 360° 多视图，输出结果可作为图生高模/中模/低模的输入。
"""

import os
import sys
from pathlib import Path

# 将 SDK 根目录加入路径（开发模式运行时）
sys.path.insert(0, str(Path(__file__).parent.parent))

from visvise import Environment, VisviseClient

# ── 从环境变量读取鉴权信息 ──────────────────────────────────────────────
APP_ID     = os.environ["VISVISE_APP_ID"]
SECRET_KEY = os.environ["VISVISE_SECRET_KEY"]
ENV        = os.environ.get("VISVISE_ENV", "prod")

ENV_MAP = {"prod": Environment.PROD, "test": Environment.TEST, "dev": Environment.DEV}

# ── 素材路径 ────────────────────────────────────────────────────────────
ASSETS = Path(__file__).parent / "assets"
MAIN_VIEW = ASSETS / "main_view.png"


def main():
    client = VisviseClient(APP_ID, SECRET_KEY, env=ENV_MAP[ENV])  # noqa

    print(f"[gen_360] 开始生成多视图，输入图片：{MAIN_VIEW}")

    model_id = client.gen_360(
        main_view=str(MAIN_VIEW),
        algorithm_model="VISVISE-MultiView-V1.0.0",
        name="example_gen_360",
    )
    print(f"[gen_360] 任务已创建，model_id={model_id}")

    print("[gen_360] 等待完成...")
    model = client.wait_model(model_id, interval=3, timeout=300)

    output = model.image_gen_360_output
    print(f"[gen_360] 生成成功！耗时 {model.time_cost}s")
    if output and output.output_view:
        v = output.output_view
        print(f"  main_view  : {v.main_view}")
        print(f"  back_view  : {v.back_view}")
        print(f"  left_view  : {v.left_view}")
        print(f"  right_view : {v.right_view}")
    if output and output.horizontal_view_video:
        print(f"  旋转视频   : {output.horizontal_view_video}")


if __name__ == "__main__":
    main()
