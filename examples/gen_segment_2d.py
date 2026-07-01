"""
Example: gen_segment_2d —— 2D 拆分（node_type=14）

对图生 360 输出的多视图进行组件分割，生成的分割资产可作为后续图生中模 / 低模的
segment_model_id 输入，用于基于分割结果的精细化生成。

使用 SSE 协议，过程中会推送 thinking 思考态。
"""

import os
import sys
from pathlib import Path

import logging
logging.basicConfig(level=logging.DEBUG)  # 查看详细请求/响应日志

# 或只开启 visvise 相关日志
logging.getLogger("visvise").setLevel(logging.INFO)

sys.path.insert(0, str(Path(__file__).parent.parent))

from visvise import Environment, VisviseClient, SegmentSplitType, SegmentGranularity

APP_ID     = os.environ["VISVISE_APP_ID"]
SECRET_KEY = os.environ["VISVISE_SECRET_KEY"]
RTX        = os.environ["VISVISE_RTX"]
ENV        = os.environ.get("VISVISE_ENV", "prod")
ENV_MAP    = {"prod": Environment.PROD, "test": Environment.TEST, "dev": Environment.DEV}


def main():
    client = VisviseClient(APP_ID, SECRET_KEY, env=ENV_MAP[ENV])  # noqa

    # 需要先有 gen_360 输出的 model_id
    mv_model_id = os.environ.get("MV_360_MODEL_ID")
    if not mv_model_id:
        print("[gen_segment_2d] 需要先运行 gen_360.py 并设置环境变量 MV_360_MODEL_ID")
        return

    print(f"[gen_segment_2d] 基于 360 模型 {mv_model_id} 进行 2D 拆分...")

    def on_thinking(content: str):
        print(f"  [thinking] {content}", flush=True)

    seg_model_id = client.gen_segment_2d(
        model_id_360=mv_model_id,
        split_type=SegmentSplitType.FRONT_VIEW,   # 1 正视图（默认） / 2 四视图
        granularity=SegmentGranularity.MEDIUM,    # 1 粗 / 2 中（默认） / 3 细
        prompt=None,            # 可选：自然语言描述拆分规则
        name="example_gen_segment_2d",
        on_thinking=on_thinking,
        rtx=RTX,
    )
    print(f"[gen_segment_2d] 分割完成，model_id={seg_model_id}")
    print(f"  → 可作为图生中模/低模的 segment_model_id 参数使用")


if __name__ == "__main__":
    main()
