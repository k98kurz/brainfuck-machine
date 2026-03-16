"""
The BFF extension is inspired by the paper Computaitonal Life: How
Well-formed Self-replicating Programs Emerge from Simple Interaction
(https://arxiv.org/abs/2406.19108). The concept is that the program
tape and memory data are the same, allowing the program to modify
itself. An additional data pointer is added; stdin and stdout are
replaced with copying between pointers.

Instead of having 11 valid ops and 245 nops, as indicated in the
original paper, this has only 5 nops and stores operands in the lower
4 bits of each opcode.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from os.path import exists, isfile
from sys import argv, stdin


class Operator(Enum):
    HLT = 0
    ADD = 1 # add to data under first pointer: +
    SUB = 2 # sub from data undr first pointer: -
    S1P = 3 # sub first pointer: <
    A1P = 4 # add first pointer: >
    S2P = 5 # sub second pointer: {
    A2P = 6 # add second pointer: }
    CP1 = 7 # copy from first to second pointer ,
    CP2 = 8 # copy from second to first pointer .
    BIZ = 9 # branch if zero: [
    BNZ = 10 # branch if not zero: ]
    NOP11 = 11
    NOP12 = 12
    NOP13 = 13
    NOP14 = 14
    NOP15 = 15


@dataclass
class OpCode:
    operator: Operator = field(default=Operator.HLT)
    operand: int = 0

    def __repr__(self) -> str:
        return f'{self.operator.name} {self.operand}'

    def __bytes__(self) -> bytes:
        return ((self.operator.value << 4) + (self.operand & 15)).to_bytes(1, 'big')

    @classmethod
    def decode(cls, code: int):
        operator = (code & 240) >> 4
        operand = code & 15
        return cls(Operator(operator), operand)


SYMBOLS = [
    '+', # increment data under first pointer
    '-', # decrement data under first pointer
    '<', # decrement first pointer
    '>', # increment first pointer
    '{', # decrement second pointer
    '}', # increment second pointer
    ',', # copy from first pointer to second
    '.', # copy from second pointer to first
    '[', # branch if zero under first pointer
    ']', # branch if not zero under first pointer
]


def compile(code: str) -> list[OpCode]:
    assert code.count('[') == code.count(']'), 'unequal number of brackets'
    symbols = [s for s in code if s in SYMBOLS]
    opcodes = []
    idx = 0
    while idx < len(symbols):
        s = symbols[idx]
        match s:
            case '+':
                opcodes.append(OpCode(Operator.ADD, 1))
            case '-':
                opcodes.append(OpCode(Operator.SUB, 1))
            case '<':
                opcodes.append(OpCode(Operator.S1P, 1))
            case '>':
                opcodes.append(OpCode(Operator.A1P, 1))
            case '{':
                opcodes.append(OpCode(Operator.A2P, 1))
            case '}':
                opcodes.append(OpCode(Operator.S2P, 1))
            case ',':
                opcodes.append(OpCode(Operator.CP1, 1))
            case '.':
                opcodes.append(OpCode(Operator.CP2, 1))
            case '[':
                opcodes.append(OpCode(Operator.BIZ, 0))
            case ']':
                # find nearest [ with operand 0
                idx2 = idx
                while True:
                    idx2 -= 1
                    if  (   opcodes[idx2].operator is Operator.BIZ
                            and opcodes[idx2].operand == 0
                        ):
                        offset = idx - idx2
                        opcodes[idx2].operand = offset
                        opcodes.append(OpCode(Operator.BNZ, offset))
                        break
        idx += 1
    opcodes.append(OpCode(Operator.HLT, 0))
    return opcodes


def optimize(opcodes: list[OpCode]) -> list[OpCode]:
    """Combine consecutive OpCodes that use the same Operator up to an
        Operand of 15 to ensure the result can be encoded with 1 byte
        per OpCode, then adjust the branch offsets.
    """
    new_opcodes = []

    # first phase: combine opcodes
    i = 0
    acc = OpCode(opcodes[i].operator, opcodes[i].operand)
    while True:
        if i >= len(opcodes) - 1:
            new_opcodes.append(acc)
            break

        nextcode = OpCode(opcodes[i+1].operator, opcodes[i+1].operand)
        i += 1

        if  (   nextcode.operator != acc.operator
                or nextcode.operand + acc.operand >= 16
            ):
            new_opcodes.append(acc)
            acc = nextcode
            continue

        acc.operand += nextcode.operand

    # second phase: fix branch offsets
    def fix_branch_offsets(ops: list[OpCodes], start: int = 0) -> None:
        if start > 0:
            assert ops[start].operator == Operator.BIZ, (
                f'must start with BIZ ([); encountered {ops[start].operator.name}')
        else:
            for i in range(0, len(ops)):
                if ops[i].operator == Operator.BIZ:
                    start = i
                    break
            if start == 0:
                return

        depth = 0
        for i in range(start+1, len(ops)):
            if ops[i].operator == Operator.BIZ:
                depth += 1
                fix_branch_offsets(ops, i)
            elif ops[i].operator == Operator.BNZ:
                if depth == 0:
                    end = i
                    break
                else:
                    depth -= 1

        if end:
            offset = end - start
            ops[end].operand = offset
            ops[start].operand = offset

    fix_branch_offsets(new_opcodes)
    return new_opcodes


def decompile_to_asm(opcodes: list[OpCode]) -> str:
    """Decompile opcodes to the bff-asm representation."""
    src = ''
    indent_level = 0
    indentation = lambda: '    ' * indent_level
    representation = lambda oc: f'{oc.operator.name.lower()} {oc.operand}'
    last = None
    add_ops = (
        Operator.ADD,
        Operator.A1P, Operator.A2P,
        Operator.S1P, Operator.S2P,
        Operator.CP1, Operator.CP2,
    )
    sub_ops = (
        Operator.SUB,
        Operator.A1P, Operator.A2P,
        Operator.S1P, Operator.S2P,
        Operator.CP1, Operator.CP2,
    )
    for oc in opcodes:
        if oc.operator == Operator.BIZ:
            if last and last.operator not in (Operator.BIZ, Operator.BNZ):
                src += '\n'
            src += f'{indentation()}{representation(oc)}'
            indent_level += 1

        elif oc.operator == Operator.BNZ:
            if last and last.operator not in (Operator.BIZ, Operator.BNZ):
                src += '\n'
            indent_level -= 1
            src += f'{indentation()}{representation(oc)}'

        else:
            if not last:
                src += indentation() + representation(oc)

            elif oc.operator in add_ops:
                if (last and last.operator in add_ops):
                    src += f' {representation(oc)}'
                else:
                    src += f'\n{indentation()}{representation(oc)}'

            elif oc.operator in sub_ops:
                if (last and last.operator in sub_ops):
                    src += f' {representation(oc)}'
                else:
                    src += f'\n{indentation()}{representation(oc)}'

        last = oc

    return src


class Buffer:
    data: bytearray
    ptr: int
    size: int

    def __init__(self, size: int = 256):
        self.data = bytearray(size)
        self.ptr = 0
        self.size = size

    def read(self) -> int:
        val = self.data[self.ptr]
        self.ptr = (self.ptr + 1) % self.size
        return val

    def write(self, val: int):
        self.data[self.ptr] = val
        self.ptr = (self.ptr + 1) % self.size

    def __bytes__(self) -> bytes:
        return bytes(self.data)


def run(
        opcodes: list[OpCode], debug: bool = False, max_steps: int = 2**16,
    ) -> Buffer:
    instr_ptr, data_ptr1, data_ptr2 = 0, 0, 0
    trace = []
    steps_executed = 1
    # initialize buffer
    buffer = bytearray(b''.join([bytes(o) for o in opcodes]))
    size = len(buffer)

    while steps_executed <= max_steps:
        op = OpCode.decode(buffer[instr_ptr])
        if debug:
            trace.append(op)
            if steps_executed % 1000 == 0:
                print(' '.join([repr(o) for o in trace]), end=" ")
                trace.clear()

        match op.operator:
            case Operator.ADD:
                buffer[data_ptr1] = (buffer[data_ptr1] + op.operand) % 256
            case Operator.SUB:
                buffer[data_ptr1] = (256 + buffer[data_ptr1] - op.operand) % 256
            case Operator.A1P:
                data_ptr1 += op.operand
                if data_ptr1 >= size:
                    data_ptr1 = 0
            case Operator.S1P:
                data_ptr1 -= op.operand
                if data_ptr1 < 0:
                    data_ptr1 = size - 1
            case Operator.A2P:
                data_ptr2 += op.operand
                if data_ptr2 >= size:
                    data_ptr2 = 0
            case Operator.S2P:
                data_ptr2 -= op.operand
                if data_ptr2 < 0:
                    data_ptr2 = size - 1
            case Operator.CP1:
                buffer[data_ptr2] = buffer[data_ptr1]
            case Operator.CP2:
                buffer[data_ptr1] = buffer[data_ptr2]
            case Operator.BIZ:
                if buffer[data_ptr1] == 0:
                    instr_ptr = (instr_ptr + op.operand) % len(buffer)
            case Operator.BNZ:
                if buffer[data_ptr1] != 0:
                    instr_ptr = (len(buffer) + instr_ptr - op.operand) % len(buffer)
            case Operator.HLT:
                break

        steps_executed += 1
        instr_ptr += 1
        if instr_ptr >= len(buffer):
            instr_ptr = 0

    if debug and trace:
        print(' '.join([repr(o) for o in trace]))

    return buffer


def compile_asm(code: str) -> list[OpCode]:
    symbols = code.split()
    ops = []
    labels = {}
    index_map = {}

    # first find labels
    for i in range(len(symbols)):
        if symbols[i][-1] == ':':
            labels[symbols[i][:-1]] = i

    i = 0
    while i < len(symbols):
        operator = symbols[i]
        i2 = i
        if operator in ('add', 'sub', 'a1p', 's1p', 'a2p', 's2p', 'biz', 'bnz'):
            assert len(symbols) > i + 1, f'missing operand for {operator}'
            operand = symbols[i+1]
            i += 1
        if operator in ('add', 'sub', 'a1p', 's1p', 'a2p', 's2p'):
            assert operand.isnumeric(), f'operand for {operator} must be integer'
        if operator in ('biz', 'bnz') and not operand.isnumeric():
            assert operand in labels, (
                f'operand for {operator} must be integer or valid label')
        match operator:
            case 'add':
                ops.append(OpCode(Operator.ADD, int(operand)))
            case 'sub':
                ops.append(OpCode(Operator.SUB, int(operand)))
            case 'a1p':
                ops.append(OpCode(Operator.A1P, int(operand)))
            case 's1p':
                ops.append(OpCode(Operator.S1P, int(operand)))
            case 'a2p':
                ops.append(OpCode(Operator.A2P, int(operand)))
            case 's2p':
                ops.append(OpCode(Operator.S2P, int(operand)))
            case 'biz':
                if operand.isnumeric():
                    ops.append(OpCode(Operator.BIZ, int(operand)))
                else:
                    ops.append(OpCode(Operator.BIZ, 0))
            case 'bnz':
                if operand.isnumeric():
                    ops.append(OpCode(Operator.BNZ, int(operand)))
                else:
                    # find nearest biz with operand 0
                    idx = idx2 = len(ops)
                    while True:
                        idx2 -= 1
                        if ops[idx2].operator is Operator.BIZ and ops[idx2].operand == 0:
                            offset = idx - idx2
                            ops[idx2].operand = offset
                            ops.append(OpCode(Operator.BNZ, offset))
                            break
            case 'cp1':
                ops.append(OpCode(Operator.CP1))
            case 'cp2':
                ops.append(OpCode(Operator.CP2))
            case 'hlt':
                ops.append(OpCode(Operator.HLT))
            case _:
                assert operator[-1] == ':', (
                    f'unrecognized symbol {operator} (not a label; {i=})')
        i += 1
        index_map[i2] = len(ops)-1

    return ops



def main():
    if len(argv) < 2:
        print(
            f'use:\t{argv[0]} src_code_or_file_path '
            '[--debug|--compile|--asm|--toasm|--hex]'
        )
        exit()

    debug = len(argv) > 2 and argv[2] in ('debug', '--debug', '-d', 'd')
    justcompile = len(argv) > 2 and argv[2] in ('compile', '--compile', '-c', 'c')
    usehex = len(argv) > 2 and argv[2] in ('hex', '--hex', '-x', 'x')

    if exists(argv[1]) and isfile(argv[1]):
        with open(argv[1], 'r') as f:
            codes = compile(f.read())
    else:
        codes = compile(argv[1])

    if justcompile:
        print(f'{len(codes)} ops')
        print(' '.join([f'{op.operator.name}:{op.operand}' for op in codes]))
        return

    result = run(codes, debug=debug)

    if usehex or debug:
        print(bytes(result).hex())

    print([OpCode.decode(o) for o in result])


if __name__ == '__main__':
    main()


