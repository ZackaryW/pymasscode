from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import cached_property
from types import MappingProxyType
from typing import Any, Generator
import typing
from masscodeDriver.apploader import Shortcut
from masscodeDriver.model import Content, FolderModel, SnippetModel, TagModel
from masscodeDriver.utils import (
    AllMatcher,
    AnyMatcher,
    FileProperty,
    classproperty,
    create_timestamp,
    generate_short_id,
    kwargs_match,
    save_json,
    single_match,
)


class MasscodeDataMeta(type):
    __cached: dict = FileProperty(lambda: Shortcut.lazyLoader.dbPath)
    __tags = {}
    __snippets = {}
    __folders = {}

    REFLECT_FILE_CHANGE = True

    @classproperty
    def cached(cls):
        return MappingProxyType(cls.__cached)

    def __call__(cls, id: str = ..., name: str = ..., **kwargs) -> Any:
        if name is ... and id is ...:
            raise ValueError("name or id is required")

        if cls == Tag:
            target = cls.__tags
        elif cls == Snippet:
            target = cls.__snippets
        elif cls == Folder:
            target = cls.__folders

        if len(kwargs) == 0 and name is ...:
            return target[id]

        if (
            not hasattr(cls, "__inited_tags_folders__")
            and (len(cls.__tags) == 0 or len(cls.__folders) == 0)
            and (len(cls.__cached["folders"]) != 0 or len(cls.__cached["tags"]) != 0)
        ):
            cls.__inited_tags_folders__ = True
            list(Interface.values(Folder))
            list(Interface.values(Tag))

        if isinstance(name, tuple):
            for item in target.values():
                if item.name == name[0]:
                    return item

            return None

        if id is ...:
            raise ValueError("id is required")

        if id in target:
            item = target[id]
            item.update(**kwargs)

        else:
            item = super().__call__(id=id, name=name, **kwargs)
            target[id] = item
        return item
    
    @contextmanager
    def __saving_logic__(cls, instance : "Interface"):
        if not cls.REFLECT_FILE_CHANGE:
            yield

        try:
            if not hasattr(cls, "__save_logic_counter__"):
                cls.__save_logic_counter__ = 0

            cls.__save_logic_counter__ += 1
            yield

        finally:
            if cls.__save_logic_counter__ > 1:
                cls.__save_logic_counter__ -= 1
                return

            cls.__cached[f"{instance.__class__.__name__.lower()}s"][instance.nindex(instance.id)] = instance.toDict()
            save_json(cls.__cached, Shortcut.lazyLoader.dbPath)

