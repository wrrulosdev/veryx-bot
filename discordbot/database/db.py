import sqlite3
import sys
import os

from typing import Optional, Any
from contextlib import contextmanager

from loguru import logger

from discordbot.database.models.ids import IdObject
from .models.discord_user import DiscordUser
from .models.ids import IdObject
from ..constants import BotConstants


class Database:
    def __init__(self) -> None:
        if not os.path.exists('db'):
            os.makedirs('db')

        if not os.path.exists(f'db/{BotConstants.DB_FILENAME}'):
            open(f'db/{BotConstants.DB_FILENAME}', 'w').close()

        try:
            self.conn: sqlite3.Connection = sqlite3.connect(f'db/{BotConstants.DB_FILENAME}')

        except sqlite3.Error as e:
            logger.critical(f'Failed to connect to the database: {e}')
            sys.exit(1)

        self._create_table()

    @contextmanager
    def _get_cursor(self):
        """Context manager for database cursor."""
        cursor: Optional[sqlite3.Cursor] = None

        try:
            cursor = self.conn.cursor()
            yield cursor

        except sqlite3.Error as e:
            logger.error(f'Database error: {e}')
            self.conn.rollback()
            raise

        finally:
            if cursor:
                cursor.close()

    def _create_table(self) -> None:
        """Creates the users table if it doesn't exist."""
        try:
            with self._get_cursor() as cursor:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ids (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        object_id INTEGER NOT NULL,
                        name TEXT NOT NULL, 
                        type TEXT NOT NULL
                    );
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS discord_users (
                        discord_id INTEGER PRIMARY KEY,
                        username TEXT NOT NULL,
                        joined_at TEXT NOT NULL
                    );
                ''')
                self.conn.commit()

        except sqlite3.Error as e:
            logger.critical(f'Failed to create table: {e}')
            sys.exit(1)

    def _execute_query(self, query: str, params: tuple = ()) -> None:
        """
        Executes an insert or update query on the database.
        :param query: The SQL query to execute.
        :param params: The parameters for the query, default is an empty tuple.
        """
        try:
            with self._get_cursor() as cursor:
                cursor.execute(query, params)
                self.conn.commit()

        except sqlite3.Error as e:
            logger.error(f'Error executing query: {e}')

    def _fetch_data(self, query: str, params: tuple = ()) -> list:
        """
        Fetches data from the database.
        :param query: The SQL query to fetch data.
        :param params: The parameters for the query, default is an empty tuple.
        :return: A list of tuples containing the fetched data.
        """
        try:
            with self._get_cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()

        except sqlite3.Error as e:
            logger.error(f'Error fetching data: {e}')
            return []

    def add_id(self, id_to_add: int, name: str, id_type: str) -> None:
        """
        Adds a new category, channel, message or role to the database.
        :param id_to_add: The ID of the category (from Discord).
        :param name: The name of the category.
        :param id_type: Object type to add. (ticket, category, channel, message or role)
        """
        if id_type not in ['ticket', 'category', 'channel', 'message', 'role']:
            logger.critical(f'Invalid id type in add_id -> {id_type}')
            return

        # Check if the name already exists
        existing_entry: Optional[IdObject] = self.get_id_by_name(name)

        if existing_entry:
            self.del_id(name)

        self._execute_query('''
        INSERT INTO ids (object_id, name, type)
        VALUES (?, ?, ?);
        ''', (id_to_add, name, id_type))

    def del_id(self, name: str) -> None:
        """
        Deletes a category, channel, message or role from the database by its name.
        :param name: The name of the object to delete (ticket, category, channel, message or role)
        """
        existing_entry: Optional[IdObject] = self.get_id_by_name(name)

        if not existing_entry:
            logger.warning(f'No entry found with the name "{name}" to delete.')
            return

        # Delete the entry if it exists
        self._execute_query('''
        DELETE FROM ids WHERE name = ?;
        ''', (name,))
        logger.info(f'Entry with name "{name}" has been deleted from the database.')

    def get_id_by_name(self, name: str) -> Optional[IdObject]:
        """
        Fetches a category, channel, message or role by its name from the database.
        :param name: The name of the object to search for.
        :return: A dictionary containing the object's information or an empty dictionary if not found.
        """
        result: list = self._fetch_data('''
        SELECT id, object_id, name, type
        FROM ids
        WHERE name = ?;
        ''', (name,))

        if result:
            return IdObject(
                id=result[0][0],
                object_id=result[0][1],
                name=result[0][2],
                type=result[0][3],
            )

        return None

    def get_id_by_id(self, object_id: int) -> Optional[IdObject]:
        """
        Fetches a category, channel, message or role by its object_id from the database.
        :param object_id: The id of the object to search for.
        :return: A dictionary containing the object's information or an empty dictionary if not found.
        """
        result: list = self._fetch_data('''
        SELECT id, object_id, name, type
        FROM ids
        WHERE object_id = ?;
        ''', (object_id,))

        if result:
            return IdObject(
                id=result[0][0],
                object_id=result[0][1],
                name=result[0][2],
                type=result[0][3],
            )

        return None

    def add_discord_user(self, discord_id: int, username: str, joined_at: str) -> None:
        """
        Adds a new Discord user to the database.
        :param discord_id: The Discord user ID.
        :param username: The Discord username.
        :param joined_at: The timestamp when the user joined the server.
        """
        existing_user = self.get_discord_user_by_id(discord_id)

        if existing_user:
            logger.info(f'User with ID {discord_id} already exists. Updating information.')
            self.update_discord_user(discord_id, username, joined_at)
            return

        self._execute_query('''
        INSERT INTO discord_users (discord_id, username, joined_at)
        VALUES (?, ?, ?);
        ''', (discord_id, username, joined_at))

    def get_discord_user_by_id(self, discord_id: int) -> Optional[DiscordUser]:
        """
        Fetches a Discord user by their Discord ID.
        :param discord_id: The Discord user ID.
        :return: A dictionary with user information or None if not found.
        """
        result: list = self._fetch_data('''
        SELECT discord_id, username, joined_at
        FROM discord_users
        WHERE discord_id = ?;
        ''', (discord_id,))

        if result:
            return DiscordUser(
                discord_id=result[0][0],
                username=result[0][1],
                joined_at=result[0][2]
            )

        return None

    def get_discord_users_count(self) -> int:
        """
        Fetches the count of all discord users in the database.
        :return: The count of discord users.
        """
        try:
            with self._get_cursor() as cursor:
                cursor.execute('''
                SELECT COUNT(*) FROM discord_users;
                ''')
                result: list = cursor.fetchone()
                return result[0]

        except sqlite3.Error as e:
            logger.error(f'Error fetching users count from database: {e}')
            return 0

    def update_discord_user(self, discord_id: int, username: str, joined_at: str) -> None:
        """
        Updates the information of an existing Discord user in the database.
        :param discord_id: The Discord user ID.
        :param username: The updated Discord username.
        :param joined_at: The updated timestamp when the user joined the server.
        """
        self._execute_query('''
        UPDATE discord_users
        SET username = ?, joined_at = ?
        WHERE discord_id = ?;
        ''', (username, joined_at, discord_id))

    def del_discord_user(self, discord_id: int) -> None:
        """
        Deletes a Discord user from the database by their Discord ID.
        :param discord_id: The Discord user ID.
        """
        existing_user = self.get_discord_user_by_id(discord_id)

        if not existing_user:
            logger.warning(f'No user found with ID {discord_id} to delete.')
            return

        self._execute_query('''
        DELETE FROM discord_users WHERE discord_id = ?;
        ''', (discord_id,))
        logger.info(f'User with ID {discord_id} has been deleted from the database.')

    def _close(self) -> None:
        """Closes the database connection."""
        try:
            self.conn.close()
            logger.info('Database connection closed successfully.')

        except sqlite3.Error as e:
            logger.error(f'Failed to close database connection: {e}')