"""
Example: gen_segment_2d（跳过360 + 跳过去背景 + 上传六视图）—— 2D 拆分（node_type=14）

与 gen_segment_2d.py 的区别：不依赖图生360产出的 model_id，直接上传本地原画，
并同时跳过 360 前置（skip_360_preprocess）与去背景预处理（skip_remove_background），
原始图原样送拆分算法，不再经过任何图像预处理。

视图按需传入：split_type=2（多视图）支持 1~6 个视图，素材缺失的视图留空即可，
后端按实际传入的视图投递；只有正视图也能跑（等价于正视图拆分）。
本示例会把 assets 目录下存在的视图全部带上，缺哪个就跳过哪个。

Usage:
    VISVISE_APP_ID=xxx VISVISE_SECRET_KEY=xxx VISVISE_RTX=xxx VISVISE_ENV=prod \
    SEG_ASSETS_DIR=examples/assets python examples/gen_segment_2d_skip360.py
"""

import os
import sys
from pathlib import Path

import logging

logging.basicConfig(level=logging.DEBUG)  # 查看详细请求/响应日志

# 或只开启 visvise 相关日志
logging.getLogger("visvise").setLevel(logging.INFO)

sys.path.insert(0, str(Path(__file__).parent.parent))

from visvise import Environment, VisviseClient, SegmentSplitType, View

APP_ID     = os.environ["VISVISE_APP_ID"]
SECRET_KEY = os.environ["VISVISE_SECRET_KEY"]
RTX        = os.environ["VISVISE_RTX"]
ENV        = os.environ.get("VISVISE_ENV", "prod")
ENV_MAP    = {"prod": Environment.PROD, "test": Environment.TEST, "dev": Environment.DEV}

# 六视图素材目录（默认 examples/assets，可用 SEG_ASSETS_DIR 覆盖）
ASSETS_DIR = Path(os.environ.get("SEG_ASSETS_DIR", Path(__file__).parent / "assets"))

# 六个视图：本地文件路径，SDK 自动上传 COS
VIEW_FILES = [
    ("main_view", "main_view.png"),
    ("back_view", "back_view.png"),
    ("left_view", "left_view.png"),
    ("right_view", "right_view.png"),
    ("top_view", "top_view.png"),
    ("bottom_view", "bottom_view.png"),
]


def build_input_view() -> View:
    """逐个探测六视图素材，存在则带上，不存在则跳过该视图。"""
    kwargs = {}
    for field, filename in VIEW_FILES:
        path = ASSETS_DIR / filename
        if path.is_file():
            print(f"  [view] {path}")
            kwargs[field] = str(path)
        else:
            print(f"  [skip] 素材不存在，跳过该视图: {path}")
    if not kwargs.get("main_view"):
        raise SystemExit("[gen_segment_2d_skip360] 正视图 main_view.png 必传")
    return View(**kwargs)


def main():
    client = VisviseClient(APP_ID, SECRET_KEY, env=ENV_MAP[ENV])  # noqa

    input_view = build_input_view()

    print("[gen_segment_2d_skip360] 上传原画并跳过 360 前置 / 去背景，直接 2D 拆分...")

    def on_thinking(content: str):
        print(f"  [thinking] {content}", flush=True)

    seg_model_id = client.gen_segment_2d(
        input_view=input_view,
        split_type=SegmentSplitType.FOUR_VIEW,  # 2 多视图拆分（按实际传入的视图，1~6 个）
        skip_360_preprocess=True,               # 跳过图生360前置，直接用 input_view 拆分
        skip_remove_background=True,            # 跳过去背景，原始图直接送算法
        # 可选：拆解 plan（json 文件），本地路径自动上传；不传时算法自行推理
        decomposition_plan=os.environ.get("SEG_DECOMPOSITION_PLAN") or None,
        name="example_gen_segment_2d_skip360",
        on_thinking=on_thinking,
        rtx=RTX,
    )
    print(f"[gen_segment_2d_skip360] 分割完成，model_id={seg_model_id}")
    print("  → 可作为图生中模/低模的 segment_model_id 参数使用")


if __name__ == "__main__":
    main()
