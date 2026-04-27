"""
Example: gen_text_motion —— 文本生动画（node_type=4）

通过提示词描述动作自动生成 3D 动画，一次返回 4 个版本供抽卡选择。
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from visvise import Environment, VisviseClient

APP_ID     = os.environ["VISVISE_APP_ID"]
SECRET_KEY = os.environ["VISVISE_SECRET_KEY"]
ENV        = os.environ.get("VISVISE_ENV", "prod")
ENV_MAP    = {"prod": Environment.PROD, "test": Environment.TEST, "dev": Environment.DEV}

ASSETS = Path(__file__).parent / "assets"


def main():
    client = VisviseClient(APP_ID, SECRET_KEY, env=ENV_MAP[ENV])  # noqa

    print("[gen_text_motion] 开始文本生动画...")

    # 一次生成 4 个版本供抽卡
    model_ids = client.gen_text_motion(
        model_path=str(ASSETS / "animation_model.fbx"),
        prompt="一个人在跳街舞",
        algorithm_model="VISVISE-TextMotion-V1.1.0",
        output_model_format="fbx",
        name="example_gen_text_motion",
    )
    print(f"[gen_text_motion] 任务已创建，共 {len(model_ids)} 个版本：{model_ids}")

    print("[gen_text_motion] 等待第一个版本完成（可按需等待全部）...")
    model = client.wait_model(model_ids[0], interval=5, timeout=900)
    print(f"[gen_text_motion] model_ids[0] 生成成功！耗时 {model.time_cost}s")
    print(f"  output_model : {model.output_model}")


if __name__ == "__main__":
    main()
