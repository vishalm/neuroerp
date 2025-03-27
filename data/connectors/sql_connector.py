"""
SQL Connector for NeuroERP.

This module provides a flexible SQL connector that enables seamless integration
with various database systems including MySQL, PostgreSQL, SQLite, and SQL Server.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Union, Tuple
import contextlib
import threading
from datetime import datetime

# Database libraries
import sqlite3
try:
    import psycopg2
    import psycopg2.extras
    HAVE_POSTGRES = True
except ImportError:
    HAVE_POSTGRES = False

try:
    import pymysql
    HAVE_MYSQL = True
except ImportError:
    HAVE_MYSQL = False

try:
    import pyodbc
    HAVE_SQLSERVER = True
except ImportError:
    HAVE_SQLSERVER = False

from ...core.config import Config

logger = logging.getLogger(__name__)

class SQLConnector:
    """Connector for interacting with SQL databases."""
    
    def __init__(self, db_name: str, config: Optional[Dict[str, Any]] = None):
        """Initialize the SQL connector.
        
        Args:
            db_name: Name of the database connection (used to load config)
            config: Optional manual configuration (overrides config file)
        """
        self.db_name = db_name
        self.config = Config()
        
        # Load configuration
        self._load_configuration(config)
        
        # Connection pool
        self._connections = {}
        self._pool_lock = threading.RLock()
        
        # Query metrics
        self.query_count = 0
        self.error_count = 0
        self.last_query_time = None
        
        logger.info(f"Initialized SQL connector for {db_name}")
    
    def _load_configuration(self, manual_config: Optional[Dict[str, Any]]):
        """Load database configuration from config or manual override.
        
        Args:
            manual_config: Optional manual configuration to override config file
        """
        # Set default configuration
        self.db_config = {
            "type": "sqlite",  # sqlite, mysql, postgres, sqlserver
            "host": "localhost",
            "port": None,
            "database": "",
            "username": "",
            "password": "",
            "pool_size": 5,
            "connection_timeout": 30,
            "query_timeout": 60,
            "ssl_mode": None,
            "options": {}
        }
        
        # Set default port based on database type
        db_default_ports = {
            "mysql": 3306,
            "postgres": 5432,
            "sqlserver": 1433
        }
        
        # Load from config file if available
        config_path = f"connectors.sql.{self.db_name}"
        file_config = self.config.get(config_path, {})
        
        if file_config:
            self.db_config.update(file_config)
            logger.debug(f"Loaded configuration for database {self.db_name} from config file")
        
        # Override with manual config if provided
        if manual_config:
            self.db_config.update(manual_config)
            logger.debug(f"Applied manual configuration for database {self.db_name}")
        
        # Set default port if not specified
        if self.db_config["port"] is None:
            db_type = self.db_config["type"]
            if db_type in db_default_ports:
                self.db_config["port"] = db_default_ports[db_type]
        
        # Validate configuration
        self._validate_configuration()
    
    def _validate_configuration(self):
        """Validate database configuration."""
        db_type = self.db_config["type"]
        
        if db_type not in ["sqlite", "mysql", "postgres", "sqlserver"]:
            logger.warning(f"Unsupported database type: {db_type}")
            return False
        
        if db_type == "sqlite":
            # SQLite only requires a database file path
            if not self.db_config["database"]:
                logger.warning("No database file specified for SQLite")
                return False
        else:
            # Other databases require host, database, username, password
            required_fields = ["host", "database", "username", "password"]
            for field in required_fields:
                if not self.db_config.get(field):
                    logger.warning(f"Missing required field for {db_type}: {field}")
                    return False
        
        # Check for required libraries
        if db_type == "postgres" and not HAVE_POSTGRES:
            logger.warning("PostgreSQL support requires psycopg2 package")
            return False
        elif db_type == "mysql" and not HAVE_MYSQL:
            logger.warning("MySQL support requires pymysql package")
            return False
        elif db_type == "sqlserver" and not HAVE_SQLSERVER:
            logger.warning("SQL Server support requires pyodbc package")
            return False
        
        return True
    
    def _get_connection(self, thread_id: Optional[int] = None) -> Any:
        """Get a database connection from the pool.
        
        Args:
            thread_id: Optional thread ID for connection tracking
            
        Returns:
            Database connection
        """
        if thread_id is None:
            thread_id = threading.get_ident()
        
        with self._pool_lock:
            # Check if connection exists for this thread
            if thread_id in self._connections:
                conn = self._connections[thread_id]
                # Test if connection is still valid
                try:
                    self._test_connection(conn)
                    return conn
                except Exception:
                    # Connection is invalid, remove it and create a new one
                    logger.debug(f"Connection for thread {thread_id} is invalid, creating a new one")
                    self._close_connection(conn)
                    del self._connections[thread_id]
            
            # Create a new connection
            try:
                conn = self._create_connection()
                self._connections[thread_id] = conn
                return conn
            except Exception as e:
                logger.error(f"Failed to create database connection: {e}")
                raise
    
    def _create_connection(self) -> Any:
        """Create a new database connection.
        
        Returns:
            Database connection
        """
        db_type = self.db_config["type"]
        
        try:
            if db_type == "sqlite":
                conn = sqlite3.connect(
                    self.db_config["database"],
                    timeout=self.db_config["connection_timeout"]
                )
                # Enable foreign keys
                conn.execute("PRAGMA foreign_keys = ON")
                # Row factory for dictionary-like results
                conn.row_factory = sqlite3.Row
                
            elif db_type == "postgres":
                if not HAVE_POSTGRES:
                    raise ImportError("PostgreSQL support requires psycopg2 package")
                
                conn = psycopg2.connect(
                    host=self.db_config["host"],
                    port=self.db_config["port"],
                    database=self.db_config["database"],
                    user=self.db_config["username"],
                    password=self.db_config["password"],
                    connect_timeout=self.db_config["connection_timeout"],
                    sslmode=self.db_config["ssl_mode"],
                    **self.db_config["options"]
                )
                # Use dictionary cursor by default
                conn.cursor_factory = psycopg2.extras.DictCursor
                
            elif db_type == "mysql":
                if not HAVE_MYSQL:
                    raise ImportError("MySQL support requires pymysql package")
                
                conn = pymysql.connect(
                    host=self.db_config["host"],
                    port=self.db_config["port"],
                    database=self.db_config["database"],
                    user=self.db_config["username"],
                    password=self.db_config["password"],
                    connect_timeout=self.db_config["connection_timeout"],
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor,
                    **self.db_config["options"]
                )
                
            elif db_type == "sqlserver":
                if not HAVE_SQLSERVER:
                    raise ImportError("SQL Server support requires pyodbc package")
                
                # Build connection string
                conn_str = (
                    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                    f"SERVER={self.db_config['host']},{self.db_config['port']};"
                    f"DATABASE={self.db_config['database']};"
                    f"UID={self.db_config['username']};"
                    f"PWD={self.db_config['password']};"
                    f"Timeout={self.db_config['connection_timeout']};"
                )
                
                # Add additional options
                for key, value in self.db_config["options"].items():
                    conn_str += f"{key}={value};"
                
                conn = pyodbc.connect(conn_str)
                
            else:
                raise ValueError(f"Unsupported database type: {db_type}")
            
            logger.debug(f"Created new connection to {db_type} database")
            return conn
            
        except Exception as e:
            logger.error(f"Failed to connect to {db_type} database: {e}")
            raise
    
    def _test_connection(self, conn: Any) -> bool:
        """Test if a connection is still valid.
        
        Args:
            conn: Database connection to test
            
        Returns:
            True if connection is valid, False otherwise
        """
        db_type = self.db_config["type"]
        
        try:
            cursor = None
            if db_type == "sqlite":
                cursor = conn.execute("SELECT 1")
            elif db_type == "postgres":
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
            elif db_type == "mysql":
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
            elif db_type == "sqlserver":
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
            
            if cursor:
                cursor.fetchone()
                if db_type != "sqlite":  # SQLite cursor doesn't need to be closed
                    cursor.close()
            
            return True
        except Exception as e:
            logger.debug(f"Connection test failed: {e}")
            return False
    
    def _close_connection(self, conn: Any):
        """Close a database connection.
        
        Args:
            conn: Database connection to close
        """
        try:
            conn.close()
            logger.debug("Closed database connection")
        except Exception as e:
            logger.warning(f"Error closing database connection: {e}")
    
    def close(self):
        """Close all database connections in the pool."""
        with self._pool_lock:
            for thread_id, conn in list(self._connections.items()):
                self._close_connection(conn)
                del self._connections[thread_id]
        
        logger.debug(f"Closed all connections for {self.db_name}")
    
    @contextlib.contextmanager
    def connection(self) -> Any:
        """Get a database connection as a context manager.
        
        Yields:
            Database connection
        """
        conn = self._get_connection()
        try:
            yield conn
        finally:
            # SQLite connections are returned to the pool, not closed
            pass
    
    @contextlib.contextmanager
    def transaction(self) -> Any:
        """Start a database transaction as a context manager.
        
        Yields:
            Database connection with active transaction
        """
        conn = self._get_connection()
        try:
            if self.db_config["type"] == "postgres":
                # In PostgreSQL, transactions are managed with begin/commit/rollback
                conn.begin()
            else:
                # Other databases use autocommit mode and explicit transactions
                conn.rollback()  # Ensure no pending transaction
            
            yield conn
            
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    
    def execute(self, 
              query: str, 
              params: Optional[Union[Dict[str, Any], List[Any], Tuple[Any, ...]]] = None,
              fetch: bool = False,
              fetch_one: bool = False,
              as_dict: bool = True) -> Union[List[Dict[str, Any]], Dict[str, Any], None]:
        """Execute a SQL query.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            fetch: Whether to fetch results
            fetch_one: Whether to fetch only one result
            as_dict: Whether to return results as dictionaries
            
        Returns:
            Query results if fetch is True, otherwise None
        """
        start_time = time.time()
        self.query_count += 1
        self.last_query_time = start_time
        
        try:
            with self.connection() as conn:
                cursor = None
                db_type = self.db_config["type"]
                
                try:
                    if db_type == "sqlite":
                        cursor = conn.execute(query, params or [])
                    else:
                        cursor = conn.cursor()
                        cursor.execute(query, params or [])
                    
                    if fetch:
                        if fetch_one:
                            row = cursor.fetchone()
                            if as_dict and row is not None:
                                if db_type == "sqlite":
                                    return dict(row)
                                elif db_type == "sqlserver":
                                    # pyodbc doesn't have dict cursor, convert manually
                                    columns = [column[0] for column in cursor.description]
                                    return dict(zip(columns, row))
                                else:
                                    # MySQL and PostgreSQL already use dict cursor
                                    return row
                            return row
                        else:
                            rows = cursor.fetchall()
                            if as_dict:
                                if db_type == "sqlite":
                                    return [dict(row) for row in rows]
                                elif db_type == "sqlserver":
                                    # pyodbc doesn't have dict cursor, convert manually
                                    columns = [column[0] for column in cursor.description]
                                    return [dict(zip(columns, row)) for row in rows]
                                else:
                                    # MySQL and PostgreSQL already use dict cursor
                                    return rows
                            return rows
                    
                    # For INSERT/UPDATE/DELETE, return affected row count
                    if db_type == "sqlite":
                        return {"rowcount": cursor.rowcount}
                    else:
                        cursor.close()
                        return {"rowcount": cursor.rowcount}
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Query execution error: {e}")
                    logger.debug(f"Query: {query}")
                    logger.debug(f"Parameters: {params}")
                    raise
                finally:
                    if db_type != "sqlite" and cursor:
                        cursor.close()
        finally:
            elapsed = time.time() - start_time
            logger.debug(f"Query executed in {elapsed:.3f}s")
    
    def query(self, 
             query: str, 
             params: Optional[Union[Dict[str, Any], List[Any], Tuple[Any, ...]]] = None,
             as_dict: bool = True) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return all results.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            as_dict: Whether to return results as dictionaries
            
        Returns:
            Query results
        """
        return self.execute(query, params, fetch=True, fetch_one=False, as_dict=as_dict) or []
    
    def query_one(self, 
                query: str, 
                params: Optional[Union[Dict[str, Any], List[Any], Tuple[Any, ...]]] = None,
                as_dict: bool = True) -> Optional[Dict[str, Any]]:
        """Execute a SELECT query and return the first result.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            as_dict: Whether to return results as dictionaries
            
        Returns:
            First query result or None
        """
        return self.execute(query, params, fetch=True, fetch_one=True, as_dict=as_dict)
    
    def insert(self, 
              table: str, 
              data: Dict[str, Any],
              return_id: bool = False,
              id_column: str = "id") -> Union[int, Dict[str, Any]]:
        """Insert a row into a table.
        
        Args:
            table: Table name
            data: Column data to insert
            return_id: Whether to return the ID of the inserted row
            id_column: Name of the ID column
            
        Returns:
            Inserted row ID if return_id is True, otherwise rowcount
        """
        columns = list(data.keys())
        values = list(data.values())
        
        db_type = self.db_config["type"]
        
        # Build query with appropriate parameter placeholders
        if db_type == "postgres":
            placeholders = [f"%s" for _ in range(len(columns))]
            query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            
            if return_id:
                query += f" RETURNING {id_column}"
        elif db_type == "mysql":
            placeholders = [f"%s" for _ in range(len(columns))]
            query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        elif db_type == "sqlserver":
            placeholders = [f"?" for _ in range(len(columns))]
            query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            
            if return_id:
                query += f"; SELECT SCOPE_IDENTITY() AS {id_column}"
        else:  # sqlite
            placeholders = ["?" for _ in range(len(columns))]
            query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        
        # Execute the query
        if return_id:
            if db_type == "postgres":
                result = self.query_one(query, values)
                return result[id_column] if result else None
            elif db_type == "sqlserver":
                result = self.query_one(query, values)
                return result[id_column] if result else None
            else:  # sqlite, mysql
                with self.connection() as conn:
                    if db_type == "sqlite":
                        cursor = conn.execute(query, values)
                        return cursor.lastrowid
                    else:  # mysql
                        cursor = conn.cursor()
                        cursor.execute(query, values)
                        last_id = cursor.lastrowid
                        cursor.close()
                        return last_id
        else:
            result = self.execute(query, values)
            return result.get("rowcount", 0) if result else 0
    
    def update(self, 
              table: str, 
              data: Dict[str, Any],
              where: str,
              where_params: Optional[Union[Dict[str, Any], List[Any], Tuple[Any, ...]]] = None) -> int:
        """Update rows in a table.
        
        Args:
            table: Table name
            data: Column data to update
            where: WHERE clause
            where_params: Parameters for WHERE clause
            
        Returns:
            Number of affected rows
        """
        columns = list(data.keys())
        values = list(data.values())
        
        db_type = self.db_config["type"]
        
        # Build query with appropriate parameter placeholders
        if db_type == "postgres":
            set_clause = ", ".join([f"{col} = %s" for col in columns])
            query = f"UPDATE {table} SET {set_clause}"
            
            if where:
                query += f" WHERE {where}"
                
            # Combine parameters
            params = values
            if where_params:
                if isinstance(where_params, dict):
                    for param in where_params.values():
                        params.append(param)
                else:
                    params.extend(where_params)
                    
        elif db_type == "mysql":
            set_clause = ", ".join([f"{col} = %s" for col in columns])
            query = f"UPDATE {table} SET {set_clause}"
            
            if where:
                query += f" WHERE {where}"
                
            # Combine parameters
            params = values
            if where_params:
                if isinstance(where_params, dict):
                    for param in where_params.values():
                        params.append(param)
                else:
                    params.extend(where_params)
                    
        elif db_type == "sqlserver" or db_type == "sqlite":
            set_clause = ", ".join([f"{col} = ?" for col in columns])
            query = f"UPDATE {table} SET {set_clause}"
            
            if where:
                query += f" WHERE {where}"
                
            # Combine parameters
            params = values
            if where_params:
                if isinstance(where_params, dict):
                    for param in where_params.values():
                        params.append(param)
                else:
                    params.extend(where_params)
        
        # Execute the query
        result = self.execute(query, params)
        return result.get("rowcount", 0) if result else 0
    
    def delete(self, 
              table: str, 
              where: str,
              where_params: Optional[Union[Dict[str, Any], List[Any], Tuple[Any, ...]]] = None) -> int:
        """Delete rows from a table.
        
        Args:
            table: Table name
            where: WHERE clause
            where_params: Parameters for WHERE clause
            
        Returns:
            Number of affected rows
        """
        query = f"DELETE FROM {table}"
        
        if where:
            query += f" WHERE {where}"
        
        # Execute the query
        result = self.execute(query, where_params)
        return result.get("rowcount", 0) if result else 0
    
    def execute_script(self, script: str) -> None:
        """Execute a SQL script.
        
        Args:
            script: SQL script to execute
        """
        db_type = self.db_config["type"]
        
        with self.connection() as conn:
            if db_type == "sqlite":
                conn.executescript(script)
            elif db_type == "postgres":
                cursor = conn.cursor()
                cursor.execute(script)
                cursor.close()
            elif db_type == "mysql":
                cursor = conn.cursor()
                # Split script by semicolons to execute statements individually
                for statement in script.split(';'):
                    if statement.strip():
                        cursor.execute(statement)
                cursor.close()
            elif db_type == "sqlserver":
                cursor = conn.cursor()
                cursor.execute(script)
                cursor.close()
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists.
        
        Args:
            table_name: Table name to check
            
        Returns:
            True if table exists, False otherwise
        """
        db_type = self.db_config["type"]
        
        if db_type == "sqlite":
            result = self.query_one(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                [table_name]
            )
        elif db_type == "postgres":
            schema, table = "public", table_name
            if "." in table_name:
                schema, table = table_name.split(".", 1)
                
            result = self.query_one(
                "SELECT table_name FROM information_schema.tables WHERE table_schema=%s AND table_name=%s",
                [schema, table]
            )
        elif db_type == "mysql":
            result = self.query_one(
                "SELECT table_name FROM information_schema.tables WHERE table_schema=%s AND table_name=%s",
                [self.db_config["database"], table_name]
            )
        elif db_type == "sqlserver":
            result = self.query_one(
                "SELECT table_name FROM information_schema.tables WHERE table_catalog=? AND table_name=?",
                [self.db_config["database"], table_name]
            )
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
        
        return result is not None
    
    def get_tables(self) -> List[str]:
        """Get all tables in the database.
        
        Returns:
            List of table names
        """
        db_type = self.db_config["type"]
        
        if db_type == "sqlite":
            results = self.query(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            return [row["name"] for row in results]
        elif db_type == "postgres":
            results = self.query(
                "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
            )
            return [row["table_name"] for row in results]
        elif db_type == "mysql":
            results = self.query(
                "SELECT table_name FROM information_schema.tables WHERE table_schema=%s",
                [self.db_config["database"]]
            )
            return [row["table_name"] for row in results]
        elif db_type == "sqlserver":
            results = self.query(
                "SELECT table_name FROM information_schema.tables WHERE table_catalog=? AND table_type='BASE TABLE'",
                [self.db_config["database"]]
            )
            return [row["table_name"] for row in results]
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    def get_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """Get all columns in a table.
        
        Args:
            table_name: Table name
            
        Returns:
            List of column information dictionaries
        """
        db_type = self.db_config["type"]
        
        if db_type == "sqlite":
            return self.query(f"PRAGMA table_info({table_name})")
        elif db_type == "postgres":
            schema, table = "public", table_name
            if "." in table_name:
                schema, table = table_name.split(".", 1)
                
            return self.query(
                """
                SELECT 
                    column_name,
                    data_type,
                    character_maximum_length,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_schema=%s AND table_name=%s
                ORDER BY ordinal_position
                """,
                [schema, table]
            )
        elif db_type == "mysql":
            return self.query(
                """
                SELECT 
                    column_name,
                    data_type,
                    character_maximum_length,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_schema=%s AND table_name=%s
                ORDER BY ordinal_position
                """,
                [self.db_config["database"], table_name]
            )
        elif db_type == "sqlserver":
            return self.query(
                """
                SELECT 
                    column_name,
                    data_type,
                    character_maximum_length,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_catalog=? AND table_name=?
                ORDER BY ordinal_position
                """,
                [self.db_config["database"], table_name]
            )
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    def backup(self, backup_path: str) -> bool:
        """Backup the database.
        
        Args:
            backup_path: Path to save the backup
            
        Returns:
            True if backup was successful, False otherwise
        """
        db_type = self.db_config["type"]
        
        try:
            if db_type == "sqlite":
                # For SQLite, create a new connection for backup
                source_conn = sqlite3.connect(self.db_config["database"])
                dest_conn = sqlite3.connect(backup_path)
                
                source_conn.backup(dest_conn)
                
                dest_conn.close()
                source_conn.close()
                
                logger.info(f"SQLite database backed up to {backup_path}")
                return True
            else:
                # For other databases, this would typically involve executing a command-line utility
                # like pg_dump, mysqldump, etc., which is beyond the scope of this connector
                logger.warning(f"Backup not implemented for {db_type} database")
                return False
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get connector metrics.
        
        Returns:
            Dictionary of connector metrics
        """
        return {
            "db_name": self.db_name,
            "db_type": self.db_config["type"],
            "query_count": self.query_count,
            "error_count": self.error_count,
            "success_rate": ((self.query_count - self.error_count) / self.query_count) * 100 if self.query_count > 0 else 0,
            "active_connections": len(self._connections),
            "last_query_time": self.last_query_time
        }