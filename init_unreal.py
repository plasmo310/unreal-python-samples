import os

import unreal


#追加されたエントリーから呼ばれる関数
def export_data_table():

    EXPORT_DIR = r"C:/Tmp"
    TARGET_FOLDER = "/Game/ForestSample/Data"

    # 指定フォルダのアセットを取得
    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
    asset_data_list = asset_registry.get_assets_by_path(TARGET_FOLDER, recursive=True)

    # DataTableのみを処理
    for asset_data in asset_data_list:
        asset_class = asset_data.get_class()
        if asset_class.get_name() == "DataTable":
            # アセットをロード
            asset_package_name = str(asset_data.package_name)
            asset_project_name = os.path.dirname(asset_package_name).split('/')[-1]
            datatable = unreal.EditorAssetLibrary.load_asset(asset_data.package_name)
            
            # 出力ファイルパス
            file_name = f"{datatable.get_name()}.csv"
            file_dir = os.path.join(EXPORT_DIR, asset_project_name)
            if not os.path.exists(file_dir):
                os.makedirs(file_dir)
            file_path = os.path.join(file_dir,  file_name)

            # CSV文字列取得
            csv_string = unreal.DataTableFunctionLibrary.export_data_table_to_csv_string(datatable)

            # ファイル書き出し
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(csv_string)
            unreal.log(f"Export => {file_path}")

    unreal.log("All DataTables exported!")


def main():
    ToolMenus = unreal.ToolMenus.get()
    ToolMenu = ToolMenus.find_menu("LevelEditor.MainMenu.Tools")
    ToolMenu.add_section(section_name="procedural",label="Procedural",insert_type=unreal.ToolMenuInsertType.DEFAULT,)

    entry = unreal.ToolMenuEntry(name="export_data_table", type=unreal.MultiBlockType.MENU_ENTRY)
    entry.set_label("Export Data Table")
    entry.set_string_command(unreal.ToolMenuStringCommandType.PYTHON, "", "export_data_table()")
    ToolMenu.add_menu_entry("procedural", entry)

main()
