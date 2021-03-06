"""PostgreSQL CRUD-executor.

Methods of PostreSQL-executor use those of
SQL-QueryBuilder to form specific queries to database
and send back info to the Webserver.
"""
import datetime
import logging
import settings
import utils
import psycopg2
from collections import namedtuple
from typing import List, Dict, Union, Any, Tuple
from .base_crud_executor import BaseCrudExecutor
from .singleton_connector import Singleton

Credentials = namedtuple('Credentials', ['host', 'port', 'database', 'user', 'password'])
PSQL_CREDENTIALS = Credentials(settings.POSTGRES_HOST, settings.POSTGRES_PORT, settings.POSTGRES_DATABASE,
                               settings.POSTGRES_DB_USER, settings.POSTGRES_PASSWORD)


class QueryBuilder:

    @staticmethod
    def drop_tables() -> str:
        return "DROP TABLE IF EXISTS posts; DROP TABLE IF EXISTS users;"

    @staticmethod
    def create_tables() -> str:
        return """CREATE TABLE users ( 
        user_name VARCHAR(20),
        comment_karma VARCHAR(6),
        post_karma VARCHAR(6),
        total_karma VARCHAR(6),
        user_cakeday DATE,
        CONSTRAINT pk_users PRIMARY KEY (user_name)
        );
        CREATE TABLE posts (
        unique_id UUID,
        post_url VARCHAR(150),
        post_date DATE,
        post_category VARCHAR(20),
        comments_number VARCHAR(6),
        votes_number VARCHAR(6),
        user_name VARCHAR(20) REFERENCES users (user_name) 
        ON UPDATE CASCADE,   
        CONSTRAINT pk_posts PRIMARY KEY (unique_id)
        );"""

    @staticmethod
    def insert_to_users_and_posts(post_as_dict: Dict[str, str], unique_id_given: str = '') \
            -> Tuple[str, Dict[str, str]]:

        unique_id = post_as_dict.get("unique_id")
        post_url = post_as_dict.get("post_url", "")
        post_date = post_as_dict.get("post_date")
        post_category = post_as_dict.get("post_category", "")
        comments_number = post_as_dict.get("comments_number", "")
        votes_number = post_as_dict.get("votes_number", "")
        user_name = post_as_dict.get("user_name", "")
        comment_karma = post_as_dict.get("comment_karma", "")
        post_karma = post_as_dict.get("post_karma", "")
        total_karma = post_as_dict.get("total_karma", "")
        user_cakeday = post_as_dict.get("user_cakeday")

        query_parameters = {'user_name': user_name, 'comment_karma': comment_karma, 'post_karma': post_karma,
                            'total_karma': total_karma, 'user_cakeday': user_cakeday, 'unique_id': unique_id,
                            'post_url': post_url, 'post_date': post_date, 'post_category': post_category,
                            'comments_number': comments_number, 'votes_number': votes_number
                            }

        update_operation = unique_id_given
        if update_operation:
            return f"""WITH upd_to_users AS
            (
            UPDATE users SET
            user_name = %(user_name)s,
            comment_karma = %(comment_karma)s,
            post_karma = %(post_karma)s,
            total_karma = %(total_karma)s,
            user_cakeday = %(user_cakeday)s
            WHERE user_name IN  
            (SELECT user_name FROM posts
            WHERE unique_id = '{unique_id_given}')
            )
            UPDATE posts SET
            post_url = %(post_url)s,
            post_date = %(post_date)s,
            post_category = %(post_category)s,
            comments_number = %(comments_number)s,
            votes_number = %(votes_number)s
            WHERE unique_id = '{unique_id_given}'
            RETURNING unique_id
            ;""", query_parameters

        return """WITH ins_to_users AS 
        (INSERT INTO users VALUES (%(user_name)s, %(comment_karma)s, %(post_karma)s,
        %(total_karma)s, %(user_cakeday)s) ON CONFLICT (user_name) DO NOTHING)
        INSERT INTO posts VALUES (%(unique_id)s, %(post_url)s, %(post_date)s, %(post_category)s,
        %(comments_number)s, %(votes_number)s, %(user_name)s) RETURNING unique_id;
        """, query_parameters

    @staticmethod
    def retrieve_from_posts_and_users(unique_id: str = None) -> str:
        general_query = """SELECT 
            posts.unique_id, posts.post_url, posts.user_name, users.comment_karma, users.post_karma, users.total_karma,
            users.user_cakeday, posts.post_date, posts.comments_number, posts.votes_number, posts.post_category
            FROM posts NATURAL JOIN users
            """
        if unique_id:
            return f"{general_query} WHERE unique_id = '{unique_id}';"
        return f"{general_query} ORDER BY unique_id;"

    @staticmethod
    def delete_from_posts(unique_id: str) -> str:
        return f"""WITH deleted_post_info AS (DELETE FROM posts * WHERE unique_id = '{unique_id}' RETURNING user_name) 
        SELECT user_name, count(*) FROM posts WHERE user_name = (SELECT user_name FROM deleted_post_info)
        GROUP BY user_name;"""

    @staticmethod
    def delete_from_users(user_name: str) -> str:
        return f"DELETE FROM users * WHERE user_name = '{user_name}';"