@dataclass
class Interface(metaclass=MasscodeDataMeta):
    id: str = field()
    name: str = field()
    createdAt: int = field()
    updatedAt: int = field()
    __disallowed_update_list__: typing.ClassVar[typing.List[str]] = ["id", "createdAt"]

    def __post_init__(self):
        self.__inited = True

    @classmethod
    def nindex(cls, id: str):
        data: dict = cls._MasscodeDataMeta__cached
        for i, item in enumerate(data[f"{cls.__name__.lower()}s"]):
            if item["id"] == id:
                index = i
                break

        return index


    def __setattr__(self, __name: str, __value: Any) -> None:
        if not hasattr(self, "_Interface__inited"):
            return object.__setattr__(self, __name, __value)

        if __value == getattr(self, __name, None):
            return

        if hasattr(self, __name) and __name in self.__disallowed_update_list__:
            raise AttributeError(f"{__name} is disallowed to be changed.")

        if (
            self._Interface__inited
            and __name not in self.__class__.__dataclass_fields__
        ):
            raise AttributeError(f"{__name} is not a valid field.")

        with self.__class__.__saving_logic__(self):
            object.__setattr__(self, __name, __value)

    @classmethod
    def values(cls, __type: type) -> typing.Generator[Any, Any, None]:
        for value in cls.__class__.cached.get(f"{__type.__name__.lower()}s"):
            yield __type(**value)

    @classmethod
    def query(
        cls, limit: int = -1, **kwargs
    ) -> typing.Union[
        typing.List["Interface"], typing.Generator["Interface", None, None]
    ]:
        target_dict: dict = getattr(
            cls.__class__, f"_MasscodeDataMeta__{cls.__name__.lower()}s"
        )

        if len(target_dict) == 0:
            for _ in Interface.values(cls):
                pass

        if len(target_dict) == 0:
            return None if limit == 1 else []

        if len(kwargs) == 0:
            if limit == -1:
                return list(target_dict.values())
            return list(target_dict.values())[:limit]

        return kwargs_match(iter(target_dict.values()), limit=limit, **kwargs)

    def toDict(self):
        ret = {}
        for key in self.__class__.__dataclass_fields__:
            val = getattr(self, key)
            if val == self.__class__.__dataclass_fields__[key].default:
                continue

            if key.startswith("_"):
                continue

            ret[key] = val

        return ret

    def update(self, **kwargs):
        if self == kwargs:
            return

        with self.__class__.__saving_logic__(self):
            for k, v in kwargs.items():
                setattr(self, k, v)

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, self.__class__):
            return self.toDict() == __value.toDict()
        elif isinstance(__value, dict):
            return self.toDict() == __value

        return False

    def __generate_till_valid_id(cls):
        while True:
            id = generate_short_id()
            if id not in cls.__class__.cached[f"{cls.__name__.lower()}s"]:
                return id

    @classmethod
    def create(cls, name: str, **kwargs):
        # drop none
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        uid = cls.__generate_till_valid_id()
        if "createdAt" not in kwargs:
            kwargs["createdAt"] = create_timestamp()

        if "updatedAt" not in kwargs:
            kwargs["updatedAt"] = create_timestamp()

        ins = cls(id=uid, name=name, **kwargs)

        # modify and save
        cls.__class__._MasscodeDataMeta__cached[f"{cls.__name__.lower()}s"].append(
            ins.toDict()
        )
        save_json(cls.__class__._MasscodeDataMeta__cached, Shortcut.lazyLoader.dbPath)
        cls.__class__._MasscodeDataMeta__cached(updateMetaNoReload=True)
        return ins

    @classmethod
    def delete(cls, item: typing.Union[str, "Interface"]):
        if isinstance(item, str):
            item = cls(item)

        for i, x in enumerate(
            cls.__class__._MasscodeDataMeta__cached[f"{cls.__name__.lower()}s"]
        ):
            if x["id"] == item.id:
                cls.__class__._MasscodeDataMeta__cached[f"{cls.__name__.lower()}s"].pop(
                    i
                )
                break

        save_json(cls.__class__._MasscodeDataMeta__cached, Shortcut.lazyLoader.dbPath)
        cls.__class__._MasscodeDataMeta__cached(updateMetaNoReload=True)

    def __del__(self):
        self.delete(self)
        super().__del__()


@dataclass
class Tag(Interface):
    @classmethod
    def values(cls) -> typing.Generator["Tag", None, None]:
        return Interface.values(cls)

    @classmethod
    def create(cls, name: str, createdAt: int = None, updatedAt: int = None):
        return super().create(name, createdAt=createdAt, updatedAt=updatedAt)

    @classmethod
    def query(cls, limit: int = -1, **kwargs: typing.Unpack[TagModel]) -> typing.Generator["Tag", None, None]:
        return super().query(limit, **kwargs)


@dataclass
class Folder(Interface):
    index: int = field()
    parentId: str = None
    isOpen: bool = False
    isSystem: bool = False
    defaultLanguage: str = "plain_text"
    icon: str = None

    @property
    def parent(self):
        return Folder(self.parentId) if self.parentId else None

    @classmethod
    def values(cls) -> typing.Generator["Folder", None, None]:
        return Interface.values(cls)
    
    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name == "parentId":
            self.__dict__.pop("path", None)

        return super().__setattr__(__name, __value)

    @cached_property
    def path(self):
        if self.parent:
            return [self] + self.parent.path

        return [self]

    @classmethod
    def create(
        cls,
        name: str,
        index: int = None,
        parentId: str = None,
        isOpen: bool = None,
        isSystem: bool = None,
        defaultLanguage: str = None,
        icon: str = None,
    ):
        return super().create(
            name,
            index=index,
            parentId=parentId,
            isOpen=isOpen,
            isSystem=isSystem,
            defaultLanguage=defaultLanguage,
            icon=icon,
        )

    @classmethod
    def query(cls, limit: int = -1, path =None, **kwargs: typing.Unpack[FolderModel]):    
        return super().query(limit, **kwargs)


