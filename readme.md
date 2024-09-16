# Brainfuck Machine

The purpose of this project is to implement a simple virtual machine that
simulates a planned Minecraft redstone computer project. The ISA is simple
and intended to be packed into 8-bit opcodes containing 4-bit operator and
4-bit operand.

## Instruction Set Architecture

### Hardware (Abstraction)

The hardware abstraction of the system contains of the following:

- Program ROM: an addressable module of registers that contain opcodes
- Program Pointer: a register containing the address of the current opcode
- RAM: an addressable module of registers that are used for calculations
- Data Pointer: a register containing the current RAM address
- Stdin buffer: a buffer from which input bytes are read
- Stdout buffer: a buffer to which output bytes are written

Additionally, the Minecraft implementation will contain an instruction
decoder. All registers have a value range of 0-255 and will overflow and/or
underflow. Addresses are 8-bit, but I plan to use only memory modules of 64
bytes each.

### Operators

- `ADD`: adds the operand to the current RAM register
- `SUB`: subtracts the operand from the current RAM register
- `ADP`: adds the operand to the data pointer
- `SDP`: subtracts the operand from the data pointer
- `BIZ`: if the current RAM register is 0, add the operand to the program
pointer
- `BNZ`: if the current RAM register is not 0, subtracts the operand from the
program pointer
- `INP`: reads the next byte from Stdin into the current RAM register
- `OUT`: writes the current RAM register to Stdout
- `HLT`: halts execution of the program

The Minecraft redstone opcode decoder will interpret 0b0000 as `HLT`.

### Assembly Syntax

- Labels can be created with the label name followed by a colon, e.g. `loopstart1:`.
- The operators ADD, SUB, ADP, and SDP take an integer operand, e.g. "ADD 12".
- The operators BIZ and BNZ take an integer or label operand, e.g. "BIZ 15" or "BNZ loopstart1".
- The operators INP, OUT, and HLT take no operands.

Examples can be found in the "examples" folder.

## Compiler

The Brainfuck symbols map to the operators as follows:

- `+` -> `ADD 1`
- `-` -> `SUB 1`
- `>` -> `ADP 1`
- `<` -> `SDP 1`
- `[` -> `BIZ {offset}`
- `]` -> `BNZ {offset}`
- `,` -> `INP`
- `.` -> `OUT`

The offsets for BIZ and BNZ are determined by counting the number of opcodes in
the loop between `[` and `]`. The ISA allows for repeated `+`, `-`, `>`, or `<`
symbols to be combined into a single opcode as an optimization.


# How to Use

## Run Brainfuck

```bash
python brainfuck.py "+++>+++++[<+>-]<."
```

or

```bash
python brainfuck.py source_file.bf
```

If you want to use stdin, use a pipe or redirection, i.e.
`cat file | python brainfuck.py source_file.bf` or
`python brainfuck.py source_file.bf < file`.

To debug the program, add `-d` or `--debug` to the end of the command. This
will print a trace of all instructions run and then the whole stdout in hex
(normal output truncates least significant null bytes).

### Run Assembly

```bash
python asm.py "ADD 3 ADP 1 ADD 5 start: BIZ end SDP 1 ADD 1 ADP 1 SUB 1 BNZ start end: SDP 1 OUT"
```

or

```bash
python asm.py source_file.s
```

If you want to use stdin, use a pipe or redirection, i.e. `cat file | python asm.py source_file.s`
or `python asm.py source_file.s < file`.

To debug the program, add `-d` or `--debug` to the end of the command. This
will print a trace of all instructions run and then the whole stdout in hex
(normal output truncates least significant null bytes).


# License

ISC License

Copyleft (c) 2024 k98kurz

Permission to use, copy, modify, and/or distribute this software
for any purpose with or without fee is hereby granted, provided
that the above copyleft notice and this permission notice appear in
all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL 
WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE 
AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR
CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS
OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

