import unreal
import json
import os

def export_roles_from_sets():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)
    
    output_path = os.path.join(script_dir, "data", "roles.json").replace("\\", "/")
    img_export_dir = os.path.join(root_dir, "public", "images", "roles").replace("\\", "/")

    if not os.path.exists(img_export_dir):
        os.makedirs(img_export_dir)

    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
    
    set_class_name = "PDA_Set_C"  
    set_name_variable = "Set Name"
    roles_array_variable = "Roles"       

    filter = unreal.ARFilter(
        class_names=[set_class_name], 
        recursive_classes=True
    )
    set_assets = asset_registry.get_assets(filter)
    
    json_data = []
    processed_roles = set() 
    
    print(f"Found {len(set_assets)} Sets. Starting export...")
    allowed_sets = ["Standard", "Dark", "Olympia", "Grimm"]

    for set_data in set_assets:
        set_asset = set_data.get_asset()
        current_set_name = str(set_asset.get_editor_property(set_name_variable))

        if current_set_name not in allowed_sets:
            continue

        roles_in_set = set_asset.get_editor_property(roles_array_variable)
        if not roles_in_set:
            continue 
            
        for role_asset in roles_in_set:
            if not role_asset: 
                continue 

            base_role_id = str(role_asset.get_editor_property("Name")).lower().replace(" ", "-")
            safe_set_name = current_set_name.lower().replace(" ", "-")
            unique_role_id = f"{safe_set_name}-{base_role_id}"
            
            if unique_role_id in processed_roles:
                continue
            processed_roles.add(unique_role_id)

            image_tex = role_asset.get_editor_property("Image")
            image_filename = exportImage(image_tex, img_export_dir, "default_image.png")

            portrait_tex = role_asset.get_editor_property("Portrait")
            portrait_filename = exportImage(portrait_tex, img_export_dir, "default_portrait.png")

            faction_obj = role_asset.get_editor_property("Faction")
            class_obj = role_asset.get_editor_property("Class")

            role_info = {
                "id": unique_role_id,
                "set": current_set_name, 
                "name": str(role_asset.get_editor_property("Name")),
                "faction": faction_obj.get_name() if faction_obj else "Unknown",
                "factionName": str(faction_obj.get_editor_property("Name")) if faction_obj else "Unknown",
                "class": class_obj.get_name() if class_obj else "Unknown",
                "description": str(role_asset.get_editor_property("Description")),
                "imageUrl": f"/images/roles/{image_filename}",
                "portraitUrl": f"/images/roles/{portrait_filename}"
            }
            
            json_data.append(role_info)

    json_data = sorted(json_data, key=lambda k: k['name'])

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2)
        
    print(f"SUCCESS: Exported {len(json_data)} roles and assets!")

def exportImage(texture, img_export_dir, default_filename):
    """Exports a texture asset (Image or Portrait) to img_export_dir as a PNG.

    Returns the resulting filename, falling back to default_filename when
    there is no texture to export.
    """
    if not texture:
        return default_filename

    filename = f"{texture.get_name()}.png"
    export_path = os.path.join(img_export_dir, filename)

    # Only export if file doesn't already exist to save time
    if not os.path.exists(export_path):
        task = unreal.AssetExportTask()
        task.object = texture
        task.filename = export_path
        task.automated = True
        task.replace_identical = True
        unreal.Exporter.run_asset_export_task(task)
        print(f"Exported Image: {filename}")

    return filename

export_roles_from_sets()