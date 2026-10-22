"""
Example: 2D 拆分产物 zip_path 的两种获取方式（node_type=14）

输入方式：直接上传本地六视图原画，不走图生360
    input_view              六视图（正视图必传，其余按需，缺哪个就跳过哪个）
    skip_360_preprocess     True —— 跳过图生360前置，直接用 input_view 拆分
    skip_remove_background  True —— 跳过去背景，原始图原样送拆分算法
    split_type              2（多视图拆分），支持 1~6 个视图，按实际传入的视图投递

zip_path 是算法侧产出的拆分结果压缩包（COS 路径），后端只落库不解析，里面装什么由算法定义。
后端对外返回时会自动加临时签名 ⇒ **浏览器打开 / curl / 代码 GET 都能直接下载，无需鉴权头**。

方式一（最简单）：gen_segment_2d + wait_model
    client.gen_segment_2d(...)  → model_id（本地文件由 SDK 自动上传 COS）
    client.wait_model(...)      → ModelInfo.segment_output.zip_path
    顺带还能拿到各视图的部件表 components / npz data_path / 彩色预览图 color_imgs。
    链接在「查询那一刻」现签，24h 内有效，过期重新查一次详情即可拿新链接。

方式二（生成瞬间就拿到）：底层 api.init_segment 自己消费 SSE 帧
    高层 gen_segment_2d 只把 model_id 返回、reply 帧被丢弃；
    想在同一条 SSE 连接里直接取 zip_path，就自己遍历事件帧拿 reply。
    注意底层接口只接受「已上传到平台的 COS URL」，本地文件需要先自己上传一次。

两种方式拿到的是同一个 COS 文件，区别只在「什么时候签的名」和「要不要多查一次接口」。

Usage:
    VISVISE_APP_ID=xxx VISVISE_SECRET_KEY=xxx VISVISE_RTX=xxx VISVISE_ENV=prod \
    SEG_ASSETS_DIR=examples/assets python examples/gen_segment_2d_zip.py
"""

import os
import sys
import urllib.request
from pathlib import Path

import logging

logging.basicConfig(level=logging.INFO)

sys.path.insert(0, str(Path(__file__).parent.parent))

from visvise import Environment, NodeType, SegmentSplitType, View, VisviseClient

APP_ID     = os.environ["VISVISE_APP_ID"]
SECRET_KEY = os.environ["VISVISE_SECRET_KEY"]
RTX        = os.environ["VISVISE_RTX"]
ENV        = os.environ.get("VISVISE_ENV", "prod")
ENV_MAP    = {"prod": Environment.PROD, "test": Environment.TEST, "dev": Environment.DEV}

# 六视图素材目录（默认 examples/assets，可用 SEG_ASSETS_DIR 覆盖）
ASSETS_DIR = Path(os.environ.get("SEG_ASSETS_DIR", Path(__file__).parent / "assets"))

# zip 下载到哪个目录
OUT_DIR = Path(os.environ.get("SEG_OUT_DIR", Path(__file__).parent))

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
        raise SystemExit("[gen_segment_2d_zip] 正视图 main_view.png 必传")
    return View(**kwargs)


def download(url: str, save_as: Path) -> None:
    """zip_path 是带 COS 签名的 URL，直接 GET 即可，无需任何鉴权头。"""
    if not url:
        print("  [warn] zip_path 为空（该资产没有算法产物，或后端未落库），跳过下载")
        return
    urllib.request.urlretrieve(url, save_as)  # 链接 24h 内有效
    print(f"  [download] {save_as}（{save_as.stat().st_size} bytes）")


