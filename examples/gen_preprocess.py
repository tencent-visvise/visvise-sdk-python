"""
Example: gen_style_transfer / gen_patter_auto_remove —— 2D 预处理。

同步处理输入图片并保存为 2D 预处理资产（node_type=16），直接返回 model_id。
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from visvise import Environment, StyleType, VisviseClient

APP_ID     = os.environ["VISVISE_APP_ID"]
SECRET_KEY = os.environ["VISVISE_SECRET_KEY"]
RTX        = os.environ["VISVISE_RTX"]
ENV        = os.environ.get("VISVISE_ENV", "prod")
ENV_MAP    = {"prod": Environment.PROD, "test": Environment.TEST, "dev": Environment.DEV}

ASSETS = Path(__file__).parent / "assets"


def main():
    client = VisviseClient(APP_ID, SECRET_KEY, env=ENV_MAP[ENV])

    # 原画风格化
    print("[gen_preprocess] 开始原画风格化...")
    styled_id = client.gen_style_transfer(
        str(ASSETS / "preprocess.png"),
        style_type=StyleType.GRAYSCALE,
        name="example_gen_style_transfer",
        rtx=RTX,
    )
    print(f"[gen_preprocess] 原画风格化完成，model_id={styled_id}")

    # 智能去花纹
    print("[gen_preprocess] 开始智能去花纹...")
    patterned_id = client.gen_patter_auto_remove(
        str(ASSETS / "preprocess.png"),
        name="example_gen_patter_auto_remove",
        rtx=RTX,
    )
    print(f"[gen_preprocess] 智能去花纹完成，model_id={patterned_id}")


if __name__ == "__main__":
    main()
