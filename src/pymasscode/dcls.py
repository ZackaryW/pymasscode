from dataclasses import dataclass
import datetime
import inspect
import typing

from .etc.clsprop import classproperty
from .loader import Loader
from .model import Content
from .etc.tinydb_query import FolderQuery, SnippetQuery, TagQuery


class ClsMeta:
    def __get__(self, instance, owner):
        if not hasattr(self, "_clsname"):
            self._clsname = owner.__name__.lower() + "s"

        return self._clsname


class BaseItemMeta(type):
    _instances = {}
    _query_cache = {}
    _query_max_count = 100
    _db_hash = -1

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = {}

        _id = kwargs.get("id", None)
        if _id is None:
            _id = kwargs.get("_id", None)

        if _id is None and len(args) > 0:
            _id = args[0]

        if not _id:
            raise ValueError("No id provided")

        if _id not in cls._instances[cls]:
            cls._instances[cls][_id] = super().__call__(*args, **kwargs)

        return cls._instances[cls][_id]


@dataclass(slots=True)
class BaseItem(metaclass=BaseItemMeta):
    _id: str

    _counter: int = None

    __clsmeta = ClsMeta()

    @property
    def id(self):
        return self._id

    def __post_init__(self):
        if self._counter is None:
            self.__get_counter()

    def __get_counter(self):
        self._counter = None
        for i, item in enumerate(Loader.currentLoader.dbContent[self.__clsmeta]):
            if item["id"] == self._id:
                self._counter = i
                break

    @property
    def _raw(self):
        try:
            temp = Loader.currentLoader.dbContent[self.__clsmeta][self._counter]
            if temp["id"] != self._id:
                raise
        except:  # noqa
            self.__get_counter()
            temp = Loader.currentLoader.dbContent[self.__clsmeta][self._counter]

        return temp

    @classmethod
    def all(cls) -> typing.List[typing.Self]:
        items = []
        for i, item in enumerate(
            Loader.currentLoader.dbContent[cls.__name__.lower() + "s"]
        ):
            items.append(cls(_id=item["id"], _counter=i))
        return items

    @classmethod
    def create(cls):
        raise NotImplementedError

    @property
    def createdAtRaw(self):
        return self._raw["createdAt"]

    @createdAtRaw.setter
    def createdAtRaw(self, value):
        with Loader.currentLoader.dbLock():
            self._raw["createdAt"] = value

    @property
    def updatedAtRaw(self):
        return self._raw["updatedAt"]

    @updatedAtRaw.setter
    def updatedAtRaw(self, value):
        with Loader.currentLoader.dbLock():
            self._raw["updatedAt"] = value

    @property
    def createdAt(self):
        return datetime.datetime.fromtimestamp(self.createdAtRaw / 1000)

    @createdAt.setter
    def createdAt(self, value: datetime.datetime):
        self.createdAtRaw = int(value.timestamp() * 1000)

    @property
    def updatedAt(self):
        return datetime.datetime.fromtimestamp(self.updatedAtRaw / 1000)

    @updatedAt.setter
    def updatedAt(self, value: datetime.datetime):
        self.updatedAtRaw = int(value.timestamp() * 1000)

    @property
    def name(self):
        return self._raw["name"]

    @name.setter
    def name(self, value):
        with Loader.currentLoader.dbLock():
            self._raw["name"] = value

    @classproperty
    def properties(self):
        return [
            name
            for name, value in inspect.getmembers(self.__class__)
            if isinstance(value, property)
        ] + ["name", "createdAt", "updatedAt", "id"]

    def delete(self):
        with Loader.currentLoader.dbLock():
            Loader.currentLoader.dbContent[self.__clsmeta].pop(self._counter)

        self.__class__._instances[self.__class__].pop(self._id, None)
        self.__class__._query_cache = {
            cond: res
            for cond, res in self.__class__._query_cache.items()
            if cond[0] != self.__class__
        }
        self.__class__._db_hash = Loader.currentLoader.dbMdate

    @classmethod
    def query(cls, cond, limit=-1) -> typing.List[typing.Self]:
        Loader.currentLoader.dbContent

        if Loader.currentLoader.dbMdate != cls._db_hash:
            cls._query_cache.clear()
            cls._db_hash = Loader.currentLoader.dbMdate

        cached_results = cls._query_cache.get((cls, cond), None)
        if cached_results is not None:
            return cached_results[:]

        matched = []

        for i, item in enumerate(
            Loader.currentLoader.dbContent[cls.__name__.lower() + "s"]
        ):
            if cond(item):
                matched.append(cls(_id=item["id"], _counter=i))

        is_cacheable: typing.Callable[[], bool] = getattr(
            cond, "is_cacheable", lambda: True
        )
        if is_cacheable():
            # Update the query cache
            cls._query_cache[(cls, cond)] = matched

        if limit == -1 or len(matched) <= limit:
            return matched

        return matched[:limit]

    @classmethod
    def queryParse(cls, querystr: str):
        cond = eval(
            querystr.replace("q", f"{cls.__name__}.q"), {f"{cls.__name__}": cls}
        )
        return cls.query(cond)

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self._id}, name={self.name})"

    def __str__(self):
        return self._raw


