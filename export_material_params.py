####################
# 指定アセットパス配下のStaticMeshのマテリアルパラメータをJSON形式で出力 (UE4.27)
#
# 出力JSON構造:
# [
#   {
#     "mesh_path": "/Game/Assets/SM_Foo",
#     "materials": [
#       {
#         "slot_name": "Material_Slot_0",
#         "params": {
#           "material_path": "/Game/Materials/M_Foo",
#           "parameters": {
#             "Roughness":     { "type": "scalar",  "value": 0.5 },
#             "BaseColor":     { "type": "vector",  "value": {"r":1,"g":1,"b":1,"a":1} },
#             "BaseColorMap":  { "type": "texture", "value": "/Game/Textures/T_Foo_D" }
#           }
#         }
#       }
#     ]
#   }
# ]
####################
import json

import unreal


def _collect_params_from_base_material(material):
    """
    MaterialEditingLibrary を使ってベース Material のパラメータを
    {"name": {"type": ..., "value": ...}} の順序付き dict で返す。
    """
    mel = unreal.MaterialEditingLibrary
    parameters = {}

    for name in mel.get_scalar_parameter_names(material):
        name_str = str(name)
        result = mel.get_material_default_scalar_parameter_value(material, name_str)
        # 戻り値は (success: bool, value: float) のタプル
        parameters[name_str] = {
            "type": "scalar",
            "value": result[1] if isinstance(result, (tuple, list)) else result,
        }

    for name in mel.get_vector_parameter_names(material):
        name_str = str(name)
        result = mel.get_material_default_vector_parameter_value(material, name_str)
        color = result[1] if isinstance(result, (tuple, list)) else result
        if color is not None:
            parameters[name_str] = {
                "type": "vector",
                "value": {"r": color.r, "g": color.g, "b": color.b, "a": color.a},
            }

    for name in mel.get_texture_parameter_names(material):
        name_str = str(name)
        result = mel.get_material_default_texture_parameter_value(material, name_str)
        tex = result[1] if isinstance(result, (tuple, list)) else result
        parameters[name_str] = {
            "type": "texture",
            "value": tex.get_path_name().split(".")[0] if tex else None,
        }

    return parameters


def _apply_mi_overrides(mat_instance, parameters):
    """MaterialInstance のオーバーライド値を parameters dict に上書きする。
    既存キーは value のみ更新（挿入順を保持）、新規キーは末尾に追加する。
    """
    for sv in mat_instance.get_editor_property("scalar_parameter_values"):
        name = str(sv.get_editor_property("parameter_info").get_editor_property("name"))
        value = sv.get_editor_property("parameter_value")
        if name in parameters:
            parameters[name]["value"] = value
        else:
            parameters[name] = {"type": "scalar", "value": value}

    for vv in mat_instance.get_editor_property("vector_parameter_values"):
        name = str(vv.get_editor_property("parameter_info").get_editor_property("name"))
        color = vv.get_editor_property("parameter_value")
        value = {"r": color.r, "g": color.g, "b": color.b, "a": color.a}
        if name in parameters:
            parameters[name]["value"] = value
        else:
            parameters[name] = {"type": "vector", "value": value}

    for tv in mat_instance.get_editor_property("texture_parameter_values"):
        name = str(tv.get_editor_property("parameter_info").get_editor_property("name"))
        tex = tv.get_editor_property("parameter_value")
        value = tex.get_path_name().split(".")[0] if tex else None
        if name in parameters:
            parameters[name]["value"] = value
        else:
            parameters[name] = {"type": "texture", "value": value}


def collect_material_params(mat_interface):
    """
    MaterialInterface のパラメータ情報を dict で返す
    """
    if mat_interface is None:
        return None

    mat_path = mat_interface.get_path_name().split(".")[0]
    parameters = {}

    # 親マテリアルを辿る
    chain = []
    current = mat_interface
    while current is not None:
        chain.append(current)
        if isinstance(current, unreal.MaterialInstance):
            current = current.get_editor_property("parent")
        else:
            break

    # 親マテリアルを起点にパラメータをチェックする
    for item in reversed(chain):
        if isinstance(item, unreal.Material):
            parameters.update(_collect_params_from_base_material(item))
        elif isinstance(item, unreal.MaterialInstance):
            _apply_mi_overrides(item, parameters)

    return {
        "material_path": mat_path,
        "parameters": parameters,
    }


def export_static_mesh_material_params(asset_path, output_json_path):
    """
    指定アセットパス配下の全 StaticMesh を走査し、
    マテリアルパラメータを JSON ファイルへ出力する。

    Args:
        asset_path (str):       対象アセットパス (例: "/Game/Character")
        output_json_path (str): 出力先 JSON ファイルパス (例: "C:/output/params.json")
    """
    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
    asset_registry.scan_paths_synchronous([asset_path], force_rescan=False)

    ar_filter = unreal.ARFilter(
        class_names=["StaticMesh"],
        package_paths=[asset_path],
        recursive_paths=True,
    )
    asset_data_list = asset_registry.get_assets(ar_filter)

    result = []
    for asset_data in asset_data_list:
        mesh_package_path = str(asset_data.package_name)
        unreal.log(f"処理中: {mesh_package_path}")

        static_mesh = unreal.EditorAssetLibrary.load_asset(mesh_package_path)
        if not isinstance(static_mesh, unreal.StaticMesh):
            unreal.log_warning(
                f"  StaticMesh としてロードできませんでした: {mesh_package_path}"
            )
            continue

        mesh_entry = {
            "mesh_path": mesh_package_path,
            "materials": [],
        }

        static_materials = static_mesh.get_editor_property("static_materials")
        for mat_slot in static_materials:
            mat_interface = mat_slot.get_editor_property("material_interface")
            slot_name = str(mat_slot.get_editor_property("material_slot_name"))

            try:
                params = collect_material_params(mat_interface)
            except Exception as exc:
                unreal.log_warning(f"  パラメータ取得失敗 [{slot_name}]: {exc}")
                params = None

            mesh_entry["materials"].append(
                {
                    "slot_name": slot_name,
                    "params": params,
                }
            )

        result.append(mesh_entry)

    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    unreal.log(f"出力完了: {len(result)} 件 -> {output_json_path}")


# TODO: 以下の2変数を環境に合わせて変更してください
TARGET_ASSET_PATH = "/Game/StarterContent"
OUTPUT_JSON_PATH = "C:/material_params.json"
export_static_mesh_material_params(TARGET_ASSET_PATH, OUTPUT_JSON_PATH)
