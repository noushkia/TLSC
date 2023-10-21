from analyzer.disasm import disassemble_for_time_lock


def bytecode_has_potential_time_lock(bytecode: str) -> bool:
    instructions = disassemble_for_time_lock(bytecode)
    if instructions is None:
        return True
    return False
