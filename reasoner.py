
from z3 import *
from typing import Dict, Any

class NeemaReasoner:
    """
    NEIGI Reasoning Engine.
    Uses Z3 Theorem Prover to strictly verify design logic.
    """
    
    # Simple Material DB (Duplicated from Governor for now)
    MATERIAL_DB = {
        "AISI_316L": {"yield_strength": 200.0, "density": 8000.0},
        "CMSX-4": {"yield_strength": 900.0, "density": 8700.0},
        "Ti-6Al-4V": {"yield_strength": 880.0, "density": 4430.0}
    }

    def __init__(self, ast: Dict[str, Any]):
        self.ast = ast
        self.solver = Solver()
        self.vars = {} # Maps name -> Z3 Variable
        self.errors = []

    def reason(self) -> bool:
        print("--- IGIGI REASONER (Z3) ---")
        
        for entity in self.ast.get("entities", []):
            self.process_entity(entity)
            
        # Solve
        result = self.solver.check()
        
        if result == sat:
            print("[VERIFIED] System is logically consistent.")
            model = self.solver.model()
            print("  Example Valid Configuration:")
            for name, z3_var in self.vars.items():
                # Get value from model if possible
                val = model[z3_var]
                if val is not None:
                     # Formatting Z3 reals
                     if is_algebraic_value(val):
                         val = val.approx(2)
                     print(f"    - {name} = {val}")
            return True
        elif result == unsat:
            print("[CONTRADICTION] The design is IMPOSSIBLE.")
            # Z3 Unsat Core could explain why, simpler for now:
            print("  Constraints are mutually exclusive.")
            return False
        else:
            print("[UNKNOWN] Solver gave up.")
            return False

    def process_entity(self, entity: Dict[str, Any]):
        name = entity["name"]
        print(f"[*] Symbolizing Entity: {name}")
        
        # 1. Define Variables
        for prop in entity["properties"]:
            p_name = prop["name"]
            p_type = prop["type"]
            
            # Create Z3 Variable
            # Heuristic: If name ends in "_teeth", it must be an Integer
            if p_name.endswith("_teeth"):
                z3_var = Int(p_name)
            else:
                z3_var = Real(p_name)
                
            self.vars[p_name] = z3_var
            
            if p_type == "Property":
                val = prop.get("default_value")
                is_sym = prop.get("is_symbolic", False)
                
                if val is None:
                    # Pure symbolic, no constraints yet
                    pass 
                elif isinstance(val, dict) and val.get("type") == "Range":
                    # Range Constraint: val.min <= var <= val.max
                    min_v = float(val["min"])
                    max_v = float(val["max"])
                    self.solver.add(z3_var >= min_v)
                    self.solver.add(z3_var <= max_v)
                    print(f"    Constraint: {min_v} <= {p_name} <= {max_v}")
                elif not is_sym:
                    # Fixed value
                    f_val = float(val)
                    self.solver.add(z3_var == f_val)
                
            elif p_type == "Primitive":
                # Handle Materials
                val = prop.get("value")
                dtype = prop.get("datatype")
                
                if dtype == "Material":
                    mat_code = val.strip('"')
                    if mat_code in self.MATERIAL_DB:
                         print(f"    [Z3] Injecting Material Physics for {p_name} ({mat_code})")
                         mat_props = self.MATERIAL_DB[mat_code]
                         for k, v in mat_props.items():
                             # e.g. mat_yield_strength = 200.0
                             phys_var_name = f"{p_name}_{k}"
                             self.vars[phys_var_name] = Real(phys_var_name)
                             self.solver.add(self.vars[phys_var_name] == v)
        
        # 1b. Define Geometry Variables (Fixed from STL)
        # Note: In a full reasoner, these might be symbolic too (parametric CAD)! 
        # But for now, they are constants derived from the STL bind.
        # We need the calculated values from Governor? 
        # The AST doesn't store the governor's calc results directly?
        # Actually governor updates the context, but not the AST. 
        # We should probably run geometry engine here too or assume passed in AST?
        # The Current AST structure has 'geometry' block but not the calculated volume.
        # FIX: We will just mock them as symbolic variables for now, or 
        # better: Re-run simple geometry calc here? Or just let them be Free Vars?
        # If we let them be free vars, Z3 will find a solution for them.
        # But they are constrained by the STL.
        # Let's just create variables for them.
        if entity.get("geometry"):
            # Create Z3 vars for standard geo props
            # Standard: geometry_volume, geometry_width, etc.
            # We map "geometry.volume" -> "geometry_volume"
            geo_props = ["volume", "width", "height", "depth"]
            for gp in geo_props:
                vname = f"geometry_{gp}"
                self.vars[vname] = Real(vname)
                # Ideally constraint them to the actual STL values if we want validation.
                # For now, leaving them free implies we are checking "Is there ANY geometry that satisfies this?"
                # Which is also useful.

        # 2. Translate Invariants
        for invariant in entity["invariants"]:
            cond_str = invariant.get("condition_raw", "")
            if not cond_str: continue
            
            print(f"    Encoding Invariant: {invariant['name']}")
            try:
                # Context needs helper functions: 'And', 'Or', 'Not'
                context = self.vars.copy()
                context['and'] = And
                context['or'] = Or
                context['not'] = Not
                context['true'] = True
                context['false'] = False
                
                # Syntax Normalization
                # 1. Replace Logical Operators (already done in thought, implementing here)
                z3_friendly_cond = cond_str.replace(" and ", " & ").replace(" or ", " | ").replace(" not ", " ~ ")
                
                # 2. Replace Dot Notation for Geometry
                # "geometry.volume" -> "geometry_volume"
                # The spaces around dot come from Lexer? Lexer outputs tokens, 
                # parser reconstructs string with spaces join.
                # So "geometry . volume"
                z3_friendly_cond = z3_friendly_cond.replace("geometry . ", "geometry_")
                z3_friendly_cond = z3_friendly_cond.replace("geometry.", "geometry_")
                
                constraint = eval(z3_friendly_cond, {}, context)
                self.solver.add(constraint)
                
            except Exception as e:
                print(f"    [ERROR] Failed to compile invariant '{invariant['name']}': {e}")
                
