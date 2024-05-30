
import io
import os
import typing
import hashlib

class FileCtx(typing.TypedDict):
    sha256 : str
    size : int
    mdate : int
    adate : int

    content : typing.Any

class FileProperty:
    _properties : typing.Dict[str, FileCtx] = {}

    @staticmethod
    def returnIOWrapper(path : str):
        return open(path, 'r+')

    @staticmethod
    def __defaultLoadMethod(path :str):
        with open(path, 'r') as f:
            if path.endswith('.json'):
                import json
                return json.load(f)
            else:
                return f.read()

    @staticmethod
    def __directRead(path : str):
        with open(path, 'rb') as f:
            return f.read()

    def __init__(
        self, 
        path : property, 
        watching : typing.List[typing.Literal["mdate", "adate", "sha256", "size"]] = ["mdate","size", ],
        callback : typing.Callable = None,
        loadmethod : typing.Callable = None
    ):
        self.path = path
        self.watching = watching
        self.callback = callback
        self.loadmethod = loadmethod or FileProperty.__defaultLoadMethod

    def __get__(self, instance, owner):
        if isinstance(self.path, property):
            self.path = self.path.fget(instance)
        
        if not os.path.exists(self.path):
            return None
        
        recordedCtx =self._properties.get(self.path, {})
        
        prepNewCtx = {}

        for item in self.watching:
            if item == "sha256":
                prepNewCtx["sha256"] = hashlib.sha256(self.__directRead(self.path)).hexdigest()
            elif item == "size":
                prepNewCtx["size"] = os.path.getsize(self.path)
            elif item == "mdate":
                prepNewCtx["mdate"] = os.path.getmtime(self.path)
            elif item == "adate":
                prepNewCtx["adate"] = os.path.getatime(self.path)


        if recordedCtx and all(prepNewCtx[x] == recordedCtx[x] for x in self.watching):
            return recordedCtx["content"]
        else:
            recordedContent = recordedCtx.get("content", None)
            if isinstance(recordedContent, io.TextIOWrapper):
                recordedContent.close()

            content = self.loadmethod(self.path)
            prepNewCtx["content"] = content
            self._properties[self.path] = prepNewCtx
            return content
            
