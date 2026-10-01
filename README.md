# HL Interpreter

A simple custom interpreter written in Python for the HL programming language. It performs lexical analysis, parses statements, and executes the code.

## Features

- **Variables:** Supports `integer` and `double` data types.
- **Variable Declaration:** `<identifier>: <type>;`
- **Assignment:** `<identifier> := <value_or_expression>;`
- **Arithmetic:** Supports basic addition (`+`) and subtraction (`-`).
- **Output:** Output strings and variable values using `output << <value>;`.
- **Conditionals:** Basic `if` statements with comparison operators (`<`, `>`, `==`, `!=`).

## Usage

To run the interpreter, provide a source `.HL` file as a command-line argument:

```bash
python HLInt.py <filename>.HL
```

**Example:**
```bash
python HLInt.py PROG1.HL
```

## Generated Files

When the interpreter runs, it generates two files as part of its lexical analysis process:
1. `NOSPACES.TXT` - The source code with all spaces removed (except within string literals).
2. `RES_SYM.TXT` - A list of all reserved keywords and symbols extracted from the source code.

## Example Program
```hl
x: integer;
x := 3;
if (x < 5)
  output << x;
```
