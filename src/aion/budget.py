"""Explicit bounds on logical external commands in a research invocation."""
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import replace
import time

from .errors import AionError
from .models import Limits

ACTIVE = ContextVar("aion_research_budget", default=None)


class ResearchBudget:
    def __init__(self, commands: int, seconds: float):
        if type(commands) is not int or not 1 <= commands <= 10000 or not 1 <= seconds <= 7200:
            raise AionError("Research budget requires 1..10000 commands and 1..7200 seconds.")
        self.maximum_commands, self.maximum_seconds = commands, seconds
        self.started = time.monotonic()
        self.attempts = []
        self.parent = None

    def charge(self, command, limits):
        remaining = self.maximum_seconds - (time.monotonic() - self.started)
        if len(self.attempts) >= self.maximum_commands or remaining <= 0:
            raise AionError("Research computational budget exhausted; retained attempts must not be discarded.")
        if self.parent is not None:
            item, limits = self.parent.charge(command, limits)
        else:
            item = {"command": list(map(str, command)), "status": "started"}
        self.attempts.append(item)
        return item, replace(limits or Limits(), timeout_seconds=min((limits or Limits()).timeout_seconds, remaining))

    def record(self):
        return {"maximum_commands": self.maximum_commands, "maximum_seconds": self.maximum_seconds,
                "elapsed_seconds": time.monotonic()-self.started, "commands_used": len(self.attempts),
                "accounting": "logical run_process calls, including probes/builds/training/checks/pilots/warmups/samples; not OS child PIDs",
                "attempts": self.attempts}


@contextmanager
def bounded(budget):
    previous_parent = budget.parent
    budget.parent = ACTIVE.get()
    if budget.parent is budget:
        budget.parent = previous_parent
        raise AionError("A research budget cannot contain itself.")
    token = ACTIVE.set(budget)
    try:
        yield budget
    finally:
        ACTIVE.reset(token)
        budget.parent = previous_parent
