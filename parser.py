
from typing import List, Dict, Any
from lexer import Token, NeemaLexer

class NeemaParser:
    """
    NEEMA Parser - Converts Tokens into an Abstract Syntax Tree (AST).
    Architecture: Recursive Descent Parser.
    """
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> Dict[str, Any]:
        """Root entry point: expecting a program with meta + entities."""
        ast = {
            "type": "Program",
            "meta": None,
            "entities": []
        }
        
        while self.pos < len(self.tokens):
            if self.match("KEYWORD", "meta"):
                ast["meta"] = self.parse_meta()
            elif self.match("KEYWORD", "entity"):
                ast["entities"].append(self.parse_entity())
            else:
                raise SyntaxError(f"Unexpected token {self.current()}")
        
        return ast

    # --- Grammar Rules ---

    def parse_meta(self) -> Dict[str, Any]:
        """Parses: meta { key: value ... }"""
        self.consume("KEYWORD", "meta")
        self.consume("LBRACE")
        
        entries = {}
        while not self.check("RBRACE"):
            # key: value
            key_token = self.consume("ID")
            self.consume("COLON")
            # For simplicity, values in meta are strings or numbers
            val_token = self.advance()
            entries[key_token.value] = val_token.value
        
        self.consume("RBRACE")
        return {"type": "MetaBlock", "attributes": entries}

    def parse_entity(self) -> Dict[str, Any]:
        """Parses: entity Name { property... invariant... }"""
        self.consume("KEYWORD", "entity")
        name_token = self.consume("ID")
        self.consume("LBRACE")
        
        props = []
        invariants = []
        geo_block = None
        
        while not self.check("RBRACE"):
            if self.match("KEYWORD", "property"):
                props.append(self.parse_property())
            elif self.match("KEYWORD", "primitive"):
                props.append(self.parse_primitive())
            elif self.match("KEYWORD", "invariant"):
                invariants.append(self.parse_invariant())
            elif self.match("KEYWORD", "geometry"):
                geo_block = self.parse_geometry()
            else:
                raise SyntaxError(f"Expected property, invariant, or geometry inside entity, got {self.current()}")
        
        self.consume("RBRACE")
        return {
            "type": "Entity",
            "name": name_token.value,
            "properties": props,
            "geometry": geo_block,
            "invariants": invariants
        }

    def parse_property(self) -> Dict[str, Any]:
        """Parses: property name : Type [= value [.. max_value]]"""
        self.consume("KEYWORD", "property")
        name = self.consume("ID").value
        self.consume("COLON")
        dtype = self.consume("KEYWORD").value # Float, String, etc.
        
        val = None
        is_symbolic = True
        
        if self.match("ASSIGN"):
            self.consume("ASSIGN")
            is_symbolic = False
            
            # Get first value
            val = self.advance().value
            
            # Check for Range (.. max)
            if self.match("DOT_DOT"):
                self.consume("DOT_DOT")
                max_val = self.advance().value
                val = {"type": "Range", "min": val, "max": max_val}
        
        return {
            "type": "Property",
            "name": name,
            "datatype": dtype,
            "default_value": val,
            "is_symbolic": is_symbolic
        }

    def parse_primitive(self) -> Dict[str, Any]:
        """Parses: primitive name : Type = val OR { ... }"""
        self.consume("KEYWORD", "primitive")
        name = self.consume("ID").value
        self.consume("COLON")
        dtype = self.consume("KEYWORD").value # Material, Load, etc.
        self.consume("ASSIGN")
        
        # Value can be a literal OR an object block { ... }
        if self.check("LBRACE"):
            val = self.parse_object_literal()
        else:
            val = self.advance().value # Literal value
        
        return {
            "type": "Primitive",
            "name": name,
            "datatype": dtype,
            "value": val
        }

    def parse_object_literal(self) -> Dict[str, Any]:
        """Parses: { key: val, ... }"""
        self.consume("LBRACE")
        obj = {}
        while not self.check("RBRACE"):
            key = self.consume("ID").value
            self.consume("COLON")
            val = self.advance().value
            obj[key] = val
            if self.match("COMMA"):
                self.consume("COMMA")
        self.consume("RBRACE")
        return obj

    def parse_geometry(self) -> Dict[str, Any]:
        """
        Parses: geometry { source: "file.stl" ... }
        """
        self.consume("KEYWORD", "geometry")
        self.consume("LBRACE")
        
        attrs = {}
        while not self.check("RBRACE"):
            # key: value
            key = self.consume("ID").value
            self.consume("COLON")
            val = self.advance().value # literal
            attrs[key] = val
            
        self.consume("RBRACE")
        return {
            "type": "GeometryBlock",
            "attributes": attrs
        }

    def parse_invariant(self) -> Dict[str, Any]:
        """
        Parses: 
        invariant name { 
            require( condition ) 
            else error( msg ) 
        }
        """
        self.consume("KEYWORD", "invariant")
        name = self.consume("ID").value
        self.consume("LBRACE")
        
        self.consume("KEYWORD", "require")
        self.consume("LPAREN")
        condition = self.parse_expression() # Simple "a < b" capture for now
        self.consume("RPAREN")
        
        error_msg = None
        if self.match("KEYWORD", "else"):
            self.consume("KEYWORD", "else")
            self.consume("KEYWORD", "error")
            self.consume("LPAREN")
            error_msg = self.consume("STRING").value
            self.consume("RPAREN")
            
        self.consume("RBRACE")
        
        return {
            "type": "Invariant",
            "name": name,
            "condition_raw": condition, # AST or raw string for v1
            "on_fail": error_msg
        }

    def parse_expression(self) -> str:
        """
        Captures expression tokens, handling nested parentheses.
        Stops when the initial (outer) parenthesis is closed.
        """
        expr_tokens = []
        paren_depth = 0
        
        # We are called AFTER consuming the opening LPAREN of require(...)
        # So we just read until we hit a closing RPAREN that brings depth to -1?
        # effectively, we are inside constraints.
        
        while self.pos < len(self.tokens):
            if self.check("LPAREN"):
                paren_depth += 1
            elif self.check("RPAREN"):
                if paren_depth == 0:
                    # Found the closing paren for the require call
                    break
                paren_depth -= 1
            
            expr_tokens.append(self.advance().value)
            
        return " ".join(expr_tokens)

    # --- Helper Methods ---

    def current(self) -> Token:
        if self.pos >= len(self.tokens):
            return Token("EOF", "", -1, -1)
        return self.tokens[self.pos]

    def advance(self) -> Token:
        if self.pos < len(self.tokens):
            t = self.tokens[self.pos]
            self.pos += 1
            return t
        raise SyntaxError("Unexpected End Of File")

    def check(self, type_name: str) -> bool:
        if self.pos >= len(self.tokens): return False
        return self.tokens[self.pos].type == type_name

    def match(self, type_name: str, value: str = None) -> bool:
        curr = self.current()
        if curr.type != type_name:
            return False
        if value and curr.value != value:
            return False
        return True

    def consume(self, type_name: str, value: str = None) -> Token:
        if self.match(type_name, value):
            return self.advance()
        expected = f"{type_name} '{value}'" if value else type_name
        raise SyntaxError(f"Expected {expected}, got {self.current()} at line {self.current().line}")

if __name__ == "__main__":
    import json
    code = """
    meta { id: "test-1" }
    entity Turbine {
        property temp : Float = 1000.0
        invariant safety {
            require( temp < 2000.0 )
            else error( "Too hot" )
        }
    }
    """
    lx = NeemaLexer(code)
    tokens = lx.tokenize()
    parser = NeemaParser(tokens)
    ast = parser.parse()
    print(json.dumps(ast, indent=2))
