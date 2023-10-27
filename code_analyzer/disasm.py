import re
from functools import lru_cache
from typing import List

from code_analyzer.opcodes import ADDRESS_OPCODE_MAPPING

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


def disassemble_for_time_lock(bytecode: str) -> List[EvmInstruction] | None:
    """Disassembles evm bytecode and returns a list of instructions if there is no time lock condition.
    Returns None if there is a time lock condition.

    :param bytecode: The bytecode to disassemble
    :return: A list of EvmInstruction objects or None
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

        if opcode in ["NUMBER", "TIMESTAMP"]:
            return None

        current_instruction = EvmInstruction(address, opcode)

        match = re.search(regex_PUSH, opcode)
        if match:
            argument_bytes = bytecode[address + 1: address + 1 + int(match.group(1))]
            if type(argument_bytes) is bytes:
                current_instruction.argument = "0x" + argument_bytes.hex()
            else:
                current_instruction.argument = argument_bytes
            address += int(match.group(1))

        instruction_list.append(current_instruction)
        address += 1

    return instruction_list


if __name__ == "__main__":
    bytecode = "0x6060604052361561027c5760e060020a600035046301991313811461027e57806303d22885146102ca5780630450991814610323578063049ae734146103705780630ce46c43146103c35780630e85023914610602578063112e39a8146106755780631b4fa6ab146106c25780631e74a2d3146106d057806326a7985a146106fd5780633017fe2414610753578063346cabbc1461075c578063373a1bc3146107d55780633a9e74331461081e5780633c2c21a01461086e5780633d9ce89b146108ba578063480b70bd1461092f578063481078431461097e57806348f0518714610a0e5780634c471cde14610a865780634db3da8314610b09578063523ccfa814610b4f578063586a69fa14610be05780635a9f2def14610c3657806364ee49fe14610caf57806367beaccb14610d055780636840246014610d74578063795b9a6f14610dca5780637b55c8b514610e415780637c73f84614610ee15780638c0e156d14610f145780638c1d01c814610f605780638e46afa914610f69578063938c430714610fc0578063971c803f146111555780639772c982146111ac57806398c9cdf41461122857806398e00e541461127f5780639f927be7146112d5578063a00aede914611383578063a1c0539d146113d3578063aff21c6514611449578063b152f19e14611474578063b549793d146114cb578063b5b33eda1461154b578063bbc6eb1f1461159b578063c0f68859146115ab578063c3a2c0c314611601578063c43d05751461164b578063d8e5c04814611694578063dbfef71014611228578063e29fb547146116e7578063e6470fbe1461173a578063ea27a8811461174c578063ee77fe86146117d1578063f158458c14611851575b005b611882600435602435604435600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea346350d4e41160016000503387876020604051908101604052806000815260200150612225610f6d565b61188260043560243560443560643560843560a43560c435600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea346350d4e4116001600050338b8a6020604051908101604052806000815260200150896125196106c6565b611882600435600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea346350d4e41160016000503385600060e060020a026020604051908101604052806000815260200150611e4a610f6d565b611882600435602435604435606435608435600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea346350d4e41160016000503389896020604051908101604052806000815260200150886124e86106c6565b604080516020604435600481810135601f8101849004840285018401909552848452611882948135946024803595939460649492939101918190840183828082843750506040805160a08082019092529597963596608435969095506101449450925060a491506005908390839080828437509095505050505050604080518082018252600160a060020a03338116825288166020820152815160c0810190925260009173e54d323f9ef17c1f0dede47ecc86a9718fe5ea349163e3042c0f91600191908a908a9089908b90808b8b9090602002015181526020018b60016005811015610002579090602002015181526020018b60026005811015610002579090602002015181526020018b60036005811015610002579090602002015181526020018b6004600581101561000257909060200201518152602001348152602001506040518860e060020a02815260040180888152602001876002602002808383829060006004602084601f0104600f02600301f150905001868152602001806020018560ff1681526020018461ffff168152602001836006602002808383829060006004602084601f0104600f02600301f1509050018281038252868181518152602001915080519060200190808383829060006004602084601f0104600f02600301f150905090810190601f1680156105d25780820380516001836020036101000a031916815260200191505b509850505050505050505060206040518083038160008760325a03f2156100025750506040515191506124cd9050565b60408051602060248035600481810135601f81018590048502860185019096528585526118829581359591946044949293909201918190840183828082843750949650505050505050600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea346350d4e411600133808787611e64610f6d565b611882600435600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea346350d4e41160016000503333600060e060020a026020604051908101604052806000815260200150611d28610f6d565b61189f5b6000611bf8611159565b6118b7600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea3463ea27a881600060005054611a9561159f565b6118b7600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea346326a7985a6040518160e060020a02815260040180905060206040518083038160008760325a03f2156100025750506040515191506107599050565b6118b760075b90565b604080516020606435600481810135601f8101849004840285018401909552848452611882948135946024803595604435956084949201919081908401838280828437509496505093359350505050600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea346350d4e41160013389898861224b610f6d565b611882600435602435600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea346350d4e41160016000503386866020604051908101604052806000815260200150611e64610f6d565b611882600435602435604435606435600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea346350d4e41160016000503333896020604051908101604052806000815260200150886123bc6106c6565b611882600435602435604435600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea346350d4e41160016000503387866020604051908101604052806000815260200150611f8d610f6d565b60408051602060248035600481810135601f810185900485028601850190965285855261188295813595919460449492939092019181908401838280828437509496505093359350505050600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea346350d4e411600133808888612225610f6d565b611882600435602435604435606435600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea346350d4e41160016000503388886020604051908101604052806000815260200150612388610f6d565b611882600435604080517fc4144b2600000000000000000000000000000000000000000000000000000000815260016004820152600160a060020a03831660248201529051600091737c1eb207c07e7ab13cf245585bd03d0fa478d0349163c4144b26916044818101926020929091908290030181878760325a03f215610002575050604051519150611b409050565b604080516020604435600481810135601f81018490048402850184019095528484526118829481359460248035959394606494929391019181908401838280828437509496505093359350505050600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea346350d4e411600133888888612238610f6d565b604080516020604435600481810135601f810184900484028501840190955284845261188294813594602480359593946064949293910191819084018382808284375094965050933593505060843591505060a43560c435600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea346350d4e4116001338b8b8b896126536106c6565b611882600435600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea346350d4e41160016000503333866020604051908101604052806000815260200150611e4a610f6d565b6118b76004355b604080517fed5bd7ea00000000000000000000000000000000000000000000000000000000815260016004820152600160a060020a03831660248201529051600091737c1eb207c07e7ab13cf245585bd03d0fa478d0349163ed5bd7ea916044818101926020929091908290030181878760325a03f215610002575050604051519150611b409050565b61189f600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea3463586a69fa6040518160e060020a02815260040180905060206040518083038160008760325a03f2156100025750506040515191506107599050565b60408051602060248035600481810135601f81018590048502860185019096528585526118829581359591946044949293909201918190840183828082843750949650509335935050606435915050600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea346350d4e411600133808989612388610f6d565b61188260043560243560443560643560843560a435600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea346350d4e4116001600050338a896020604051908101604052806000815260200150886124d76106c6565b6040805160206004803580820135601f8101849004840285018401909552848452611882949193602493909291840191908190840183828082843750949650505050505050600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea346350d4e411600133808587611e4a610f6d565b61188260043560243560443560643560843560a435600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea346350d4e4116001600050338a8a60206040519081016040528060008152602001508961262d6106c6565b604080516020606435600481810135601f810184900484028501840190955284845261188294813594602480359560443595608494920191908190840183828082843750949650505050505050600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea346350d4e4116001338888876120c7610f6d565b604080516020604435600481810135601f81018490048402850184019095528484526118829481359460248035959394606494929391019181908401838280828437505060408051608080820190925295979635969561010495509350608492508591508390839080828437509095505050505050600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea346350d4e4116001338989898961263a6106c6565b6118b7600435602435604435600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea3463ea27a881858585611ba361122c565b611882600435602435604435600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea346350d4e4116001600050333388602060405190810160405280600081526020015061236e610f6d565b6118b760005481565b6118c95b600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea34638e46afa96040518160e060020a02815260040180905060206040518083038160008760325a03f2156100025750506040515191506107599050565b60408051602060248035600481810135601f8101859004850286018501909652858552611882958135959194604494929390920191819084018382808284375094965050933593505060643591505060843560a43560c43560e43561010435600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea346350d4e411600160005033338e8e8d8f8e8e8e8e8e346040518e60e060020a028152600401808e81526020018d600160a060020a031681526020018c600160a060020a031681526020018b8152602001806020018a60ff1681526020018961ffff16815260200188815260200187815260200186815260200185815260200184815260200183815260200182810382528b8181518152602001915080519060200190808383829060006004602084601f0104600f02600301f150905090810190601f1680156111195780820380516001836020036101000a031916815260200191505b509e50505050505050505050505050505060206040518083038160008760325a03f215610002575050604051519b9a5050505050505050505050565b61189f5b600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea3463971c803f6040518160e060020a02815260040180905060206040518083038160008760325a03f2156100025750506040515191506107599050565b604080516020604435600481810135601f8101849004840285018401909552848452611882948135946024803595939460649492939101918190840183828082843750949650509335935050608435915050600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea346350d4e4116001338989896123a2610f6d565b6118b75b600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea346398c9cdf46040518160e060020a02815260040180905060206040518083038160008760325a03f2156100025750506040515191506107599050565b6118b7600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea346398e00e546040518160e060020a02815260040180905060206040518083038160008760325a03f2156100025750506040515191506107599050565b611882600435604080517fe6ce3a6a000000000000000000000000000000000000000000000000000000008152600160048201527f3e3d0000000000000000000000000000000000000000000000000000000000006024820152604481018390529051600091737c1eb207c07e7ab13cf245585bd03d0fa478d0349163e6ce3a6a916064818101926020929091908290030181878760325a03f215610002575050604051519150611b409050565b611882600435602435600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea346350d4e41160016000503385600060e060020a0260206040519081016040528060008152602001506121ef610f6d565b604080516020604435600481810135601f8101849004840285018401909552848452611882948135946024803595939460649492939101918190840183828082843750949650505050505050600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea346350d4e4116001338787876120b5610f6d565b6118b7600435600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea3463ea27a88183611b4561159f565b6118b75b600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea3463b152f19e6040518160e060020a02815260040180905060206040518083038160008760325a03f2156100025750506040515191506107599050565b60408051602060248035600481810135601f8101859004850286018501909652858552611882958135959194604494929390920191819084018382808284375094965050933593505060643591505060843560a435600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea346350d4e411600133808b8b8961262d6106c6565b611882600435602435600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea346350d4e41160016000503386600060e060020a026020604051908101604052806000815260200150612200610f6d565b6118b75b60005460649004610759565b6118b7600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea3463c0f688596040518160e060020a02815260040180905060206040518083038160008760325a03f2156100025750506040515191506107599050565b611882600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea346350d4e41160016000503333600060e060020a026020604051908101604052806000815260200150611bff610f6d565b611882600435602435600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea346350d4e41160016000503333876020604051908101604052806000815260200150612200610f6d565b611882600435602435604435600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea346350d4e41160016000503387600060e060020a026020604051908101604052806000815260200150612213610f6d565b611882600435602435604435606435608435600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea346350d4e411600160005033338a60206040519081016040528060008152602001508961250c6106c6565b61027c6000600060006118e033610b56565b6118b7600435602435604435606435600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea3463ea27a881868686866040518560e060020a0281526004018085815260200184815260200183815260200182815260200194505050505060206040518083038160008760325a03f215610002575050604051519150505b949350505050565b604080516020604435600481810135601f810184900484028501840190955284845261188294813594602480359593946064949293910191819084018382808284375094965050933593505060843591505060a435600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea346350d4e4116001338a8a8a886124fa6106c6565b6118b7600435602435600073e54d323f9ef17c1f0dede47ecc86a9718fe5ea3463ea27a88184846000611b4f61122c565b60408051600160a060020a03929092168252519081900360200190f35b6040805161ffff929092168252519081900360200190f35b60408051918252519081900360200190f35b6040805160ff929092168252519081900360200190f35b15611a905733925082600160a060020a031663c6502da86040518160e060020a0281526004018090506020604051808303816000876161da5a03f1156100025750506040805180517fc6803622000000000000000000000000000000000000000000000000000000008252915191945063c680362291600482810192602092919082900301816000876161da5a03f11561000257505060405151905080156119d1575082600160a060020a031663d379be236040518160e060020a0281526004018090506020604051808303816000876161da5a03f11561000257505060405151600160a060020a03166000141590505b80156119dd5750600082115b80156119ec5750600054600190115b15611a90578183600160a060020a031663830953ab6040518160e060020a0281526004018090506020604051808303816000876161da5a03f1156100025750506040515160640291909104915050604281118015611a4d5750600054829011155b15611a675760008054612710612711909102049055611a90565b602181108015611a7a5750600054829010155b15611a90576000805461271061270f9091020490555b505050565b6000611a9f61122c565b6040518560e060020a0281526004018085815260200184815260200183815260200182815260200194505050505060206040518083038160008760325a03f2156100025750506040515191506107599050565b6040518560e060020a0281526004018085815260200184815260200183815260200182815260200194505050505060206040518083038160008760325a03f215610002575050604051519150505b919050565b6000611af261122c565b6040518560e060020a0281526004018085815260200184815260200183815260200182815260200194505050505060206040518083038160008760325a03f215610002575050604051519150505b92915050565b6040518560e060020a0281526004018085815260200184815260200183815260200182815260200194505050505060206040518083038160008760325a03f215610002575050604051519150505b9392505050565b9050610759565b611c076106c6565b6000611c11611478565b611c1961122c565b600054611c2461159f565b346040518e60e060020a028152600401808e81526020018d600160a060020a031681526020018c600160a060020a031681526020018b8152602001806020018a60ff1681526020018961ffff16815260200188815260200187815260200186815260200185815260200184815260200183815260200182810382528b8181518152602001915080519060200190808383829060006004602084601f0104600f02600301f150905090810190601f168015611cf25780820380516001836020036101000a031916815260200191505b509e50505050505050505050505050505060206040518083038160008760325a03f2156100025750506040515191506107599050565b611d306106c6565b60008b611d3b61122c565b600054611d4661159f565b346040518e60e060020a028152600401808e81526020018d600160a060020a031681526020018c600160a060020a031681526020018b8152602001806020018a60ff1681526020018961ffff16815260200188815260200187815260200186815260200185815260200184815260200183815260200182810382528b8181518152602001915080519060200190808383829060006004602084601f0104600f02600301f150905090810190601f168015611e145780820380516001836020036101000a031916815260200191505b509e50505050505050505050505050505060206040518083038160008760325a03f215610002575050604051519150611b409050565b611e526106c6565b6000611e5c611478565b611d3b61122c565b611e6c6106c6565b6000611e76611478565b611e7e61122c565b600054611e8961159f565b346040518e60e060020a028152600401808e81526020018d600160a060020a031681526020018c600160a060020a031681526020018b8152602001806020018a60ff1681526020018961ffff16815260200188815260200187815260200186815260200185815260200184815260200183815260200182810382528b8181518152602001915080519060200190808383829060006004602084601f0104600f02600301f150905090810190601f168015611f575780820380516001836020036101000a031916815260200191505b509e50505050505050505050505050505060206040518083038160008760325a03f215610002575050604051519150611b9d9050565b611f956106c6565b8b611f9e611478565b611fa661122c565b600054611fb161159f565b346040518e60e060020a028152600401808e81526020018d600160a060020a031681526020018c600160a060020a031681526020018b8152602001806020018a60ff1681526020018961ffff16815260200188815260200187815260200186815260200185815260200184815260200183815260200182810382528b8181518152602001915080519060200190808383829060006004602084601f0104600f02600301f150905090810190601f16801561207f5780820380516001836020036101000a031916815260200191505b509e50505050505050505050505050505060206040518083038160008760325a03f215610002575050604051519150611bf19050565b6120bd6106c6565b6000611f9e611478565b6120cf6106c6565b8b6120d8611478565b6120e061122c565b6000546120eb61159f565b346040518e60e060020a028152600401808e81526020018d600160a060020a031681526020018c600160a060020a031681526020018b8152602001806020018a60ff1681526020018961ffff16815260200188815260200187815260200186815260200185815260200184815260200183815260200182810382528b8181518152602001915080519060200190808383829060006004602084601f0104600f02600301f150905090810190601f1680156121b95780820380516001836020036101000a031916815260200191505b509e50505050505050505050505050505060206040518083038160008760325a03f2156100025750506040515191506117c99050565b6121f76106c6565b8b611e76611478565b6122086106c6565b60008b611e7e61122c565b61221b6106c6565b8a8c611fa661122c565b61222d6106c6565b60008b611fa661122c565b6122406106c6565b60008b6120e061122c565b6122536106c6565b8c8b61225d61122c565b60005461226861159f565b346040518e60e060020a028152600401808e81526020018d600160a060020a031681526020018c600160a060020a031681526020018b8152602001806020018a60ff1681526020018961ffff16815260200188815260200187815260200186815260200185815260200184815260200183815260200182810382528b8181518152602001915080519060200190808383829060006004602084601f0104600f02600301f150905090810190601f1680156123365780820380516001836020036101000a031916815260200191505b509e50505050505050505050505050505060206040518083038160008760325a03f21561000257505060405151979650505050505050565b6123766106c6565b60008c8c600060005054611fb161159f565b6123906106c6565b60008c8c6000600050546120eb61159f565b6123aa6106c6565b60008c8c60006000505461226861159f565b60008d8d6000600050546120eb61159f565b346040518e60e060020a028152600401808e81526020018d600160a060020a031681526020018c600160a060020a031681526020018b8152602001806020018a60ff1681526020018961ffff16815260200188815260200187815260200186815260200185815260200184815260200183815260200182810382528b8181518152602001915080519060200190808383829060006004602084601f0104600f02600301f150905090810190601f16801561249c5780820380516001836020036101000a031916815260200191505b509e50505050505050505050505050505060206040518083038160008760325a03f215610002575050604051519150505b9695505050505050565b8e8d8d6000600050546123ce61159f565b60008d8d60006000505461226861159f565b60008d8d6000600050546123ce61159f565b60008e8e8d61226861159f565b8f8e8e8d61252561159f565b346040518e60e060020a028152600401808e81526020018d600160a060020a031681526020018c600160a060020a031681526020018b8152602001806020018a60ff1681526020018961ffff16815260200188815260200187815260200186815260200185815260200184815260200183815260200182810382528b8181518152602001915080519060200190808383829060006004602084601f0104600f02600301f150905090810190601f1680156125f35780820380516001836020036101000a031916815260200191505b509e50505050505050505050505050505060206040518083038160008760325a03f215610002575050604051519998505050505050505050565b60008e8e8d6123ce61159f565b8a5160208c015160408d015160608e015161226861159f565b60008e8e8d61252561159f56"
    insts = disassemble_for_time_lock(bytecode)
    for inst in insts:
        print(f"{inst.opcode}"+(f" {inst.argument}" if inst.argument else ""))
