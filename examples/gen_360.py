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
RTX        = os.environ["VISVISE_RTX"]
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
        name="example_gen_360",
        rtx=RTX,
    )
    print(f"[gen_360] 任务已创建，model_id={model_id}")

    # gen_360 还支持以下可选参数（与后端 ImageGen360Params 一一对应）：
    #
    #   prompt="一个穿着盔甲的骑士",          # 文本提示词
    #   enable_head_refinement=True,          # 脸部增强
    #   aspect_ratio="1:1",                   # 画面比例
    #   enable_background_removal=True,       # 去背景
    #   seed=1234,                            # 随机种子
    #   enable_15deg=True,                    # 矫正透视
    #   style=ImageGen360Style.GRAY_MODEL,    # 风格（仅 VISVISE 自研模型支持）
    #   extra_references=[                    # 参考图（图片自动上传 COS）
    #       ImageGen360ExtraReference(path=str(ASSETS / "main_view.png"), prompt="参考图说明"),
    #   ],
    #   revision=ImageGen360Revision(         # 续改参数（视图自动上传 COS）
    #       caption="上一次返回的 caption 全文",
    #       prompt="本次修改指令",
    #       views=ImageGen360RevisionViews(main_view=str(MAIN_VIEW)),
    #   ),
    #   back_view=..., left_view=..., right_view=...,   # 额外视图

    print("[gen_360] 等待完成...")
    model = client.wait_model(model_id, interval=3, timeout=300, rtx=RTX)

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
