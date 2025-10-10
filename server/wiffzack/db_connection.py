from collections.abc import Iterable
import logging
from typing import Any, LiteralString
import pymssql

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Handles the low-level connection and transaction management with the database."""

    def __init__(self) -> None:
        self.connection: pymssql.Connection | None = None
        self.cursor: pymssql.Cursor | None = None

    def connect_to_database(self, server: str, username: str, password: str, database: str) -> None:
        self.connection = pymssql.connect(server=server, user=username,
                                          password=password, database=database, tds_version=r"7.0")
        if not self.connection:
            raise ConnectionError(
                f"Failed to connect to database {database} on {server}")
        self.cursor = self.connection.cursor()
        if not self.cursor:
            raise ConnectionError(
                "Failed to create a cursor for the database connection.")

    def close(self) -> None:
        """Closes the database connection and cursor."""
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.connection:
            self.connection.close()
            self.connection = None

    def execute_query(self, query: LiteralString, params: Iterable[Any] = ()) -> list[tuple[Any, ...]] | None:
        """Executes a SQL query and returns the result."""
        if self.cursor is None:
            raise ConnectionError(
                "Database cursor is not initialized. Call connect_to_database first.")
        try:
            self.cursor.execute(query, params)
            try:
                return self.cursor.fetchall()
            # Handles cases where statement has no resultset (e.g. INSERT, UPDATE)
            except pymssql.OperationalError:
                return None
            except Exception:
                logger.error(
                    f"Error fetching results for query: {query} with params: {params}.", exc_info=True)
                raise
        except Exception:
            logger.error(
                f"Error executing query: {query} with params: {params}.", exc_info=True)
            raise

    def commit(self) -> None:
        assert self.connection is not None, "Connection is not initialized."
        self.connection.commit()

    def rollback(self) -> None:
        assert self.connection is not None, "Connection is not initialized."
        self.connection.rollback()
