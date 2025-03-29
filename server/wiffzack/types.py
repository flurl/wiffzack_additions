import queue
from typing import Any, LiteralString, NamedTuple, TypeAlias

DBResult: TypeAlias = list[tuple[Any, ...]] | None

class Article(NamedTuple):
    id: int
    name: str

class StorageModifier(NamedTuple):
    article: Article
    storage_id: int
    amount: int

class ResultQueueItem(NamedTuple):
    result: list[tuple[Any, ...]] | None

class QueryQueueItem(NamedTuple):
    query: LiteralString
    params: tuple[Any, ...]
    result_queue: queue.Queue[ResultQueueItem]