@dataclass
class Snippet(Interface):
    isDeleted: bool = False
    isFavorites: bool = False
    folderId: str = None
    tagsIds: typing.List[str] = field(default_factory=list)
    description: str = None
    content: typing.List[Content] = field(default_factory=list)

    
    @classmethod
    def values(cls) -> typing.Generator["Snippet", None, None]:
        return Interface.values(cls)

    @property
    def folder(self):
        if not self.folderId:
            return None
        return Folder(self.folderId)

    @folder.setter
    def folder(self, value: typing.Union[Folder, str]):
        if not isinstance(value, Folder):
            value = Folder(value)

        self.folderId = value.id

    @property
    def tags(self):
        return [Tag(x) for x in self.tagsIds]

    @tags.setter
    def tags(self, value: typing.Union[Tag, str, typing.List[typing.Union[Tag, str]]]):
        if not isinstance(value, list):
            value = [value]

        for x in value:
            if not isinstance(x, Tag):
                x = Tag(x)

        self.tagsIds = [x.id for x in value]

    @classmethod
    def create(
        cls,
        name: str,
        isDeleted: bool = None,
        isFavorites: bool = None,
        folder: typing.Union[Folder, str] = None,
        tags: typing.Union[Tag, str, typing.List[typing.Union[Tag, str]]] = None,
        description: str = None,
        content: typing.List[Content] = [
            Content(label="Fragment 1", language="plain_text", value=""),
        ],
    ):
        return super().create(
            name,
            isDeleted=isDeleted,
            isFavorites=isFavorites,
            folder=folder,
            tags=tags,
            description=description,
            content=content,
        )

    def __getitem__(self, key):
        return self.content[key]

    def __setitem__(self, key, value: Content):
        for k in value:
            if k not in Content.__annotations__:
                raise ValueError(f"{k} not in {Content.__annotations__}")

        self.content[key] = value
        data = self.__class__._MasscodeDataMeta__cached
        data[f"{self.__class__.__name__.lower()}s"][self.nindex(self.id)] = self.toDict()
        save_json(data, Shortcut.lazyLoader.dbPath)

    @classmethod
    def query(
        cls,
        limit: int = -1,
        folder=None,
        tag=None,
        folder_match_type: typing.Literal["any", "all"] = "any",
        tag_match_type: typing.Literal["any", "all"] = "any",
        **kwargs: typing.Unpack[SnippetModel],
    ):
        if folder is not None:
            if isinstance(folder, typing.Generator):
                matched_folders = iter(folder)
            elif isinstance(folder, dict):
                matched_folders = Folder.query(**folder)
            elif isinstance(folder, Folder):
                matched_folders = [folder]
            elif isinstance(folder, str):
                matched_folders = Folder.query(name=folder)
            elif isinstance(folder, typing.Iterable) and all(
                isinstance(x, Folder) for x in folder
            ):
                matched_folders = list(folder)
            elif isinstance(folder, typing.Iterable) and all(
                isinstance(x, str) for x in folder
            ):
                matched_folders = Folder.query(name=AllMatcher(folder))
            else:
                raise TypeError(f"unsupported type {type(folder)}")

            if folder_match_type == "any":
                kwargs["folderId"] = AnyMatcher([x.id for x in matched_folders])
            else:
                kwargs["folderId"] = AllMatcher([x.id for x in matched_folders])

        if tag is not None:
            if isinstance(tag, typing.Generator):
                matched_tags = iter(tag)
            elif isinstance(tag, dict):
                matched_tags = Tag.query(**tag)
            elif isinstance(tag, Tag):
                matched_tags = Tag.query(name=tag)
            elif isinstance(tag, str):
                matched_tags = [Tag.query(name=tag)]
            elif isinstance(tag, typing.Iterable) and all(
                isinstance(x, Tag) for x in tag
            ):
                matched_tags = list(tag)
            elif isinstance(tag, typing.Iterable) and all(
                isinstance(x, str) for x in tag
            ):
                matched_tags = Tag.query(name=AllMatcher(tag))
            else:
                raise TypeError(f"unsupported type {type(tag)}")

            if tag_match_type == "any":
                kwargs["tagsIds"] = AnyMatcher([x.id for x in matched_tags])
            else:
                kwargs["tagsIds"] = AllMatcher([x.id for x in matched_tags])

        return super().query(limit, **kwargs)

    @classmethod
    def fragmentQuery(cls, 
        gen : typing.Generator['Snippet', None, None] = None,
        limit: int = -1, 
        label : str = None,
        language : str = None,
        text : str = None,
        **kwargs: typing.Unpack[SnippetModel]
    ) -> Generator[Content, None, None]:
        if gen is None:
            gen = cls.query(**kwargs)

        for i, item in enumerate(gen):
            item : Snippet
            count = 0
            for fragment in item.content:
                if label is not None and not single_match(fragment["label"], label):
                    continue

                if language is not None and not single_match(fragment["language"], language):
                    continue

                if text is not None and not single_match(fragment["value"], text):
                    continue
                    
                if limit == 1:
                    return fragment
                
                count += 1

                yield fragment

                if limit != -1 and count >= limit:
                    break