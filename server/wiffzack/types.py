from typing import Any, NamedTuple, TypeAlias

DBResult: TypeAlias = list[tuple[Any, ...]] | None


class Article(NamedTuple):
    id: int
    name: str


class StorageModifier(NamedTuple):
    article: Article
    storage_id: int
    amount: int
