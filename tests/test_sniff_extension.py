"""使用 tests/assets 下的真实文件验证 _sniff_extension / _gen_random_filename_for 是否工作正确。"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from visvise.client import _sniff_extension, _gen_random_filename_for

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

# 期望（文件名 → 期望扩展名）
EXPECT = {
    "main_view.png": ".png",
    "back_view.png": ".png",
    "left_view.png": ".png",
    "right_view.png": ".png",
    "pose_ref.png": ".png",
    "tex_ref_front.jpg": ".jpg",
    "tex_ref_back.jpg": ".jpg",
    "tex_ref_left.jpg": ".jpg",
    "high_model.fbx": ".fbx",
    "animation_model.fbx": ".fbx",
    "rigging_model.fbx": ".fbx",
    "skinning_model.fbx": ".fbx",
    "tex_model.obj": ".obj",
    "animation_video.mp4": ".mp4",
}


def main() -> int:
    failures: list[str] = []
    for fname, expect in EXPECT.items():
        path = os.path.join(ASSETS_DIR, fname)
        if not os.path.isfile(path):
            failures.append(f"{fname}: 文件不存在")
            continue
        # 仅读取前 2KB 即可识别（节省内存）
        with open(path, "rb") as f:
            head = f.read(2048)
        got = _sniff_extension(head, default=".bin")
        gen_name = _gen_random_filename_for(head, default_ext=".bin")
        status = "✓" if got == expect else "✗"
        size_kb = os.path.getsize(path) / 1024
        print(f"  {status} {fname:30s} ({size_kb:>9.1f} KB)  →  {got}   uuid名: {gen_name}")
        if got != expect:
            failures.append(f"{fname}: got={got}, want={expect}")

    print()
    if failures:
        print(f"❌ {len(failures)} 个用例失败:")
        for f in failures:
            print(f"   - {f}")
        return 1
    print(f"✅ 全部 {len(EXPECT)} 个真实资产嗅探正确")
    return 0


if __name__ == "__main__":
    sys.exit(main())
