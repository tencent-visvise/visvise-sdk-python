"""
Example: gen_skinning —— 蒙皮生成（node_type=6）

为带骨骼的 3D 模型自动生成蒙皮权重。
SDK 内部自动构建 JSON 参数文件（含 mesh_names / joint_names）并打包成 zip 上传。
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

# 来自 skinning_model.json
MESH_NAMES = [
    "CH_M_ZB_Human_01_Body",
    "CH_M_ZB_Human_01_Hair",
    "CH_M_ZB_Human_01_Weapon",
]

JOINT_NAMES = [
    "Bip002",
    "Bip002 Pelvis",
    "Bip002 Spine",
    "Bip002 Spine1",
    "Bip002 Spine2",
    "Bip002 Neck",
    "Bip002 L Clavicle",
    "Bip002 L UpperArm",
    "Bip002 L Forearm",
    "Bip002 L Hand",
    "Bip002 L Finger0",
    "Bip002 L Finger01",
    "Bip002 L Finger02",
    "Bip002 L Finger1",
    "Bip002 L Finger11",
    "Bip002 L Finger12",
    "Bip002 L Finger2",
    "Bip002 L Finger21",
    "Bip002 L Finger22",
    "Bip002 L Finger3",
    "Bip002 L Finger31",
    "Bip002 L Finger32",
    "Bip002 L Finger4",
    "Bip002 L Finger41",
    "Bip002 L Finger42",
    "Bone001(mirrored)",
    "Bone002(mirrored)",
    "Bone003(mirrored)",
    "Bip002 R Clavicle",
    "Bip002 R UpperArm",
    "Bip002 R Forearm",
    "Bip002 R Hand",
    "Bip002 R Finger0",
    "Bip002 R Finger01",
    "Bip002 R Finger02",
    "Bip002 R Finger1",
    "Bip002 R Finger11",
    "Bip002 R Finger12",
    "Bip002 R Finger2",
    "Bip002 R Finger21",
    "Bip002 R Finger22",
    "Bip002 R Finger3",
    "Bip002 R Finger31",
    "Bip002 R Finger32",
    "Bip002 R Finger4",
    "Bip002 R Finger41",
    "Bip002 R Finger42",
    "Bone028",
    "Bone001",
    "Bone002",
    "Bone003",
    "Bip002 Head",
    "Bone031",
    "Bone031(mirrored)",
    "Bip002 L Thigh",
    "Bip002 L Calf",
    "Bip002 L Foot",
    "Bip002 L Toe0",
    "Bip002 R Thigh",
    "Bip002 R Calf",
    "Bip002 R Foot",
    "Bip002 R Toe0",
    "Bone004",
    "Bone005",
    "Bone006",
    "Bone007",
]


def main():
    client = VisviseClient(APP_ID, SECRET_KEY, env=ENV_MAP[ENV])

    print("[gen_skinning] 开始蒙皮生成...")

    model_id = client.gen_skinning(
        model_path=str(ASSETS / "skinning_model.fbx"),
        algorithm_model="VISVISE-GoSkinning-V1.0.0",
        mesh_names=MESH_NAMES,
        joint_names=JOINT_NAMES,
        name="example_gen_skinning",
    )
    print(f"[gen_skinning] 任务已创建，model_id={model_id}")

    model = client.wait_model(model_id, interval=5, timeout=600)
    print(f"[gen_skinning] 生成成功！耗时 {model.time_cost}s")
    print(f"  output_model : {model.output_model}")


if __name__ == "__main__":
    main()
