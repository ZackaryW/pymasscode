from contextlib import contextmanager
from functools import cached_property
import os
import typing
import orjson
from sioDict import SioDict
from masscodeDriver.tdict import Folder, Snippet, StorageData, Tag

class MasscodeSingleton(type):
    _singleton : 'MasscodeDriver' = None

    def __call__(cls, *args, **kwargs):
        if cls._singleton is None:
            cls._singleton = super().__call__(*args, **kwargs)
        return cls._singleton

class MasscodeDriver(metaclass=MasscodeSingleton):
    def __init__(self):
        expectAppdataPath = os.path.join(os.getenv("APPDATA"), "massCode")

        if not os.path.exists(expectAppdataPath):
            raise Exception("MassCode is not installed or initialized correctly.")
        
        self.__appdataPath = expectAppdataPath

        self.__cached_preferences = None
        self.__cachedMdate_preferences = 0

        self.__cached_appConfig = None
        self.__cachedMdate_appConfig = 0


    @classmethod
    def create(cls)->'MasscodeDriver':
        return cls()

    @cached_property
    def _preferencePath(self):
        return os.path.join(self.__appdataPath,"v2", "preferences.json")
    
    @cached_property
    def _appConfigPath(self):
        return os.path.join(self.__appdataPath, "v2", "app.json")
        
    @property
    def _preferences(self):
        if not os.path.exists(self._preferencePath):
            raise Exception("MassCode is not installed or initialized correctly.")
        if self.__cached_preferences is None or self.__cachedMdate_preferences < os.path.getmtime(self._preferencePath):
            with open(self._preferencePath, "rb") as f:
                self.__cached_preferences = orjson.loads(f.read())
                self.__cachedMdate_preferences = os.path.getmtime(self._preferencePath)
        return self.__cached_preferences
    
    @property
    def _appConfig(self):
        if not os.path.exists(self._appConfigPath):
            raise Exception("MassCode is not installed or initialized correctly.")
        if self.__cached_appConfig is None or self.__cachedMdate_appConfig < os.path.getmtime(self._appConfigPath):
            with open(self._appConfigPath, "rb") as f:
                self.__cached_appConfig = orjson.loads(f.read())
                self.__cachedMdate_appConfig = os.path.getmtime(self._appConfigPath)
        return self.__cached_appConfig
    
    @property
    def _dbStoragePath(self):
        return self._preferences.get("storagePath", None)
    
    @cached_property
    def _db(self):
        class SioDictB(SioDict):
            @staticmethod
            def _save(d, path : str):
                with open(path, 'wb') as f:
                    f.write(orjson.dumps(d, option=orjson.OPT_INDENT_2))

        sd = SioDictB(os.path.join(self._dbStoragePath, "db.json"))
        return sd
    
    @property
    def folders(self) -> typing.List[Folder]:
        return self._db.get("folders", [])
    
    @property
    def tags(self) -> typing.List[Tag]:
        return self._db.get("tags", [])
    
    @property
    def snippets(self) -> typing.List[Snippet]:
        return self._db.get("snippets", [])

    @contextmanager
    def saveLock(self):
        yield self._db.saveLock()

    def merge(self, d : StorageData):
        raise NotImplementedError()
    
    def popFolder(self, folder : Folder):
        raise NotImplementedError()
    
    def popTag(self, tag : Tag):
        raise NotImplementedError()
    
