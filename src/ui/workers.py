"""Thread-pool plumbing for long-running save operations.

Widgets may only be touched from the GUI thread, so a worker communicates
exclusively by signal. WorkerSignals is constructed on the GUI thread, which
gives it GUI-thread affinity and makes every emit from the pool thread a queued
(thread-safe) delivery.
"""
from typing import Any, Callable

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from src.core.operations import OperationCancelled


class WorkerSignals(QObject):
    progress = Signal(int, int)     # (done, total)
    finished = Signal()
    cancelled = Signal()
    failed = Signal(str)


class Worker(QRunnable):
    """Runs `fn` on a thread pool, feeding it progress and cancellation hooks."""

    def __init__(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self.signals = WorkerSignals()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def is_cancelled(self) -> bool:
        return self._cancelled

    @Slot()
    def run(self) -> None:
        try:
            self._fn(
                *self._args,
                progress=self.signals.progress.emit,
                is_cancelled=self.is_cancelled,
                **self._kwargs,
            )
        except OperationCancelled:
            self.signals.cancelled.emit()
        except Exception as exc:  # noqa: BLE001 - surfaced to the user verbatim
            self.signals.failed.emit(str(exc))
        else:
            self.signals.finished.emit()
