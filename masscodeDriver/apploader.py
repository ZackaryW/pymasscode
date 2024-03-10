import os
import shutil
from masscodeDriver.model import StorageData

from masscodeDriver.utils import FileProperty, SingletonMeta

class AppLoader(metaclass=SingletonMeta):
    CREATE_BKUP : bool = True

    def __init__(self, expectAppdataPath : str = None) -> None:
        if expectAppdataPath is None:
            expectAppdataPath = os.path.join(os.getenv("APPDATA"), "massCode")

        if not os.path.exists(expectAppdataPath):
            raise Exception("MassCode is not installed or initialized correctly.")

        if expectAppdataPath.endswith("db.json"):
            self.__class__.dbPath = expectAppdataPath
        else:
            self.__appdataPath = expectAppdataPath

        if self.CREATE_BKUP:
            shutil.copy(self.dbPath, os.path.dirname(self.dbPath) + "/db.bkup.json")

    @property
    def appdataPath(self):
        return self.__appdataPath
    
    @property
    def preferencePath(self):
        return os.path.join(self.__appdataPath, "v2", "preferences.json")

    preferences : dict = FileProperty(os.path.join("{self.appdataPath}", "v2", "preferences.json"))

    @property
    def appconfigPath(self):
        return os.path.join(self.__appdataPath, "v2", "app.json")
    
    appconfig : dict = FileProperty(os.path.join("{self.appdataPath}", "v2", "app.json"))

    @property
    def dbFolderPath(self):
        return self.preferences["storagePath"]

    @property
    def dbPath(self):
        return os.path.join(self.dbFolderPath, "db.json")
    
    _db_direct : StorageData = FileProperty("{self.dbPath}")

class LazyLoader:
    def __get__(self, instance, owner):
        return AppLoader()

class Shortcut:
    lazyLoader = LazyLoader()