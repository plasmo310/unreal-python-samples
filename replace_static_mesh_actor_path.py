####################
# 開いているレベル上のアクタのStaticMeshパスを差し替える (UE4.27)
####################
import unreal


def replace_static_mesh_actor_paths(replace_from_dir, replace_to_dir):
    # 現在開いているレベル上の全アクターを取得
    all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

    for actor in all_actors:
        # StaticMeshActorのみが対象
        if not isinstance(actor, unreal.StaticMeshActor):
            continue

        # StaticMeshを取得
        static_mesh_component = actor.static_mesh_component
        static_mesh = (
            static_mesh_component.static_mesh if static_mesh_component else None
        )
        if not static_mesh:
            continue

        # プレフィックスを replace_from_dir から replace_to_dir に置換
        path = static_mesh.get_path_name()
        if path.startswith(replace_from_dir):
            new_path = replace_to_dir + path[len(replace_from_dir) :]
            # 置き換え先のアセットをロード
            # ".オブジェクト名" のサフィックスを除去してアセットパスにする
            new_asset_path = new_path.split(".")[0]
            new_mesh = unreal.EditorAssetLibrary.load_asset(new_asset_path)

            # StaticMeshComponent にメッシュをセット
            if new_mesh and isinstance(new_mesh, unreal.StaticMesh):
                static_mesh_component.set_static_mesh(new_mesh)
                unreal.log(f"置き換え完了: {path} -> {new_asset_path}")
            else:
                unreal.log_error(f"置き換え失敗: StaticMesh対象外 => {new_asset_path}")


# TODO: Please Input Target Dirs.
REPLACE_FROM_DIR = "/Game/Replace_From"
REPLACE_TO_DIR = "/Game/Replace_To"
replace_static_mesh_actor_paths(REPLACE_FROM_DIR, REPLACE_TO_DIR)
