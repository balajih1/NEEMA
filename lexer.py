
import re
from typing import List, Tuple, NamedTuple

class Token(NamedTuple):
    type: str # e.g., 'KEYWORD', 'IDENTIFIER', 'STRING', 'LBRACE'
    value: str
    line: int
    column: int

class NeemaLexer:
    """
    NEEMA Lexer - The first step of the NEEMA Compiler.
    Responsibility: Break raw text into meaningful 'Tokens'.
    """
    
    # NEEMA Language Keywords
    KEYWORDS = {
        'meta', 'entity', 'invariant', 'geometry',
        'property', 'primitive', 'require', 'else', 'error', 'if',
        'String', 'Float', 'Boolean', 'Integer', 'Material', 'Load',
        'and', 'or', 'not'
    }

    # Token Specification (Regex)
    TOKEN_SPECS = [
        ('COMMENT',  r'//.*'),             # Comments (ignore rest of line)
        ('NUMBER',   r'\d+(\.\d*)?'),      # Integer or decimal number
        ('STRING',   r'"[^"]*"'),          # String literals
        ('ID',       r'[A-Za-z_][A-Za-z0-9_]*'), # Identifiers
        ('EQ',       r'=='),               # Equality check must be before ASSIGN
        ('ASSIGN',   r'='),                # Assignment operator
        ('LBRACE',   r'\{'),               # {
        ('RBRACE',   r'\}'),               # }
        ('LPAREN',   r'\('),               # (
        ('RPAREN',   r'\)'),               # )
        ('COLON',    r':'),                # :
        ('COMMA',    r','),                # ,
        ('DOT_DOT',  r'\.\.'),             # .. (Range)
        ('DOT',      r'\.'),               # .
        ('OP',       r'[+\-*/<>=!]+'),     # Operators
        ('NEWLINE',  r'\n'),               # Line endings
        ('SKIP',     r'[ \t]+'),           # Skip over spaces/tabs
        ('MISMATCH', r'.'),                # Any other character
    ]

    def __init__(self, code: str):
        self.code = code
        self.tokens = []
        self.line_num = 1
        self.line_start = 0

    def tokenize(self) -> List[Token]:
        pos = 0
        while pos < len(self.code):
            match = None
            for token_type, pattern in self.TOKEN_SPECS:
                regex = re.compile(pattern)
                match = regex.match(self.code, pos)
                if match:
                    text = match.group(0)
                    if token_type == 'NEWLINE':
                        self.line_start = pos + len(text)
                        self.line_num += 1
                    elif token_type == 'SKIP' or token_type == 'COMMENT':
                        pass
                    elif token_type == 'MISMATCH':
                        raise SyntaxError(f"Unexpected character '{text}' at line {self.line_num}")
                    else:
                        # Special check: Is this ID actually a Keyword?
                        refined_type = token_type
                        if token_type == 'ID' and text in self.KEYWORDS:
                            refined_type = 'KEYWORD'
                        
                        token = Token(
                            type=refined_type, 
                            value=text, 
                            line=self.line_num, 
                            column=pos - self.line_start
                        )
                        self.tokens.append(token)
                    
                    pos = match.end(0)
                    break
            
            if not match:
                # Should be caught by MISMATCH, but just in case
                raise SyntaxError(f"Lexer got stuck at line {self.line_num}")
        
        return self.tokens

if __name__ == "__main__":
    # Test the Lexer with a sample snippet
    sample_code = """
    meta {
        id: "uuid-123"
        authority: "IGIGI"
    }
    
    entity Engine {
        property max_thrust: Float = 500.0
    }
    """
    
    print(f"Tokenizing NEEMA code...\n")
    lexer = NeemaLexer(sample_code)
    try:
        tokens = lexer.tokenize()
        for t in tokens:
            print(f"{t.line}:{t.column} \t {t.type} \t {t.value}")
    except SyntaxError as e:
        print(f"Error: {e}")
