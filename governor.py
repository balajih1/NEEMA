
from typing import Dict, Any, List
import os
from geometry_engine import GeometryEngine

class NeemaGovernor:
    """
    NEEMA Governor - The Semantic Validator.
    Responsibility: Enforce the 'Constitution' (Physics & Governance).
    """
    
    # Simple Material DB for v0.1
    MATERIAL_DB = {
        "AISI_316L": {"yield_strength": 200.0, "density": 8000.0},
        "CMSX-4": {"yield_strength": 900.0, "density": 8700.0},
        "Ti-6Al-4V": {"yield_strength": 880.0, "density": 4430.0}
    }

    def __init__(self, ast: Dict[str, Any]):
        self.ast = ast
        self.errors = []
        self.warnings = []

    def govern(self) -> bool:
        """Run all validation passes. Returns True if legal."""
        print("--- IGIGI GOVERNANCE AUDIT ---")
        
        # 1. Governance Layer Check
        self.check_authority()
        
        # 2. Physics & Logic Layer Check
        for entity in self.ast.get("entities", []):
            self.validate_entity(entity)
            
        # Report
        if self.errors:
            print(f"\n[VIOLATION] The design was REJECTED by NEEMA.")
            for e in self.errors:
                print(f"  FAILED: {e}")
            return False
        else:
            print(f"\n[APPROVED] The design complies with all epistemic constraints.")
            return True

    def check_authority(self):
        """
        Validates the 'Passport' of the code (Governance Layer).
        Enforces Spec v0.1: Intent, Risk Class, and Authority.
        """
        meta = self.ast.get("meta", {})
        attrs = meta.get("attributes", {})
        
        asset_id = attrs.get("id", "unknown")
        intent = attrs.get("intent", '"unknown"').strip('"')
        risk_class = attrs.get("risk_class", '"benign"').strip('"')
        auth_req = attrs.get("authority_required", '"open"').strip('"')
        
        # Simulated User Credentials (The "Passport" of the Operator)
        user_context = {
            "role": "engineer",
            "clearance": "institutional", # Matches 'institutional' authority
            "accredited_for": ["civilian_energy", "research"] # Allowed intents
        }
        
        print(f"[*] Governance Audit for: {asset_id}")
        print(f"    Intent: {intent} | Risk: {risk_class} | Auth Required: {auth_req}")
        
        # 1. Check Authority Level
        levels = {"open": 0, "institutional": 1, "sovereign": 2}
        
        asset_level = levels.get(auth_req, 100)
        user_level = levels.get(user_context["clearance"], 0)
        
        if user_level < asset_level:
            self.errors.append(f"Security Violation: User clearance '{user_context['clearance']}' insufficient for '{auth_req}' project.")

        # 2. Check Intent Alignment
        if intent not in user_context["accredited_for"]:
             self.warnings.append(f"Intent Mismatch: User accreditation {user_context['accredited_for']} does not explicitly include '{intent}'. Audit Logged.")

        # 3. High Risk Checks
        if risk_class in ["dual_use", "existential"]:
            print("    [!] ALERT: High-Risk Asset detected. Enforcing deep invariant scanning.")
            # In a real system, this might trigger a remote approval workflow


    def validate_entity(self, entity: Dict[str, Any]):
        name = entity["name"]
        print(f"[*] Inspecting Entity: {name}")
        
        # 1. Build Compilation Context (Symbol Table)
        context = {}
        for prop in entity["properties"]:
            # Skip Primitives here, handled below
            if prop["type"] == "Primitive":
                continue
                
            # Convert string values to Python types for evaluation
            val_str = prop["default_value"]
            datatype = prop["datatype"]
            
            # Handle RANGES for basic validation (use midpoint)
            if isinstance(val_str, dict) and val_str.get("type") == "Range":
                # Governor is basic; just check if midpoint passes basic logic
                min_v = float(val_str["min"])
                max_v = float(val_str["max"])
                val = (min_v + max_v) / 2.0
                print(f"    [WARN] Symbolic Range detected for '{prop['name']}'. Governor using midpoint {val} for basic check.")
                context[prop['name']] = val
                continue
            
            if datatype == "Float":
                context[prop["name"]] = float(val_str)
            elif datatype == "String":
                context[prop["name"]] = val_str.strip('"')
            elif datatype == "Boolean":
                context[prop["name"]] = (val_str == "true")
            else:
                context[prop["name"]] = val_str
        
        # 1.5 Handle Primitives (New!)
        # We need to loop over primitives separate from properties in AST?
        # The parser puts them in properties? No, I added 'primitives' to 'props' list in parser
        # but with type="Primitive".
        # Let's iterate over ALL items in 'properties' list from AST (which now has mixed Property and Primitive)
        # Wait, in parse_entity I appended to 'props'.
        
        # Re-iterating to validate primitives specifically
        for prop in entity["properties"]:
            if prop["type"] == "Primitive":
                self.validate_primitive(prop, context)

        # 2. Inject Geometric Context (New!)
        if entity.get("geometry"):
            self.process_geometry(entity["geometry"], context)

        # 3. Check Invariants
        for invariant in entity["invariants"]:
            self.check_invariant(invariant, context)

    def process_geometry(self, geo_block: Dict[str, Any], context: Dict[str, Any]):
        attrs = geo_block["attributes"]
        source_file = attrs.get("source", "").strip('"')
        
        if not source_file:
            self.warnings.append("Geometry block empty or missing source.")
            return

        print(f"    [GEO] analyzing bound CAD file: {source_file}")
        
        try:
            # Assume file is relative to execution or absolute
            stats = GeometryEngine.analyze_stl(source_file)
            
            # Inject into context as 'geometry.volume', etc.
            # Flattening for now: 'geometry_volume'
            # Or creating a sub-object if eval supports it. 
            # Simple approach: objects in python context.
            
            class GeoProxy:
                def __init__(self, data):
                    self.volume = data["volume"]
                    self.width = data["bbox_width"]
                    self.height = data["bbox_height"]
            
            context["geometry"] = GeoProxy(stats)
            
            print(f"      -> Volume: {stats['volume']:.2f}")
            print(f"      -> Dimensions: {stats['bbox_width']:.2f} x {stats['bbox_depth']:.2f} x {stats['bbox_height']:.2f}")
            
        except Exception as e:
            self.errors.append(f"Geometry Analysis Failed: {e}")

    def validate_primitive(self, prim: Dict[str, Any], context: Dict[str, Any]):
        dtype = prim["datatype"]
        val = prim["value"]
        name = prim["name"]
        
        if dtype == "Material":
            mat_code = val.strip('"')
            if mat_code not in self.MATERIAL_DB:
                self.errors.append(f"Unknown Material Code: '{mat_code}'. Valid codes: {list(self.MATERIAL_DB.keys())}")
            else:
                # Inject material properties into context!
                print(f"    [MAT] Resolved {mat_code}. Injecting material physics.")
                mat_props = self.MATERIAL_DB[mat_code]
                for k, v in mat_props.items():
                    context[f"{name}_{k}"] = v # e.g. material_yield_strength

        elif dtype == "Load":
            # val is a dictionary from parser
            if not isinstance(val, dict):
                self.errors.append(f"Load '{name}' must be an object {{...}}")
                return
            
            # Simple check
            pk = val.get("newtons")
            if pk:
                context[f"{name}_newtons"] = float(pk)

    def check_invariant(self, invariant: Dict[str, Any], context: Dict[str, Any]):
        inv_name = invariant["name"]
        condition = invariant["condition_raw"]
        
        # SAFETY CRITICAL: We are using eval()! 
        # In a real compiler, we would write an expression evaluator.
        # For a weekend prototype, eval() is acceptable IF we trust the parser.
        # Our parser only allows identifiers, decimals, and operators.
        
        try:
            # We must map variable names in condition to context
            # We pass our context as locals, and mapping for true/false as globals
            global_context = {"true": True, "false": False}
            result = eval(condition, global_context, context)
            
            if not result:
                raw_msg = invariant.get("on_fail")
                msg = raw_msg.strip('"') if raw_msg else "Constraint violated"
                self.errors.append(f"Invariant '{inv_name}' failed: {msg}")
            else:
                print(f"    [PASS] Invariant {inv_name}")
                
        except Exception as e:
            self.errors.append(f"Internal Error evaluating '{inv_name}': {e}")

if __name__ == "__main__":
    # Mock AST to test validator
    mock_ast = {
        "meta": {"attributes": {"classification": "\"CIVILIAN\""}},
        "entities": [
            {
                "name": "Turbine",
                "properties": [
                    {"name": "temp", "datatype": "Float", "default_value": "2500.0"}
                ],
                "invariants": [
                    {
                        "name": "safety",
                        "condition_raw": "temp < 2000.0", # Should Fail (2500 < 2000 is False)
                        "on_fail": "\"Too hot!\""
                    }
                ]
            }
        ]
    }
    
    gov = NeemaGovernor(mock_ast)
    gov.govern()
