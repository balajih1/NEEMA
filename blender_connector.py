
import bpy
import json
import os
import sys

# Usage: blender --background --python neema_blender_connector.py -- <path_to_alogi.json>

def import_alogi(json_path):
    print(f"[*] IGIGI Blender Connector: Reading {json_path}")
    
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    # Clear existing scene
    bpy.ops.wm.read_factory_settings(use_empty=True)
    
    # Process Entities
    for obj_def in data.get("objects", []):
        name = obj_def["name"]
        print(f"  -> Building Entity: {name}")
        
        # 1. Import Geometry
        geo = obj_def.get("geometry")
        if geo:
            source = geo["source"]
            # Resolve relative path
            # Assuming source is relative to json file
            base_dir = os.path.dirname(json_path)
            stl_path = os.path.join(base_dir, source)
            
            if os.path.exists(stl_path):
                bpy.ops.import_mesh.stl(filepath=stl_path)
                # Rename the imported object (usually active)
                imported_obj = bpy.context.selected_objects[0]
                imported_obj.name = name
            else:
                print(f"    [ERR] STL not found: {stl_path}")
                # Create Placeholder
                bpy.ops.mesh.primitive_cube_add()
                imported_obj = bpy.context.active_object
                imported_obj.name = f"{name}_PLACEHOLDER"
        else:
             # Create Logic/Empty Object
             bpy.ops.object.empty_add(type='PLAIN_AXES')
             imported_obj = bpy.context.active_object
             imported_obj.name = name

        # 2. Attach ALOGI Metadata
        # We store NEEMA constraints/properties as Custom Properties in Blender
        imported_obj["neema_type"] = "Entity"
        
        for k, v in obj_def.get("properties", {}).items():
            # Blender custom props handle basic types well
            imported_obj[f"neema_{k}"] = v
            
        print(f"    [SUCCESS] Created {name} with metadata.")

    # Save .blend file for inspection
    output_blend = json_path.replace(".alogi.json", ".blend")
    bpy.ops.wm.save_as_mainfile(filepath=output_blend)
    print(f"[*] Saved Blender Project: {output_blend}")

if __name__ == "__main__":
    # Handle arguments passed after '--'
    # Blender args are weird. 
    argv = sys.argv
    if "--" in argv:
        args = argv[argv.index("--") + 1:]
        if args:
            import_alogi(args[0])
        else:
            print("No JSON file provided.")
    else:
        print("Usage: blender --python connector.py -- <file.alogi.json>")
