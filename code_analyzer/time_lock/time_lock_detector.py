from code_analyzer.disasm import disassemble_for_time_lock


def bytecode_has_potential_time_lock(bytecode: str) -> bool:
    """
    Checks if time-lock opcodes, i.e., TIMESTAMP and NUMBER, are in the disassembler bytecode.
    :param bytecode:  The bytecode to check
    :return: True if there are such opcodes, false otherwise.
    """
    instructions = disassemble_for_time_lock(bytecode)
    if instructions is None:
        return True
    return False


def bytecode_has_time_lock(bytecode: str) -> bool:
    """
    Checks there are time locks in the source code based on the call graph of the bytecode.

    :param bytecode:  The bytecode to check
    :return: True if there is a time lock + The node which had the time lock.
    """
    pass
