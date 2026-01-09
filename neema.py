
import sys
import os
from lexer import NeemaLexer
from parser import NeemaParser
from governor import NeemaGovernor
from reasoner import NeemaReasoner
from alogi import AlogiExporter

def compile_file(filepath):
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found.")
        return None

    print(f"Compiling {filepath}...")
    
    with open(filepath, 'r') as f:
        source_code = f.read()

    # 1. Lexing
    try:
        lexer = NeemaLexer(source_code)
        tokens = lexer.tokenize()
    except Exception as e:
        print(f"[LEXER ERROR] {e}")
        return

    # 2. Parsing
    try:
        parser = NeemaParser(tokens)
        ast = parser.parse()
    except Exception as e:
        print(f"[PARSER ERROR] {e}")
        return

    # 3. Governance / Validation
    governor = NeemaGovernor(ast)
    is_valid = governor.govern()
    
    if is_valid:
        print("\nSUCCESS: Knowledge Element successfully compiled and authorized.")
    else:
        print("\n[WARNING] Basic validation failed. Proceeding to Advanced Reasoning for diagnostics...")
        
    # Phase 2: Run Reasoner always
    print("\n" + "="*30)
    reasoner = NeemaReasoner(ast)
    is_consistent = reasoner.reason()
    
    if not is_valid and not is_consistent:
        sys.exit(1)
        
    return ast

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python neema.py <file.neema> [--export]")
    else:
        target_file = sys.argv[1]
        do_export = "--export" in sys.argv
        
        ast = compile_file(target_file) 
        
        if do_export and ast:
            # Generate export filename: file.neema -> file.alogi.json
            base = os.path.splitext(target_file)[0]
            export_path = f"{base}.alogi.json"
            AlogiExporter.export(ast, export_path)
