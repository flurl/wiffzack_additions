import logging
from typing import Any

from .db_connection import DatabaseConnection
from .db_repository import DatabaseRepository

logger = logging.getLogger(__name__)


# For backward compatibility and ease of transition, we can provide a factory function
# or a class that mimics the old `Database` class behavior.
class Database:
    """
    A facade that combines DatabaseConnection and DatabaseRepository for backward compatibility.
    It is deprecated and will be removed in the future.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        logger.warning(
            "The 'Database' class is deprecated. Please use 'DatabaseRepository' and 'DatabaseConnection' instead.")
        # Internally, it holds both the connection and the repository
        self._connection = DatabaseConnection()
        self._repository = DatabaseRepository(self._connection)

    def __getattr__(self, name: str) -> Any:
        """
        Delegates attribute access to the repository or the connection.
        This allows calls like `db.get_article()` and `db.connect_to_database()` to work seamlessly.
        """
        # Prioritize repository methods, then connection methods.
        if hasattr(self._repository, name):
            return getattr(self._repository, name)
        if hasattr(self._connection, name):
            return getattr(self._connection, name)
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'")

    @property
    def connection(self) -> DatabaseConnection:
        return self._connection

    @property
    def repository(self) -> DatabaseRepository:
        return self._repository