class Tag(BaseItem):
    q = TagQuery()


class Folder(BaseItem):
    q = FolderQuery()

    @property
    def index(self) -> int:
        return self._raw["index"]

    @index.setter
    def index(self, value):
        with Loader.currentLoader.dbLock():
            self._raw["index"] = value

    @property
    def parentId(self):
        return self._raw["parentId"]

    @parentId.setter
    def parentId(self, value):
        with Loader.currentLoader.dbLock():
            self._raw["parentId"] = value

    @property
    def isOpen(self) -> bool:
        return self._raw["isOpen"]

    @isOpen.setter
    def isOpen(self, value):
        with Loader.currentLoader.dbLock():
            self._raw["isOpen"] = value

    @property
    def isSystem(self) -> bool:
        return self._raw["isSystem"]

    @isSystem.setter
    def isSystem(self, value):
        with Loader.currentLoader.dbLock():
            self._raw["isSystem"] = value

    @property
    def defaultLanguage(self) -> str:
        return self._raw["defaultLanguage"]

    @defaultLanguage.setter
    def defaultLanguage(self, value):
        with Loader.currentLoader.dbLock():
            self._raw["defaultLanguage"] = value

    @property
    def icon(self) -> str:
        return self._raw["icon"]

    @icon.setter
    def icon(self, value):
        with Loader.currentLoader.dbLock():
            self._raw["icon"] = value


class Snippet(BaseItem):
    q = SnippetQuery()

    @property
    def isDeleted(self) -> bool:
        return self._raw["isDeleted"]

    @isDeleted.setter
    def isDeleted(self, value):
        with Loader.currentLoader.dbLock():
            self._raw["isDeleted"] = value

    @property
    def isFavorites(self) -> bool:
        return self._raw["isFavorites"]

    @isFavorites.setter
    def isFavorites(self, value):
        with Loader.currentLoader.dbLock():
            self._raw["isFavorites"] = value

    @property
    def folderId(self) -> str:
        return self._raw["folderId"]

    @folderId.setter
    def folderId(self, value):
        with Loader.currentLoader.dbLock():
            self._raw["folderId"] = value

    @property
    def tagsIds(self) -> typing.List[str]:
        return self._raw["tagsIds"]

    @tagsIds.setter
    def tagsIds(self, value):
        with Loader.currentLoader.dbLock():
            self._raw["tagsIds"] = value

    @property
    def description(self) -> str:
        return self._raw["description"]

    @description.setter
    def description(self, value):
        with Loader.currentLoader.dbLock():
            self._raw["description"] = value

    @property
    def content(self) -> typing.List[Content]:
        return self._raw["content"]

    @content.setter
    def content(self, value):
        with Loader.currentLoader.dbLock():
            self._raw["content"] = value
