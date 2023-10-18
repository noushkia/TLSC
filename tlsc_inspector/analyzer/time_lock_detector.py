from evmdasm import EvmDisassembler


def check_bytecode_time_lock(bytecode):
    # todo: move the disassembler creation to the top level
    disassembler = EvmDisassembler(bytecode)
    instructions = list(disassembler.disassemble(bytecode))
    has_timestamp = has_timestamp_condition(instructions)
    return has_timestamp


def has_timestamp_condition(instructions):
    # todo: Need to check if the timestamp is used in a condition not simply if it is used
    for instruction in instructions:
        if instruction.name in ["TIMESTAMP", "BLOCKHASH", "NUMBER"]:
            return True
    return False
