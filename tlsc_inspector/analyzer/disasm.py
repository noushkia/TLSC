import re
from functools import lru_cache
from typing import List

from tlsc_inspector.analyzer.opcodes import ADDRESS_OPCODE_MAPPING

regex_PUSH = re.compile(r"^PUSH(\d*)$")


def safe_decode(hex_encoded_string: str) -> bytes:
    """
    Safely decode a hex encoded string.

    :param hex_encoded_string: The hex encoded string
    :return: The decoded string
    """
    if hex_encoded_string.startswith("0x"):
        return bytes.fromhex(hex_encoded_string[2:])
    else:
        return bytes.fromhex(hex_encoded_string)


class EvmInstruction:
    """Object to hold the information of the disassembly."""

    def __init__(self, address, opcode, argument=None):
        self.address = address
        self.opcode = opcode
        self.argument = argument

    def __str__(self):
        return "{}{}".format(self.opcode, f" {self.argument}" if self.argument is not None else "")


lru_cache(maxsize=2 ** 10)


def disassemble(bytecode: str) -> List[EvmInstruction]:
    """Disassembles evm bytecode and returns a list of instructions.

    :param bytecode: The bytecode to disassemble
    :return: A list of EvmInstruction objects
    """
    instruction_list = []
    address = 0

    bytecode = safe_decode(bytecode)
    length = len(bytecode)
    part_code = bytecode[-43:]

    try:
        if "bzzr" in str(part_code):
            # ignore swarm hash
            length -= 43
    except ValueError:
        pass

    while address < length:
        try:
            opcode = ADDRESS_OPCODE_MAPPING[bytecode[address]]
        except KeyError:
            instruction_list.append(EvmInstruction(address, "INVALID"))
            address += 1
            continue

        current_instruction = EvmInstruction(address, opcode)

        match = re.search(regex_PUSH, opcode)
        if match:
            argument_bytes = bytecode[address + 1: address + 1 + int(match.group(1))]
            if type(argument_bytes) == bytes:
                current_instruction.argument = "0x" + argument_bytes.hex()
            else:
                current_instruction.argument = argument_bytes
            address += int(match.group(1))

        instruction_list.append(current_instruction)
        address += 1

    return instruction_list
