import psycopg2
import utils
from collections import namedtuple
from typing import List, Dict, Union, Any, Optional
from base_crud_executor import BaseCrudExecutor
from settings import *

Credentials = namedtuple('Credentials', ['host', 'port', 'database', 'user', 'password'])
PSQL_CREDENTIALS = Credentials(POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DATABASE,
                               POSTGRES_DB_USER, POSTGRES_PASSWORD)


class QueryBuilder:

    @staticmethod
    def drop_tables() -> str:
        return """DROP TABLE IF EXISTS posts;  
        DROP TABLE IF EXISTS users;"""

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
    def insert_to_users_and_posts(post_as_dict: Dict[str, str]) -> str:
        return f"""WITH ins_to_users AS 
        (INSERT INTO users VALUES (
        '{post_as_dict["user_name"]}',
        '{post_as_dict["comment_karma"]}',
        '{post_as_dict["post_karma"]}',
        '{post_as_dict["total_karma"]}',
        '{post_as_dict["user_cakeday"]}'
        )
        ON CONFLICT (user_name)
        DO NOTHING)
        INSERT INTO posts VALUES (
        '{post_as_dict["unique_id"]}',
        '{post_as_dict["post_url"]}',
        '{post_as_dict["post_date"]}',
        '{post_as_dict["post_category"]}',
        '{post_as_dict["comments_number"]}',
        '{post_as_dict["votes_number"]}',
        '{post_as_dict["user_name"]}'
        )
        RETURNING unique_id
        ;
        """

    @staticmethod
    def retrieve_from_posts_and_users(unique_id: str = None) -> str:
        general_query = """SELECT 
            posts.unique_id, posts.post_url, posts.user_name, users.comment_karma, users.post_karma, users.total_karma,
            users.user_cakeday, posts.post_date, posts.comments_number, posts.votes_number, posts.post_category
            FROM posts 
            NATURAL JOIN users
            """
        if unique_id:
            return f"{general_query} WHERE unique_id = '{unique_id}';"
        return f"{general_query} ORDER BY unique_id;"

    @staticmethod
    def update_users_and_posts(data: Dict[str, str], unique_id: str) -> str:
        return f"""WITH upd_to_users AS
        (
        UPDATE users SET
        user_name  = '{data["user_name"]}',
        comment_karma = '{data["comment_karma"]}',
        post_karma = '{data["post_karma"]}',
        total_karma = '{data["total_karma"]}',
        user_cakeday = '{data["user_cakeday"]}'
        WHERE user_name IN 
        (SELECT user_name FROM posts
        WHERE unique_id = '{unique_id}')
        )
        UPDATE posts SET
        unique_id  = '{data["unique_id"]}',
        post_url = '{data["post_url"]}',
        post_date = '{data["post_date"]}',
        post_category = '{data["post_category"]}',
        comments_number = '{data["comments_number"]}'
        WHERE unique_id = '{unique_id}'
        RETURNING unique_id
        ;"""

    @staticmethod
    def delete_from_posts(unique_id: str) -> str:
        return f"""WITH deleted_post_info AS 
        (DELETE FROM posts * WHERE unique_id = '{unique_id}' RETURNING user_name) 
        SELECT user_name, count(*) FROM posts 
        WHERE user_name = (SELECT user_name FROM deleted_post_info)
        GROUP BY user_name
        ;
        """

    @staticmethod
    def delete_from_users(user_name: str) -> str:
        return f"""DELETE FROM users *
        WHERE user_name = '{user_name}'
        ;
        """


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


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
            print(e)

    def _close_connection(self):
        if self._connection:
            self._connection.commit()
            self._connection.close()

    @property
    def cursor(self):
        return self._connection.cursor()


class SQLExecutor(BaseCrudExecutor):

    def __init__(self, connection: psycopg2._ext.connection = SQLConnector(), query_builder=QueryBuilder()):
        self._connection = connection
        self._query_builder = query_builder
        self._execution_success = True
        self._execution_results = []
        self._drop_outdated_tables()
        self._create_new_tables()

    def __enter__(self):
        self._connection.cursor()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._connection.cursor().close()

    def _do(self, queries: List[str], fetch=False, multiple=False) -> None:
        with self._connection, self._connection.cursor as cur:
            for query in queries:
                try:
                    cur.execute(query)
                    if multiple:
                        self._execution_results.append(cur.fetchone()[0])
                    if fetch:
                        self._execution_results = cur.fetchall()
                except (Exception, psycopg2.ProgrammingError) as e:
                    self._execution_success = False
                    print(f'Exception occurred --> {e}.')
                    continue

    def _drop_outdated_tables(self) -> None:
        query = self._query_builder.drop_tables()
        self._do([query])

    def _create_new_tables(self):
        query = self._query_builder.create_tables()
        self._do([query])

    def insert(self, collected_data: Union[str, List[str]]) -> Union[str, List[str]]:
        if isinstance(collected_data, List):
            posts_as_dicts = [utils.inline_values_to_dict(post) for post in collected_data]
            queries = [self._query_builder.insert_to_users_and_posts(post) for post in posts_as_dicts]
            self._do(queries, multiple=True)
            if self._execution_success:
                return self._execution_results
        post_as_dict = utils.inline_values_to_dict(collected_data)
        query = self._query_builder.insert_to_users_and_posts(post_as_dict)
        self._do([query], fetch=True)
        if self._execution_success:
            unique_id = self._execution_results[0][0]
            return unique_id

    def find(self, unique_id: str = None) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
        query = self._query_builder.retrieve_from_posts_and_users(unique_id)
        self._do([query], fetch=True)
        if len(self._execution_results):
            formatted_results = [utils.info_from_sql_db_to_dict(result)
                                 for result in self._execution_results]
            return formatted_results

    def update(self, data: Dict[str, str], unique_id: str) -> Optional[bool]:
        upd_query = self._query_builder.update_users_and_posts(data, unique_id)
        self._do([upd_query], fetch=True)
        return bool(self._execution_results)

    def delete(self, unique_id: str) -> Optional[bool]:
        deletion_of_post_made = False
        posts_query = self._query_builder.delete_from_posts(unique_id)
        self._do([posts_query], fetch=True)
        if len(self._execution_results):
            deletion_of_post_made = True
            user_posts_number = self._execution_results[0][1]
            if user_posts_number == 1:
                user_name = self._execution_results[0][0]
                users_query = self._query_builder.delete_from_users(user_name)
                self._do([users_query])
        return deletion_of_post_made


executor = SQLExecutor()