def way1_high_level(client: VisviseClient, input_view: View) -> None:
    """方式一：高层方法 + 资产详情（wait_model），最省事的一种。"""
    print("[方式一] gen_segment_2d → wait_model → segment_output.zip_path")

    seg_model_id = client.gen_segment_2d(
        input_view=input_view,                      # 本地文件由 SDK 自动上传 COS
        split_type=SegmentSplitType.FOUR_VIEW,      # 2 多视图拆分（按实际传入的视图，1~6 个）
        skip_360_preprocess=True,                   # 跳过图生360前置，直接用 input_view 拆分
        skip_remove_background=True,                # 跳过去背景，原始图直接送算法
        name="example_gen_segment_2d_zip_way1",
        rtx=RTX,
    )
    print(f"  model_id={seg_model_id}")

    # wait_model 轮询到 status=3 才返回，此时 zip_path 一定已落库
    info = client.wait_model(seg_model_id, timeout=600, rtx=RTX)

    so = info.segment_output
    if so is None:
        print("  [warn] segment_output 为空：只有 2D 拆分（node_type=14）资产才有拆分产物")
        return

    print(f"  zip_path = {so.zip_path}")

    # 顺带看下拆分结果里的其它内容（这才是 SDK 能拿到的最全信息）
    for name in ("main_view", "back_view", "left_view", "right_view", "top_view", "bottom_view"):
        v = getattr(so, name, None)
        if v is None:
            continue  # 该视图没参与拆分
        print(f"  {name}: shape={v.shape} npz={v.data_path} mask PNG={v.mask_image_path}")
        for comp in v.components or []:
            print(f"    部件 label={comp.label} name={comp.name} color={comp.color}"
                  "  ← label 可作为 component_label 送图生中模")
    if so.color_imgs and so.color_imgs.main_view:
        print(f"  正视图彩色预览图={so.color_imgs.main_view}")

    download(so.zip_path, OUT_DIR / "segment_output_way1.zip")


def way2_sse_reply(client: VisviseClient, input_view: View) -> None:
    """方式二：自己消费 SSE 流，在 reply 帧里直接拿 zip_path（不用再查一次）。"""
    print("[方式二] api.init_segment 自己遍历 SSE 帧 → reply 帧里的 zip_path")

    # 底层接口只接受已上传到平台的 COS URL，本地文件先上传一次
    # （这里复用 SDK 内部的上传方法；正式代码直接用方式一，高层方法会自动上传）
    uploaded = {}
    for field, _ in VIEW_FILES:
        src = getattr(input_view, field, None)
        if src:
            uploaded[field] = client._resolve_file(src, rtx=RTX)
    cos_view = View(**uploaded)

    # 底层接口需要显式传算法模型名，高层 gen_segment_2d 会自动选，这里手动取一个
    models = client.api.list_algorithm_model(NodeType.SEGMENT_2D, rtx=RTX)
    if not models:
        print("  [warn] 当前账号没有可用的 2D 拆分算法模型")
        return
    algorithm_model = models[0]
    print(f"  algorithm_model={algorithm_model}")

    seg_model_id, zip_path, client_id = "", "", ""
    for frame in client.api.init_segment(
        name="example_gen_segment_2d_zip_way2",
        algorithm_model=algorithm_model,
        input_view=cos_view,                    # 传 input_view 时不再走图生360
        split_type=SegmentSplitType.FOUR_VIEW,
        skip_360_preprocess=True,
        skip_remove_background=True,
        rtx=RTX,
    ):
        event = frame.get("event")
        data = frame.get("data") or {}
        if event == "pre_create":
            seg_model_id = data.get("model_id", "")
            print(f"  [pre_create] model_id={seg_model_id}")
        elif event == "thinking":
            print(f"  [thinking] {data}")
        elif event == "reply":
            zip_path = data.get("zip_path", "")
            client_id = data.get("client_id", "")
            print(f"  [reply] zip_path={zip_path}")
            break
        elif event == "error":
            print(f"  [error] {data.get('msg', data)}")
            return

    print(f"  client_id={client_id}（可传给 open_segment 做二次编辑）")
    download(zip_path, OUT_DIR / "segment_output_way2.zip")


def main():
    client = VisviseClient(APP_ID, SECRET_KEY, env=ENV_MAP[ENV])  # noqa

    input_view = build_input_view()

    way1_high_level(client, input_view)
    print()
    way2_sse_reply(client, input_view)
    print("\n[提示] zip_path 是带签名的 URL，24h 内直接 GET 即可下载；"
          "过期后重新调用 wait_model / get_model_list 就能拿到新链接。")


if __name__ == "__main__":
    main()
