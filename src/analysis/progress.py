import json
from dataclasses import dataclass, field
from queue import Queue
from typing import Any, Callable


def progress_event(
    message: str,
    *,
    stage: str | None = None,
    source: str | None = None,
    current: int | None = None,
    total: int | None = None,
    title: str | None = None,
) -> dict[str, Any]:
    event: dict[str, Any] = {"type": "progress", "message": message}
    if stage is not None:
        event["stage"] = stage
    if source is not None:
        event["source"] = source
    if current is not None:
        event["current"] = current
    if total is not None:
        event["total"] = total
    if title is not None:
        event["title"] = title
    return event


def error_event(message: str) -> dict[str, Any]:
    return {"type": "error", "message": message}


def done_event(redirect: str) -> dict[str, Any]:
    return {"type": "done", "redirect": redirect}


def format_ndjson_line(event: dict[str, Any]) -> str:
    return json.dumps(event, ensure_ascii=False) + "\n"


@dataclass
class ProgressReporter:
    """Emits structured progress events; no-op when sink is None."""

    _sink: Callable[[dict[str, Any]], None] | None = field(default=None, repr=False)

    def emit(
        self,
        message: str,
        *,
        stage: str | None = None,
        source: str | None = None,
        current: int | None = None,
        total: int | None = None,
        title: str | None = None,
    ) -> dict[str, Any]:
        event = progress_event(
            message,
            stage=stage,
            source=source,
            current=current,
            total=total,
            title=title,
        )
        if self._sink is not None:
            self._sink(event)
        return event


def null_reporter() -> ProgressReporter:
    return ProgressReporter()


class QueueProgressReporter(ProgressReporter):
    """For streaming: each emit enqueues an NDJSON line."""

    def __init__(self, queue: Queue[str | None]) -> None:
        super().__init__()
        self._queue = queue
        self._sink = lambda event: queue.put(format_ndjson_line(event))