class SQLConnector(metaclass=Singleton):

    def __init__(self, credentials: namedtuple = PSQL_CREDENTIALS):
        self._credentials = credentials._asdict()
        self._connection = None

    def __enter__(self):
        self._establish_connection()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._close_connection()

    def _establish_connection(self):
        try:
            self._connection = psycopg2.connect(**self._credentials)
        except (Exception, psycopg2.DatabaseError) as e:
            logging.error(e)

    def _close_connection(self):
        if self._connection:
            self._connection.commit()
            self._connection.close()

    @property
    def cursor(self):
        return self._connection.cursor()


class PostgreSQLExecutor(BaseCrudExecutor):

    def __init__(self, connection: psycopg2._ext.connection = SQLConnector(), query_builder=QueryBuilder()):
        self._connection = connection
        self._query_builder = query_builder
        self._execution_results = []
        self._drop_outdated_tables()
        self._create_new_tables()

    def __enter__(self):
        self._connection.cursor()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._connection.cursor().close()

    def _do(self, queries: List[Union[str, Tuple[str, Dict[str, str]]]], fetch=False, multiple=False) \
            -> Union[None, List[str], List[Tuple[str]], List[Tuple[str, datetime.date]]]:
        with self._connection, self._connection.cursor as cur:
            self._execution_results.clear()
            for query in queries:
                try:
                    if isinstance(query, Tuple):
                        cur.execute(*query)
                    if isinstance(query, str):
                        cur.execute(query)
                    if multiple:
                        self._execution_results.append(cur.fetchone()[0])
                    if fetch:
                        self._execution_results = cur.fetchall()
                except (Exception, psycopg2.ProgrammingError) as e:
                    logging.error(f'Exception occurred --> {e}.')
                    continue
            return self._execution_results

    def _drop_outdated_tables(self) -> None:
        query = self._query_builder.drop_tables()
        self._do([query])

    def _create_new_tables(self):
        query = self._query_builder.create_tables()
        self._do([query])

    def insert(self, collected_data: Union[str, List[str]]) -> Union[str, List[str]]:
        if isinstance(collected_data, str):
            collected_data = [collected_data]
        posts_as_dicts = [utils.inline_values_to_dict(line) for line in collected_data]
        queries = [self._query_builder.insert_to_users_and_posts(post) for post in posts_as_dicts]
        self._do(queries, multiple=True)
        inserted_ids = self._execution_results
        if len(inserted_ids) == 1:
            return inserted_ids[0]
        return inserted_ids

    def find(self, unique_id: str = None) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
        query = self._query_builder.retrieve_from_posts_and_users(unique_id)
        results = self._do([query], fetch=True)
        if len(results):
            formatted_results = [utils.info_from_sql_db_to_dict(result) for result in results]
            return formatted_results

    def update(self, data: Dict[str, str], unique_id: str) -> bool:
        upd_query = self._query_builder.insert_to_users_and_posts(data, unique_id)
        results = self._do([upd_query], fetch=True)
        return bool(results)

    def delete(self, unique_id: str) -> bool:
        deletion_success = False
        posts_query = self._query_builder.delete_from_posts(unique_id)
        results = self._do([posts_query], fetch=True)
        if len(results):
            deletion_success = True
            user_posts_number = results[0][1]
            if user_posts_number == 1:
                user_name = results[0][0]
                users_query = self._query_builder.delete_from_users(user_name)
                self._do([users_query])
        return deletion_success
