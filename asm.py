from brainfuck import OpCode, Operator, run
from os.path import exists, isfile
from sys import argv, stdin


def compile(code: str) -> list[OpCode]:
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
        if operator in ('add', 'sub', 'adp', 'sdp', 'biz', 'bnz'):
            assert len(symbols) > i + 1, f'missing operand for {operator}'
            operand = symbols[i+1]
            i += 1
        if operator in ('add', 'sub', 'adp', 'sdp'):
            assert operand.isnumeric(), f'operand for {operator} must be integer'
        if operator in ('biz', 'bnz') and not operand.isnumeric():
            assert operand in labels, f'operand for {operator} must be integer or valid label'
        match operator:
            case 'add':
                ops.append(OpCode(Operator.ADD, int(operand)))
            case 'sub':
                ops.append(OpCode(Operator.SUB, int(operand)))
            case 'adp':
                ops.append(OpCode(Operator.ADP, int(operand)))
            case 'sdp':
                ops.append(OpCode(Operator.SDP, int(operand)))
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
            case 'inp':
                ops.append(OpCode(Operator.INP)) 
            case 'out':
                ops.append(OpCode(Operator.OUT)) 
            case 'hlt':
                ops.append(OpCode(Operator.HLT))
            case _:
                assert operator[-1] == ':', f'unrecognized symbol {operator} (not a label; {i=})'
        i += 1
        index_map[i2] = len(ops)-1

    return ops

def main():
    if len(argv) < 2:
        print(f'use:\t{argv[0]} src_code_or_file_path [--debug]')
        print('\t{argv[0]} src_code_or_file_path [--debug] < input')
        print('\t[command] | {argv[0]} src_code_or_file_path [--debug]')
        exit()
    debug = len(argv) > 2 and argv[2] in ('debug', '--debug', '-d', 'd')
    if exists(argv[1]) and isfile(argv[1]):
        with open(argv[1], 'r') as f:
            codes = compile(f.read())
    else:
        codes = compile(argv[1])

    result = run(codes, stdinpt=stdin, debug=debug)

    if debug:
        print(bytes(result).hex())
    else:
        result = bytes(result).split(b'\x00')
        print(b'\x00'.join([r for r in result if int.from_bytes(r, 'big')]))


if __name__ == '__main__':
    main()


