from typing import List, Optional, TypedDict

class FolderModel(TypedDict):
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

class SnippetModel(TypedDict):
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

class TagModel(TypedDict):
    name: str
    createdAt: int
    updatedAt: int
    id: str

class StorageData(TypedDict):
    folders: List[FolderModel]
    tags: List[TagModel]
    snippets: List[SnippetModel]
