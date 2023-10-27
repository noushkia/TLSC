import logging

log = logging.getLogger(__name__)

time_lock_ops = ["TIMESTAMP", "NUMBER"]


class TimeLockValueAnnotation:
    """Annotation used if a variable is initialized from a predictable environment variable."""

    def __init__(self, operation: str) -> None:
        self.operation = operation


class TimeLock:
    """
    TODO
        Implement
        This module detects whether control flow decisions are made using time-locks.
    """

    pre_hooks = ["JUMPI", "BLOCKHASH"]
    post_hooks = ["BLOCKHASH"] + time_lock_ops

    def check_for_time_lock(self, state) -> bool:
        """

        :param state:
        :return:
        """

        if is_prehook():
            opcode = state.get_current_instruction()["opcode"]
            if opcode == "JUMPI":
                # Look for time-locks in jump condition
                for annotation in state.mstate.stack[-2].annotations:
                    if isinstance(annotation, TimeLockValueAnnotation):
                        return True
        else:
            # In post-hook
            opcode = state.environment.code.instruction_list[state.mstate.pc - 1]["opcode"]
            # Create an annotation when TIMESTAMP or NUMBER is executed.
            state.mstate.stack[-1].annotate(
                TimeLockValueAnnotation(opcode)
            )

        return False
