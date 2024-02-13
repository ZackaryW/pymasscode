from typing import List, Optional, TypedDict

class Folder(TypedDict):
    name: str
    index: int
    parentId: Optional[str]
    defaultLanguage: str
    isOpen: bool
    isSystem: bool
    createdAt: int
    updatedAt: int
    id: str

class Content(TypedDict):
    label: str
    language: str
    value: str

class Snippet(TypedDict):
    name: str
    description: Optional[str]
    isDeleted: bool
    isFavorites: bool
    folderId: str
    createdAt: int
    updatedAt: int
    tagsIds: List[str]
    content: List[Content]
    id: str

class Tag(TypedDict):
    name: str
    createdAt: int
    updatedAt: int
    id: str

class StorageData(TypedDict):
    folders: List[Folder]
    tags: List[Tag]
    snippets: List[Snippet]