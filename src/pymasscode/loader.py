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

        self.dbPath = dbPath
        self.appdataPath = appdataPath

        if self.dbPath and os.path.join(self.dbPath):
            self.dbPath = os.path.abspath(self.dbPath)
            assert os.path.exists(self.dbPath)
            assert self.dbPath.endswith("db.json")
        else:
            if not self.appdataPath:
                self.appdataPath = Loader.getPossiblePathByPlatform()

            if not os.path.exists(self.appdataPath):
                raise RuntimeError(
                    "MassCode is not installed or initialized correctly."
                )

            self.dbPath = os.path.join(self.preferences["storagePath"], "db.json")

        # check if db path is empty (0kb), if yes, assume an error occured and restore bkup file if it exists
        if not os.path.exists(self.dbPath) or os.path.getsize(self.dbPath) == 0:
            if os.path.exists(os.path.dirname(self.dbPath) + "/db.bkup.json"):
                shutil.copy(os.path.dirname(self.dbPath) + "/db.bkup.json", self.dbPath)

        if self.config["create_bkup"]:
            shutil.copy(self.dbPath, os.path.dirname(self.dbPath) + "/db.bkup.json")

    @property
    def preferencePath(self):
        return os.path.join(self.appdataPath, "v2", "preferences.json")

    preferences: dict = FileProperty(
        os.path.join("{self.appdataPath}", "v2", "preferences.json")
    )

    @property
    def appconfigPath(self):
        return os.path.join(self.appdataPath, "v2", "app.json")

    appconfig: dict = FileProperty(os.path.join("{self.appdataPath}", "v2", "app.json"))

    dbIo: io.TextIOWrapper = FileProperty("{self.dbPath}", passOverIoOnly=True)

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
            self.__dbContentLastModified = os.path.getmtime(self.dbPath)

        if self.__dbContentLastModified == os.path.getmtime(self.dbPath):
            return self.__dbContent

        self.__dict__.pop("__dbContent", None)
        self.__dbContentLastModified = os.path.getmtime(self.dbPath)

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
