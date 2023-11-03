from code_analyzer.disasm import disassemble_for_time_lock
from mythril.ethereum.evmcontract import EVMContract
from mythril.support.support_args import args

from mythril.analysis.security import fire_lasers
from mythril.analysis.symbolic import SymExecWrapper
from mythril.laser.smt import SolverStatistics
from mythril.support.loader import DynLoader
from mythril.support.start_time import StartTime

LARGE_TIME = 300


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
    code = bytecode[2:] if bytecode.startswith("0x") else bytecode
    contract = EVMContract(
        creation_code=code,
        name="MAIN",
        enable_online_lookup=False,
    )
    strategy = 'bfs'
    execution_timeout = 86400

    # check support args for optimal settings
    args.pruning_factor = 1 if execution_timeout > LARGE_TIME else 0
    args.solver_timeout = 25000
    args.call_depth_limit = 2

    SolverStatistics().enabled = True
    StartTime()
    sym = SymExecWrapper(
        contract=contract,
        address=None,
        strategy=strategy,
        dynloader=DynLoader(None, active=False),
        max_depth=128,
        execution_timeout=86400,
        loop_bound=3,
        create_timeout=30,
        transaction_count=2,
        modules=['PredictableVariables'],
        compulsory_statespace=False,
        disable_dependency_pruning=False,
        custom_modules_directory="",
    )
    # check if there are any predictable variables todo: check only for time locks
    issues = fire_lasers(sym, ['PredictableVariables'])

    return len(issues) > 0
