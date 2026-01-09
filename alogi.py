
import json
from typing import Dict, Any

class AlogiExporter:
    """
    ALOGI: Adaptive Language for Open Geometric Interoperability.
    Exports NEEMA AST to a standardized JSON IR.
    """
    
    @staticmethod
    def export(ast: Dict[str, Any], filepath: str):
        print(f"[*] Exporting ALOGI manifest to {filepath}...")
        
        # Transform AST to ALOGI Schema
        # 1. Clean Metadata
        meta = ast.get("meta", {}).get("attributes", {})
        
        # 2. Transform Entities
        objects = []
        for ent in ast.get("entities", []):
            obj = {
                "name": ent["name"],
                "properties": {},
                "geometry": None,
                "constraints": []
            }
            
            # Props & Primitives
            for prop in ent["properties"]:
                # Flatten structure: { "material": "AISI_316L" }
                val = prop.get("value") if prop["type"] == "Primitive" else prop.get("default_value")
                
                # Handle nested types (Ranges, Loads)
                if isinstance(val, dict):
                     # keep as object
                     pass
                
                obj["properties"][prop["name"]] = val
                
            # Geometry
            if ent.get("geometry"):
                # Clean up attrs
                geo_attrs = ent["geometry"]["attributes"]
                obj["geometry"] = {
                    "source": geo_attrs.get("source").strip('"'),
                    "format": "STL" # Default for now
                }
                
            # Constraints
            for inv in ent["invariants"]:
                obj["constraints"].append({
                    "name": inv["name"],
                    "condition": inv["condition_raw"]
                })
                
            objects.append(obj)
            
        # Final Payload
        payload = {
            "protocol": "ALOGI_v1.0",
            "meta": meta,
            "objects": objects
        }
        
        with open(filepath, 'w') as f:
            json.dump(payload, f, indent=2)
            
        print(f"    [SUCCESS] ALOGI Artifact Created.")

if __name__ == "__main__":
    pass
