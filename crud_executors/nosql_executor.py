"""MongoDB CRUD-executor.

Methods of MongoDB-executor use those of
NoSQL-QueryBuilder to form specific CRUD queries to mongo
instance and send back info to the Webserver.
"""
import logging

import settings
import utils
import pymongo.errors
from pymongo import MongoClient
from .singleton_connector import Singleton
from .base_crud_executor import BaseCrudExecutor
from typing import Union, List, Dict, Callable, Optional

MONGO_HOST = settings.MONGO_HOST
MONGO_PORT = int(settings.MONGO_PORT)
MONGO_DB_NAME = settings.MONGO_DB_NAME
MAX_CONNECTION_WAIT = 200


class MongoConnector(metaclass=Singleton):

    def __init__(self, host: str = MONGO_HOST, port: int = MONGO_PORT):
        self._host = host
        self._port = port
        self._client = None

    @property
    def client(self) -> pymongo.mongo_client.MongoClient:
        try:
            self._client = MongoClient(host=MONGO_HOST, port=MONGO_PORT, connectTimeoutMS=MAX_CONNECTION_WAIT)
        except (Exception, pymongo.errors.ConnectionFailure) as e:
            logging.error(f'Warning from MongoDB. Exception occurred --> {e}.')
        return self._client


class ClientSessionDecorator:

    def __init__(self, query_method: Callable, connector: MongoConnector = MongoConnector(),
                 db_name: str = MONGO_DB_NAME):
        self._query_builder = QueryBuilder()
        self._query_method = query_method
        self._connector = connector
        self._results = None
        self._db = db_name
        self._posts = None
        self._users = None

    def __call__(self, *args, **kwargs):
        with self._connector.client as client:
            db = client[self._db]
            self._posts = db['posts']
            self._users = db['users']
            if self._query_method.__name__ in ('find', 'check_entry'):
                return self._query_method(self, *args, **kwargs, posts_collection=self._posts)
            return self._query_method(self, *args, **kwargs,
                                      posts_collection=self._posts, users_collection=self._users)

    def _check_entry_exists(self, unique_id: str, posts_collection: pymongo.collection.Collection) -> Optional[str]:
        self._results = posts_collection.aggregate(pipeline=self._query_builder.check_for_user(unique_id))
        try:
            return list(self._results)[0]["user"]
        except IndexError:
            return


class QueryBuilder:

    @staticmethod
    def insert_to_posts(post_as_dict: Dict[str, str], user_id: str, upd: bool = False) -> Dict[str, str]:
        unique_id = {"_id": post_as_dict["unique_id"]}
        new_contents = {
            "post_url": post_as_dict.get("post_url", ""),
            "post_date": post_as_dict.get("post_date", ""),
            "post_category": post_as_dict.get("post_category", ""),
            "comments_number": post_as_dict.get("comments_number", ""),
            "votes_number": post_as_dict.get("votes_number", ""),
            "user": user_id
        }
        if upd:
            return new_contents
        return dict(**unique_id, **new_contents)

    @staticmethod
    def insert_to_users(post_as_dict: Dict[str, str]) -> Dict[str, str]:
        return {
            "user_name": post_as_dict.get("user_name", ""),
            "comment_karma": post_as_dict.get("comment_karma", ""),
            "post_karma": post_as_dict.get("post_karma", ""),
            "total_karma": post_as_dict.get("total_karma", ""),
            "user_cakeday": post_as_dict.get("user_cakeday", "")
        }

    @staticmethod
    def find_by_id(unique_id: str):
        return {"_id": unique_id}

    def retrieve(self, unique_id: str = None) \
            -> List[Union[Dict[str, str], Dict[str, Dict[str, str]]]]:
        id_matching = [
            {
                "$match": self.find_by_id(unique_id)
            }
        ]
        lookup_retrieval = [
            {
                "$lookup":
                    {
                        "from": "users",
                        "localField": "user",
                        "foreignField": "_id",
                        "as": "user"
                    }
            },
            {"$unwind": "$user"},
            {
                "$addFields":
                    {
                        "unique_id": "$_id",
                        "user_name": "$user.user_name",
                        "comment_karma": "$user.comment_karma",
                        "post_karma": "$user.post_karma",
                        "total_karma": "$user.total_karma",
                        "user_cakeday": "$user.user_cakeday"

                    }
            },
            {
                "$project":
                    {
                        "user": 0,
                        "_id": 0
                    }
            }
        ]
        if unique_id:
            return id_matching + lookup_retrieval
        return lookup_retrieval

    def check_for_user(self, unique_id: str):
        return [
            {
                "$match": self.find_by_id(unique_id)
            },
            {
                "$project":
                    {
                        "user": 1,
                        "_id": 0
                    }
            }
        ]

    @staticmethod
    def upd(_id: str, upd_info):
        return {"_id": _id}, {"$set": upd_info}


