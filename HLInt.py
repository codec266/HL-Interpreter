import sys
import re
import os

class HLInterpreter:
    def __init__(self, source_code):
        self.source_code = source_code
        self.tokens = []
        self.pos = 0
        self.vars = {}
        self.error = False
        self.output_buffer = []

    def generate_nospaces(self):
        """Removes spaces except inside string literals and writes to NOSPACES.TXT"""
        nospace_chars = []
        in_string = False
        for char in self.source_code:
            if char == '"':
                in_string = not in_string
                nospace_chars.append(char)
            elif in_string:
                nospace_chars.append(char)
            elif not char.isspace():
                nospace_chars.append(char)
                
        nospace_code = "".join(nospace_chars)
        with open("NOSPACES.TXT", "w") as f:
            f.write(nospace_code)

    def tokenize_and_extract(self):
        """Tokenizes the code and writes reserved words/symbols to RES_SYM.TXT"""
        # Token specifications
        token_regex = r'("[^"]*")|(==|!=|:=|<<|<=|>=|[<>\+\-\(\):;])|\b(integer|double|output|if)\b|([a-zA-Z_]\w*)|(\d+(?:\.\d+)?)'
        
        symbols_set = {':', ';', ':=', '+', '-', '<<', '<', '>', '==', '!=', '(', ')'}
        reserved_set = {'integer', 'double', 'output', 'if'}
        
        found_res_sym = []
        
        # re.IGNORECASE to handle instances like "If" and "Output"
        for match in re.finditer(token_regex, self.source_code, re.IGNORECASE):
            string_val = match.group(1)
            symbol = match.group(2)
            keyword = match.group(3)
            ident = match.group(4)
            number = match.group(5)
            
            if symbol:
                if symbol in symbols_set: found_res_sym.append(symbol)
                self.tokens.append(('OPERATOR' if symbol in [':=','<<','==','!=','<','>','+','-'] else 'PUNCTUATION', symbol))
            elif keyword:
                kw_lower = keyword.lower()
                if kw_lower in reserved_set: found_res_sym.append(kw_lower)
                self.tokens.append(('TYPE' if kw_lower in ['integer', 'double'] else 'KEYWORD', kw_lower))
            elif ident:
                self.tokens.append(('IDENTIFIER', ident))
            elif number:
                self.tokens.append(('NUMBER', number))
            elif string_val:
                self.tokens.append(('STRING', string_val))
                
        with open("RES_SYM.TXT", "w") as f:
            f.write("\n".join(found_res_sym))

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self, expected_type, expected_val=None):
        token = self.peek()
        if not token:
            self.error = True
            return None
        if token[0] == expected_type and (expected_val is None or (isinstance(token[1], str) and token[1].lower() == expected_val.lower())):
            self.pos += 1
            return token
        self.error = True
        return None

    def parse_value(self):
        tok = self.peek()
        if not tok:
            self.error = True
            return 0
            
        if tok[0] == 'NUMBER':
            self.consume('NUMBER')
            return float(tok[1]) if '.' in tok[1] else int(tok[1])
        elif tok[0] == 'IDENTIFIER':
            ident = self.consume('IDENTIFIER')[1].lower() # Handle case-insensitivity (x vs X)
            if ident in self.vars:
                return self.vars[ident]['value']
            else:
                self.error = True
                return 0
        self.error = True
        return 0

    def parse_statement(self, execute=True):
        token = self.peek()
        if not token: return False

        if token[0] == 'IDENTIFIER':
            ident = self.consume('IDENTIFIER')[1].lower()
            next_tok = self.peek()
            
            if next_tok and next_tok[1] == ':':  # Variable Declaration
                self.consume('PUNCTUATION', ':')
                type_tok = self.consume('TYPE')
                self.consume('PUNCTUATION', ';')
                if self.error: return False
                if execute:
                    self.vars[ident] = {'type': type_tok[1].lower(), 'value': 0}
                return True
                
            elif next_tok and next_tok[1] == ':=':  # Assignment
                self.consume('OPERATOR', ':=')
                val1 = self.parse_value()
                op = self.peek()
                
                result = val1
                if op and op[1] in ['+', '-']: # Math Operations
                    op_val = self.consume('OPERATOR')[1]
                    val2 = self.parse_value()
                    if execute:
                        if op_val == '+': result = val1 + val2
                        elif op_val == '-': result = val1 - val2
                        
                self.consume('PUNCTUATION', ';')
                if self.error: return False
                if execute:
                    # Enforce precision of 2 for doubles
                    if isinstance(result, float):
                        result = round(result, 2)
                    self.vars[ident]['value'] = result
                return True
            else:
                self.error = True
                return False

        elif token[0] == 'KEYWORD' and token[1] == 'output':  # Output Statement
            self.consume('KEYWORD', 'output')
            self.consume('OPERATOR', '<<')
            val_tok = self.peek()
            val = None
            if val_tok and val_tok[0] == 'STRING':
                val = self.consume('STRING')[1].strip('"')
            else:
                val = self.parse_value()
                
            self.consume('PUNCTUATION', ';')
            if self.error: return False
            if execute:
                if isinstance(val, float):
                    self.output_buffer.append(f"{val:.2f}")
                else:
                    self.output_buffer.append(str(val))
            return True
            
        elif token[0] == 'KEYWORD' and token[1] == 'if':  # Conditional Statement
            self.consume('KEYWORD', 'if')
            self.consume('PUNCTUATION', '(')
            left_val = self.parse_value()
            op = self.consume('OPERATOR')[1]
            right_val = self.parse_value()
            self.consume('PUNCTUATION', ')')
            
            if self.error: return False
            
            cond_true = False
            if execute:
                if op == '<': cond_true = left_val < right_val
                elif op == '>': cond_true = left_val > right_val
                elif op == '==': cond_true = left_val == right_val
                elif op == '!=': cond_true = left_val != right_val
                
            # If the condition is false, we still parse the inner statement to check for syntax 
            # errors, but we pass execute=False so variables aren't altered and output isn't printed.
            return self.parse_statement(execute=(execute and cond_true))
            
        self.error = True
        return False

    def run(self):
        self.generate_nospaces()
        self.tokenize_and_extract()
        
        # Parse all statements
        while self.pos < len(self.tokens) and not self.error:
            self.parse_statement(execute=True)
            
        if self.error or self.pos < len(self.tokens):
            print("ERROR")
        else:
            print("NO ERROR(S) FOUND")
            for out in self.output_buffer:
                print(out)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python HLInt.py ")
        sys.exit(1)
        
    filename = sys.argv[1]
    if not os.path.exists(filename):
        print(f"File '{filename}' not found.")
        sys.exit(1)
        
    with open(filename, 'r') as file:
        source = file.read()
        
    interpreter = HLInterpreter(source)
    interpreter.run()