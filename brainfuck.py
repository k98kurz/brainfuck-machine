from dataclasses import dataclass, field
from enum import Enum
from os.path import exists, isfile
from sys import argv, stdin


class Operator(Enum):
    HLT = 0
    ADD = 1
    SUB = 2
    ADP = 3
    SDP = 4
    BIZ = 5
    BNZ = 6
    INP = 7
    OUT = 8


@dataclass
class OpCode:
    operator: Operator = field(default=Operator.HLT)
    operand: int = 0

    def __bytes__(self) -> bytes:
        return (self.operator.value * 8 + self.operand).to_bytes(1, 'big')

    @classmethod
    def decode(cls, code: int):
        operator = code // 8
        operand = code - (operator * 8)
        return cls(operator, operand)


SYMBOLS = [
    '+',
    '-',
    '>',
    '<',
    '[',
    ']',
    ',',
    '.',
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
            case '>':
                opcodes.append(OpCode(Operator.ADP, 1))
            case '<':
                opcodes.append(OpCode(Operator.SDP, 1))
            case ',':
                opcodes.append(OpCode(Operator.INP, 1))
            case '.':
                opcodes.append(OpCode(Operator.OUT, 1))
            case '[':
                opcodes.append(OpCode(Operator.BIZ, 0))
            case ']':
                # find nearest [ with operand 0
                idx2 = idx
                while True:
                    idx2 -= 1
                    if opcodes[idx2].operator is Operator.BIZ and opcodes[idx2].operand == 0:
                        offset = idx - idx2
                        opcodes[idx2].operand = offset
                        opcodes.append(OpCode(Operator.BNZ, offset))
                        break
        idx += 1
    opcodes.append(OpCode(Operator.HLT, 0))
#    return b''.join([bytes(o) for o in opcodes])
    return opcodes


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


def run(opcodes: list[OpCode], buffer_size: int = 256, stdinpt: Buffer = None,
        debug: bool = False, hexinput: bool = False) -> Buffer:
    buffer = bytearray(buffer_size)
    data_ptr = 0
    instr_ptr = 0
    stdinpt = stdinpt or Buffer(buffer_size)
    inptbuf = Buffer(buffer_size)
    hasinpt = False
    stdout = Buffer(buffer_size)
    trace = []

    while instr_ptr < len(opcodes):
        op = opcodes[instr_ptr]
        if debug:
            trace.append(op)
        match op.operator:
            case Operator.ADD:
                buffer[data_ptr] = (buffer[data_ptr] + op.operand) % 256
            case Operator.SUB:
                buffer[data_ptr] = (256 + buffer[data_ptr] - op.operand) % 256
            case Operator.ADP:
                data_ptr += op.operand
            case Operator.SDP:
                data_ptr -= op.operand
            case Operator.INP:
                if not hasinpt:
                    inp = stdinpt.read()
                    inp = bytes.fromhex(inp) if hexinput else inp
                    for i in range(len(inp)):
                        inptbuf.write(inp[i])
                    hasinpt = True
                    inptbuf.ptr = 0
                buffer[data_ptr] = inptbuf.read()
            case Operator.OUT:
                stdout.write(buffer[data_ptr])
            case Operator.BIZ:
                if buffer[data_ptr] == 0:
                    instr_ptr += op.operand
            case Operator.BNZ:
                if buffer[data_ptr] != 0:
                    instr_ptr -= op.operand
            case Operator.HLT:
                break
        instr_ptr += 1

    if debug:
        print(' '.join([f'{op.operator.name}:{op.operand}' for op in trace]))

    return stdout


def main():
    if len(argv) < 2:
        print(f'use:\t{argv[0]} src_code_or_file_path [--debug|--compile|--hex]')
        print('\t{argv[0]} src_code_or_file_path [--debug|--compile|--hex] < input')
        print('\t[command] | {argv[0]} src_code_or_file_path [--debug|--compile|--hex]')
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

    result = run(codes, stdinpt=stdin, debug=debug, hexinput=usehex)

    if debug:
        print(bytes(result).hex())
    else:
        result = bytes(result).split(b'\x00')
        if usehex:
            print('00'.join([r.hex() for r in result if int.from_bytes(r, 'big')]))
        else:
            print(b'\x00'.join([r for r in result if int.from_bytes(r, 'big')]))


if __name__ == '__main__':
    main()


