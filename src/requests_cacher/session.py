import hashlib
import json
import os
import requests
import sqlite3
from typing import Optional

class CacheDataBase:
    def __init__(self) -> None:
        self.database_path = self._get_database_path()
        self.connection = sqlite3.connect(self.database_path)
        self.cursor = self.connection.cursor()
        self._schema_query = self._get_create_table_query()
        self.cursor.execute(self._schema_query)
        self.connection.commit()

    def _get_database_path(self) -> str:
        path = os.getcwd()
        while path != os.path.dirname(path):
            if os.path.isdir(os.path.join(path, "data")):
                break
            path = os.path.dirname(path)
        else:
            raise FileNotFoundError("There must exist a directory named data in the project")

        database_path = os.path.relpath(os.path.join(path, "data/cached_responses.sqlite"))

        return database_path

    def _get_create_table_query(self) -> str:
        query = f"CREATE TABLE IF NOT EXISTS cache (uri TEXT, params_hash TEXT CHECK(length(params_hash) = 32), content TEXT) "

        return query

    def fetch_cache(self, uri: str, params_hash: str) -> Optional[dict]:
        query = f"SELECT content FROM cache WHERE uri = ? AND params_hash = ?"
        self.cursor.execute(query, (uri, params_hash))
        response = self.cursor.fetchone()

        return json.loads(response[0]) if response else None

    def cache_response(self, uri: str, params_hash: str, content: str):
        query = f"INSERT INTO cache (uri, params_hash, content) VALUES (?, ?, ?)"
        self.cursor.execute(query, (uri, params_hash, content))
        self.connection.commit()


class Session:
    def __init__(self, domain, headers: Optional[dict] = None, params: Optional[dict] = None) -> None:
        self.domain = domain
        self.session = requests.Session()
        if headers:
            self.session.headers.update(headers)
        if params:
            self.session.params = params
        self.db = CacheDataBase()

    def get(self, endpoint: str, params: Optional[dict]) -> dict:
        uri = f"{self.domain}/{endpoint}"
        params_hash = self._compute_dictionary_hash(params)

        if content := self.db.fetch_cache(uri, params_hash):
            return content

        response = self.session.get(uri, params=params)
        response.raise_for_status()
        content = response.json()
        self.db.cache_response(uri, params_hash, json.dumps(content))

        return content

    @staticmethod
    def _compute_dictionary_hash(dictionary: Optional[dict]) -> str:
        dictionary_str = json.dumps(dictionary, sort_keys=True) if dictionary else ''
        hash_md5 = hashlib.md5(dictionary_str.encode()).hexdigest()
        return hash_md5
