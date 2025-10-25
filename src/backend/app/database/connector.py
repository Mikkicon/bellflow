from typing import Optional, Dict, Any
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging
from contextlib import asynccontextmanager
from .config import db_settings, get_database_url, get_database_name

# Configure logging
logger = logging.getLogger(__name__)


class DatabaseConnector:
    """MongoDB database connector with connection pooling and error handling."""

    def __init__(self):
        self._client: Optional[MongoClient] = None
        self._database: Optional[Database] = None
        self._is_connected = False

    def connect(self) -> bool:
        """
        Establish connection to MongoDB.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Get connection URL and database name
            connection_url = get_database_url()
            database_name = get_database_name()

            logger.info(f"Connecting to MongoDB at: {connection_url}")
            logger.info(f"Using database: {database_name}")

            # Create MongoDB client with connection pooling
            self._client = MongoClient(
                connection_url,
                maxPoolSize=db_settings.max_pool_size,
                minPoolSize=db_settings.min_pool_size,
                maxIdleTimeMS=db_settings.max_idle_time_ms,
                connectTimeoutMS=db_settings.connect_timeout_ms,
                serverSelectionTimeoutMS=db_settings.server_selection_timeout_ms,
                retryWrites=True,
                retryReads=True
            )

            # Test the connection
            self._client.admin.command('ping')

            # Get database instance
            self._database = self._client[database_name]
            self._is_connected = True

            logger.info("Successfully connected to MongoDB")
            return True

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self._is_connected = False
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            self._is_connected = False
            return False

    def disconnect(self) -> None:
        """Close the database connection."""
        if self._client:
            self._client.close()
            self._is_connected = False
            logger.info("Disconnected from MongoDB")

    def get_database(self) -> Optional[Database]:
        """
        Get the database instance.

        Returns:
            Database: MongoDB database instance or None if not connected
        """
        if not self._is_connected or self._database is None:
            logger.warning("Database not connected. Call connect() first.")
            return None
        return self._database

    def get_collection(self, collection_name: str) -> Optional[Collection]:
        """
        Get a collection from the database.

        Args:
            collection_name (str): Name of the collection

        Returns:
            Collection: MongoDB collection instance or None if not connected
        """
        database = self.get_database()
        if database is None:
            return None
        return database[collection_name]

    def is_connected(self) -> bool:
        """
        Check if the database is connected.

        Returns:
            bool: True if connected, False otherwise
        """
        return self._is_connected

    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the database connection.

        Returns:
            Dict[str, Any]: Health check results
        """
        if not self._is_connected or not self._client:
            return {
                "status": "disconnected",
                "message": "Database not connected",
                "connected": False
            }

        try:
            # Ping the database
            result = self._client.admin.command('ping')
            return {
                "status": "healthy",
                "message": "Database connection is healthy",
                "connected": True,
                "ping_result": result
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Database health check failed: {e}",
                "connected": False
            }

    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get information about the current connection.

        Returns:
            Dict[str, Any]: Connection information
        """
        if not self._is_connected or not self._client:
            return {
                "connected": False,
                "message": "Not connected to database"
            }

        try:
            server_info = self._client.server_info()
            return {
                "connected": True,
                "database_name": get_database_name(),
                "server_version": server_info.get("version"),
                "server_type": server_info.get("gitVersion", "Unknown"),
                "max_pool_size": db_settings.max_pool_size,
                "min_pool_size": db_settings.min_pool_size
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e)
            }


# Global database connector instance
_db_connector = DatabaseConnector()


def get_database() -> Optional[Database]:
    """
    Get the database instance from the global connector.

    Returns:
        Database: MongoDB database instance or None if not connected
    """
    return _db_connector.get_database()


def get_collection(collection_name: str) -> Optional[Collection]:
    """
    Get a collection from the global database connector.

    Args:
        collection_name (str): Name of the collection

    Returns:
        Collection: MongoDB collection instance or None if not connected
    """
    return _db_connector.get_collection(collection_name)


def connect_database() -> bool:
    """
    Connect to the database using the global connector.

    Returns:
        bool: True if connection successful, False otherwise
    """
    return _db_connector.connect()


def disconnect_database() -> None:
    """Disconnect from the database using the global connector."""
    _db_connector.disconnect()


def is_database_connected() -> bool:
    """
    Check if the database is connected.

    Returns:
        bool: True if connected, False otherwise
    """
    return _db_connector.is_connected()


def get_database_health() -> Dict[str, Any]:
    """
    Get database health status.

    Returns:
        Dict[str, Any]: Health check results
    """
    return _db_connector.health_check()


def get_database_info() -> Dict[str, Any]:
    """
    Get database connection information.

    Returns:
        Dict[str, Any]: Connection information
    """
    return _db_connector.get_connection_info()
