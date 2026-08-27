"""
Example: gen_text_motion —— 文本生动画（node_type=4）

通过提示词描述动作自动生成 3D 动画，返回 1 个 model_id（内部含 4 个抽卡候选，
见 framing_ai_output.text2_motion_result）。

支持两种模式（segments 非空时以多段为准）：
1. 多段提示词 segments（时间轴分段，1~15 段）
2. 单段提示词 prompt（segments 为空时回退使用）
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from visvise import Environment, VisviseClient, MotionSegment, OutputModelFormat

APP_ID     = os.environ["VISVISE_APP_ID"]
SECRET_KEY = os.environ["VISVISE_SECRET_KEY"]
RTX        = os.environ["VISVISE_RTX"]
ENV        = os.environ.get("VISVISE_ENV", "prod")
ENV_MAP    = {"prod": Environment.PROD, "test": Environment.TEST, "dev": Environment.DEV}

ASSETS = Path(__file__).parent / "assets"


def main():
    client = VisviseClient(APP_ID, SECRET_KEY, env=ENV_MAP[ENV])  # noqa

    print("[gen_text_motion] 开始文本生动画（多段 segments）...")

    # 多段提示词：时间轴分段，1~15 段；每段 num_frames / duration 二选一
    segments = [
        MotionSegment(text="从站立姿势开始，缓缓抬起右手", num_frames=60),
        MotionSegment(text="向前走两步", num_frames=90, overlap_frames_with_prev=10),
        MotionSegment(text="转身并挥手告别", num_frames=60, overlap_frames_with_prev=10),
    ]
    model_ids = client.gen_text_motion(
        model_path=str(ASSETS / "animation_model.fbx"),
        segments=segments,
        algorithm_model="MotusAI-T2M-V1.5",
        output_model_format=OutputModelFormat.FBX,
        name="example_gen_text_motion_multi",
        rtx=RTX,
    )
    print(f"[gen_text_motion] 任务已创建，返回 {len(model_ids)} 个 model_id：{model_ids}")

    print("[gen_text_motion] 等待第一个版本完成...")
    model = client.wait_model(model_ids[0], interval=5, timeout=900, rtx=RTX)
    print(f"[gen_text_motion] model_ids[0] 生成成功！耗时 {model.time_cost}s")
    print(f"  output_model : {model.output_model}")

    # 单段提示词模式：
    # model_ids = client.gen_text_motion(
    #     model_path=str(ASSETS / "animation_model.fbx"),
    #     prompt="一个人在跳街舞",
    #     algorithm_model="MotusAI-T2M-V1.5",
    #     output_model_format=OutputModelFormat.FBX,
    #     name="example_gen_text_motion",
    #     rtx=RTX,
    # )


if __name__ == "__main__":
    main()
