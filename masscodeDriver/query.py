
import typing
from masscodeDriver.driver import MasscodeDriver
from masscodeDriver.tdict import Tag, Snippet, Folder

class Query:
    def __init__(self):
        self.__driver = MasscodeDriver()

    def snippet_via_id(
        self,
        id : str
    ):
        for item in self.__driver.snippets:
            if item["id"] == id:
                return item

    def is_folder_tree(self, folder1: Folder, folder2: Folder) -> bool:
        if folder2['id'] == folder1['id']:
            return True
        current_parent_id = folder2['parentId']
        while current_parent_id:
            parent_folder = next((f for f in self.__driver.folders if f['id'] == current_parent_id), None)
            if parent_folder:
                if parent_folder['id'] == folder1['id']:
                    return True
                current_parent_id = parent_folder['parentId']
            else:
                break
        return False
    
    def folder_via_id(
        self,
        id : str
    ):
        for item in self.__driver.folders:
            if item["id"] == id:
                return item
    
    def tag_via_id(
        self,
        id : str
    ):
        for item in self.__driver.tags:
            if item["id"] == id:
                return item

    def tag(
        self,
        text : str,
        limit : int = 1
    ):
        ret = []
        for item in self.__driver.tags:
            if text in item["name"]:
                ret.append(item)
                if len(ret) >= limit:
                    break

        return ret

    def snippet(
        self,
        text: str = None,
        tags : typing.List[typing.Union[Tag, str]] = [],
        folder : typing.Optional[typing.Union[Folder, str]] = None,
        fav : bool = None,
        deleted : bool = None,
        containLanguages : typing.List[str] = [],
        limit : int =1
    )-> typing.List[Snippet]:
        results = []
        for snippet in self.__driver.snippets:
            # Text match in name or description
            if text is not None:
                if text.lower() not in snippet["name"].lower() or (
                    snippet["description"] is not None and
                    text.lower() not in snippet["description"].lower()
                ):
                    continue
                
            # Tag matching, considering tag via id for direct comparison
            if tags:
                snippet_tags_ids = [self.tag_via_id(tag_id)["id"] for tag_id in snippet["tagsIds"]]
                search_tags_ids = [tag['id'] if isinstance(tag, dict) else tag for tag in tags]
                if not all(tag_id in snippet_tags_ids for tag_id in search_tags_ids):
                    continue

            # Folder match (considering folder trees)
            if folder:
                folder_id = folder['id'] if isinstance(folder, dict) else folder
                snippet_folder = next((f for f in self.__driver.folders if f['id'] == snippet['folderId']), None)
                if not self.is_folder_tree({'id': folder_id}, snippet_folder):
                    continue

            # Favorites filter
            if fav is not None and snippet["isFavorites"] != fav:
                continue

            # Deleted filter
            if deleted is not None and snippet["isDeleted"] != deleted:
                continue

            # Language filter
            if containLanguages and not any(content['language'] in containLanguages for content in snippet['content']):
                continue

            results.append(snippet)
            if len(results) >= limit:
                break

        return results
    

def decorator(func):
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)
        if not res:
            return res
        
        if isinstance(res, list):
            return [dict(item) for item in res]
        elif isinstance(res, dict):
            return dict(res)
        else:
            return res

    return wrapper

class ReadOnlyQuery(Query):
    __funcs__ : typing.ClassVar[typing.Dict[str, typing.Callable]] = {}
    def __getattribute__(self, __name: str) -> typing.Any:
        if __name.startswith("_"):
            return super().__getattribute__(__name)
        
        res = super().__getattribute__(__name)
        if not callable(res):
            return res
        
        if __name not in self.__funcs__:
            self.__funcs__[__name] = decorator(res)
        return self.__funcs__[__name]


