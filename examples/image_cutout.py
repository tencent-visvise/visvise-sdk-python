"""
Example: image_cutout —— 图片抠图（去背景）。

同步接口：只返回处理结果图片，不创建模型资产。
抠图为同步处理，服务端算法最长可能耗时数分钟，请把客户端 timeout 调大（这里用 300 秒）。
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from visvise import Environment, ImageCutoutMode, VisviseClient

APP_ID     = os.environ["VISVISE_APP_ID"]
SECRET_KEY = os.environ["VISVISE_SECRET_KEY"]
RTX        = os.environ["VISVISE_RTX"]
ENV        = os.environ.get("VISVISE_ENV", "prod")
ENV_MAP    = {"prod": Environment.PROD, "test": Environment.TEST, "dev": Environment.DEV}

ASSETS = Path(__file__).parent / "assets"

# 抠图为同步接口，算法最长可能耗时数分钟，超时需放大
CUTOUT_TIMEOUT = 300


def main():
    client = VisviseClient(APP_ID, SECRET_KEY, env=ENV_MAP[ENV], timeout=CUTOUT_TIMEOUT)

    # ① 默认模式（mode 省略 = 1，直接抠图，输出透明背景）
    print("[image_cutout] 开始直接抠图...")
    result = client.image_cutout(
        [str(ASSETS / "main_view.png")],
        background_color="white",
        rtx=RTX,
    )
    print(f"[image_cutout] 直接抠图完成，最终底色={result.background_color}")
    for url in result.image_list:
        print(f"  {url}")

    # ② 纯色底抠图（mode=2），可一次传多张图片
    print("[image_cutout] 开始纯色底抠图...")
    solid = client.image_cutout(
        [
            str(ASSETS / "main_view.png"),
            str(ASSETS / "back_view.png"),
        ],
        mode=ImageCutoutMode.SOLID_COLOR,
        background_color="red",
        rtx=RTX,
    )
    print(f"[image_cutout] 纯色底抠图完成，最终底色={solid.background_color}")
    for url in solid.image_list:
        print(f"  {url}")

    # ③ 换底并抠图（mode=3）
    print("[image_cutout] 开始换底并抠图...")
    replace = client.image_cutout(
        [str(ASSETS / "main_view.png")],
        mode=ImageCutoutMode.REPLACE,
        background_color="blue",
        rtx=RTX,
    )
    print(f"[image_cutout] 换底并抠图完成，最终底色={replace.background_color}")
    for url in replace.image_list:
        print(f"  {url}")


if __name__ == "__main__":
    main()
