from typing import List

from tlsc_inspector.analyzer.disasm import disassemble


def bytecode_has_time_lock(bytecode: str) -> bool:
    instructions = disassemble(bytecode)
    return has_time_lock_condition(instructions)


def has_time_lock_condition(instructions: List) -> bool:
    # todo: Need to check if the timestamp is used in a condition not simply if it is used
    # todo: Can optimize this by checking for the timestamp opcode during disassembly
    for instruction in instructions:
        if instruction.opcode in ["TIMESTAMP", "NUMBER"]:
            return True
    return False