class MongoExecutor(BaseCrudExecutor):

    def __init__(self):
        self._drop_tables()
        self._query_builder = None

    @ClientSessionDecorator
    def _drop_tables(self, posts_collection: pymongo.collection.Collection,
                     users_collection: pymongo.collection.Collection) -> None:
        posts_collection.drop()
        users_collection.drop()

    @ClientSessionDecorator
    def insert(self, collected_info: Union[str, List[str]],
               posts_collection: pymongo.collection.Collection,
               users_collection: pymongo.collection.Collection) -> Union[str, List[str]]:
        if isinstance(collected_info, str):
            collected_info = [collected_info]
        posts_as_dicts = [utils.inline_values_to_dict(line) for line in collected_info]

        users_queries = [self._query_builder.insert_to_users(post) for post in posts_as_dicts]
        insertions_to_users_results = users_collection.insert_many(users_queries)
        user_ids = insertions_to_users_results.inserted_ids

        posts_queries = [self._query_builder.insert_to_posts(post, user_id)
                         for post, user_id in zip(posts_as_dicts, user_ids)]
        insertions_to_posts_results = posts_collection.insert_many(posts_queries)
        inserted_ids = insertions_to_posts_results.inserted_ids

        if len(inserted_ids) == 1:
            return inserted_ids[0]
        return inserted_ids

    @ClientSessionDecorator
    def find(self, unique_id: Optional[str] = None,
             posts_collection: pymongo.collection.Collection = None) \
            -> Union[Dict[str, str], List[Dict[str, str]], None]:
        if unique_id:
            search_results = posts_collection.aggregate(pipeline=self._query_builder.retrieve(unique_id))
            try:
                return list(search_results)[0]
            except IndexError:
                return
        search_results = posts_collection.aggregate(pipeline=self._query_builder.retrieve())
        return list(search_results)

    @ClientSessionDecorator
    def update(self, new_doc: Dict[str, str], unique_id: str,
               posts_collection: pymongo.collection.Collection,
               users_collection: pymongo.collection.Collection) -> bool:
        upd_result = False
        user_id = self._check_entry_exists(unique_id, posts_collection)
        if user_id:
            try:
                users_upd_info = self._query_builder.insert_to_users(new_doc)
                posts_upd_info = self._query_builder.insert_to_posts(new_doc, user_id, upd=True)
                posts_collection.update_one(*self._query_builder.upd(unique_id, posts_upd_info))
                users_collection.update_one(*self._query_builder.upd(user_id, users_upd_info))
                upd_result = True
            except (KeyError, pymongo.errors.DuplicateKeyError, pymongo.errors.PyMongoError) as e:
                logging.error(f'Error from MongoDB ---> {e}')
        return upd_result

    @ClientSessionDecorator
    def delete(self, unique_id: str,
               posts_collection: pymongo.collection.Collection,
               users_collection: pymongo.collection.Collection) -> bool:
        deletion_result = False
        user_id = self._check_entry_exists(unique_id, posts_collection)
        if user_id:
            posts_collection.delete_one(self._query_builder.find_by_id(unique_id))
            users_collection.delete_one(self._query_builder.find_by_id(user_id))
            deletion_result = True
        return deletion_result
