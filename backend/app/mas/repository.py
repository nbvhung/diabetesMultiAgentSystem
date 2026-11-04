"""Explicit app-owned storage. Returned models never alias stored runs."""
from collections import OrderedDict
from threading import RLock
from typing import Protocol
from uuid import UUID
from backend.app.schemas.runtime import WorkflowResponse

class RunRepository(Protocol):
    def save(self, run: WorkflowResponse) -> None: ...
    def get(self, run_id: UUID) -> WorkflowResponse | None: ...

class InMemoryRunRepository:
    def __init__(self, max_runs: int = 100):
        if max_runs < 1:
            raise ValueError("max_runs must be positive")
        self._max_runs = max_runs
        self._runs: OrderedDict[UUID, WorkflowResponse] = OrderedDict()
        self._lock = RLock()

    def save(self, run: WorkflowResponse) -> None:
        with self._lock:
            self._runs[run.run_id] = run.model_copy(deep=True)
            while len(self._runs) > self._max_runs:
                self._runs.popitem(last=False)

    def get(self, run_id: UUID) -> WorkflowResponse | None:
        with self._lock:
            run = self._runs.get(run_id)
            return run.model_copy(deep=True) if run else None
