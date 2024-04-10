from contextlib import contextmanager
from functools import cached_property
import io
import json
import os
import shutil
from typing import TypedDict

from .etc.fileProp import FileProperty
from .model import StorageData


class _Loader:
    def __init__(self) -> None:
        self.currentLoader = None

    def __get__(self, instance, owner):
        if self.currentLoader is None:
            self.currentLoader = Loader()

        return self.currentLoader

    def __set__(self, instance, value):
        self.currentLoader = value


class LoaderConfig(TypedDict):
    create_bkup: bool

    @staticmethod
    def defaultConfig():
        return {"create_bkup": True}


class Loader:
    currentLoader = _Loader()

    @staticmethod
    def getPossiblePathByPlatform():
        import platform

        if platform.system() == "Windows":
            return os.path.join(os.getenv("APPDATA"), "massCode")
        else:
            return os.path.join(os.getenv("HOME"), ".massCode")

    def __init__(
        self, dbPath: str = None, appdataPath: str = None, config: dict = None
    ) -> None:
        self.__dbLockGate = 0

        if config is not None:
            self.config = config
        else:
            self.config = LoaderConfig.defaultConfig()

        self.__dbPath = dbPath
        self.__appdataPath = appdataPath

        if self.__dbPath and os.path.join(self.__dbPath):
            self.__dbPath = os.path.abspath(self.__dbPath)
            assert os.path.exists(self.__dbPath)
            assert self.__dbPath.endswith("db.json")
        else:
            if not self.__appdataPath:
                self.__appdataPath = Loader.getPossiblePathByPlatform()

            if not os.path.exists(self.__appdataPath):
                raise RuntimeError(
                    "MassCode is not installed or initialized correctly."
                )

            self.__dbPath = os.path.join(self.preferences["storagePath"], "db.json")

        # check if db path is empty (0kb), if yes, assume an error occured and restore bkup file if it exists
        if not os.path.exists(self.__dbPath) or os.path.getsize(self.__dbPath) == 0:
            if os.path.exists(os.path.dirname(self.__dbPath) + "/db.bkup.json"):
                shutil.copy(os.path.dirname(self.__dbPath) + "/db.bkup.json", self.__dbPath)

        if self.config["create_bkup"]:
            shutil.copy(self.__dbPath, os.path.dirname(self.__dbPath) + "/db.bkup.json")

    @property
    def dbPath(self):
        return self.__dbPath
    
    @property
    def appdataPath(self):
        return self.__appdataPath

    @property
    def preferencePath(self):
        return os.path.join(self.__appdataPath, "v2", "preferences.json")

    preferences: dict = FileProperty(preferencePath)

    @property
    def appconfigPath(self):
        return os.path.join(self.__appdataPath, "v2", "app.json")

    appconfig: dict = FileProperty(appconfigPath)

    dbIo: io.TextIOWrapper = FileProperty(dbPath, loadmethod=FileProperty.returnIOWrapper)

    def dbFolders(self):
        for folder in self.dbContent["folders"]:
            yield folder

    def dbSnippets(self):
        for snippet in self.dbContent["snippets"]:
            yield snippet

    def dbTags(self):
        for tag in self.dbContent["tags"]:
            yield tag

    @cached_property
    def __dbContent(self):
        self.dbIo.seek(0)
        return json.load(self.dbIo)

    @property
    def dbContent(self) -> StorageData:
        if not hasattr(self, "__dbContentLastModified"):
            self.__dbContentLastModified = os.path.getmtime(self.__dbPath)

        if self.__dbContentLastModified == os.path.getmtime(self.__dbPath):
            return self.__dbContent

        self.__dict__.pop("__dbContent", None)
        self.__dbContentLastModified = os.path.getmtime(self.__dbPath)

        return self.__dbContent

    @contextmanager
    def dbLock(self):
        try:
            self.__dbLockGate += 1
            yield

        finally:
            self.__dbLockGate -= 1
            if self.__dbLockGate == 0:
                self.dbIo.seek(0)
                self.dbIo.truncate()
                self.dbIo.write(json.dumps(self.dbContent, indent=4))

    @property
    def dbMdate(self):
        # mdate
        return hash(self.__dbContentLastModified)
