from dataclasses import dataclass
from functools import lru_cache
from typing import Any, List, Optional
import typing
from masscodeDriver.query import Query
from masscodeDriver.tdict import Content
import masscodeDriver.driver as driver

def get_driver():
    return driver.MasscodeDriver()

@lru_cache(maxsize=32)
def get(id : str, type_ : typing.Literal["folder", "snippet", "tag"]):
    iterlist : list = get_driver().__getattribute__(type_.lower() + "s")
    for item in iterlist:
        if item["id"] == id:
            return item

class GenericMeta(type):
    _instances : typing.Dict[type, typing.Dict[str, Any]] = {}

    def __call__(cls,**kwargs):
        id = kwargs["id"]
        if cls not in cls._instances:
            cls._instances[cls] = {}
        if id not in cls._instances[cls]:
            cls._instances[cls][id] = super().__call__(**kwargs)
        else:
            preped = kwargs.copy()
            preped.pop("id")
            cls._instances[cls][id].edit(**preped)
        return cls._instances[cls][id]

@dataclass(slots=True)
class Generic(object, metaclass=GenericMeta):
    id: str
    __prohibited__ : typing.ClassVar[List[str]] = ["id"]

    def edit(self, **kwargs):
        if len(kwargs) == 0:
            return
        with get_driver().saveLock():
            for k, v in kwargs.items():
                if k.startswith("_") or k in self.__prohibited__:
                    raise ValueError("invalid key")
                
                if v == getattr(self, k, None):
                    continue

                setattr(self, k, v)
                get(self.id, self.__class__.__name__)[k] = v

@dataclass(slots=True)
class Folder(Generic):
    name: str
    index: int
    parentId: Optional[str]
    defaultLanguage: str
    isOpen: bool
    isSystem: bool
    createdAt: int
    updatedAt: int

@dataclass(slots=True)
class Snippet(Generic):
    name: str
    description: Optional[str]
    isDeleted: bool
    isFavorites: bool
    folderId: str
    createdAt: int
    updatedAt: int
    tagsIds: List[str]
    content: List[Content]

@dataclass(slots=True)
class Tag(Generic):
    name: str
    createdAt: int
    updatedAt: int

class ModelQuery(Query):
    def __init__(self):
        super().__init__()
        self.__driver : driver.MasscodeDriver = self._Query__driver

    @property
    def tags(self):
        return [Tag(**item) for item in self.__driver.tags]
    
    @property
    def folders(self):
        return [Folder(**item) for item in self.__driver.folders]
    
    @property
    def snippets(self):
        return [Snippet(**item) for item in self.__driver.snippets]
    
    __funcs__ : typing.ClassVar[typing.Dict[str, typing.Callable]] = {}
    def __getattribute__(self, __name: str) -> typing.Any:
        if __name.startswith("_"):
            return super().__getattribute__(__name)
        
        res = super().__getattribute__(__name)
        if not callable(res):
            return res
        

        def model_decorator(func):
            def wrapper(*args, **kwargs):
                res = func(*args, **kwargs)
                if not res:
                    return res
                
                if "folder" in __name:
                    targetModel = Folder
                elif "tag" in __name:
                    targetModel = Tag
                elif "snippet" in __name:
                    targetModel = Snippet

                if isinstance(res, list):
                    return [targetModel(**item) for item in res]
                elif isinstance(res, dict):
                    return targetModel(**res)
                else:
                    return res
            return wrapper

        if __name not in self.__funcs__:
            self.__funcs__[__name] = model_decorator(res)
        return self.__funcs__[__name]
