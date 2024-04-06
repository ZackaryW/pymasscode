import os

from pymasscode.etc.utils import load_json

class FileProperty:
    def __init__(
        self, 
        path, 
        watching=["mdate", "size"],
        passOverIoOnly : bool = False
    ):
        self.path : str = path

        self.watching = {k : None for k in watching}
        self.content = None
        self.checked = False

        self.callback = None
        self.overloadOpen = None

        #
        self.passOverIoOnly = passOverIoOnly

    def prep(self):
        if "size" in self.watching:
            self.watching["size"] = os.path.getsize(self.path)
        
        if "mdate" in self.watching:
            self.watching["mdate"] = os.path.getmtime(self.path)

    def __check_path__(self, instance, owner):
        if self.checked:
            return
        
        if callable(self.path):
            self.path = self.path()

        has_self = "{self." in self.path
        has_cls = "{cls." in self.path

        if has_self or has_cls:

            header = self.path.index("{self.")
            footer = self.path.index("}")
            dynpart = self.path[header:footer + 1]

            # convert self.{} into a instance var
            target = self.path[header + 6:footer] if has_self else self.path[header + 5:footer]
            output = {"output" : instance if has_self else owner}
            exec(f"output = output.{target}\n", output)
            
            # replace self.{} with var
            self.path = self.path.replace(dynpart, str(output["output"]))
        
        self.prep()

        self.checked = True

    def watch(self, instance, owner):
        ctx = {}
        if "mdate" in self.watching:
            nmdate = os.path.getmtime(self.path)
            ctx["mdate"] = nmdate
            if ctx["mdate"] != self.watching["mdate"]:
                return True, ctx
        
        if "size" in self.watching:
            csize = os.path.getsize(self.path)
            ctx["size"] = csize
            if ctx["size"] != self.watching["size"]:
                return True, ctx

        return False, ctx

    def __get__(self, instance, owner):
        self.__check_path__(instance, owner)

        if self.passOverIoOnly:
            self.passOverIoOnly = open(self.path, 'r+')
            return self.passOverIoOnly
        
        if self.content is None or (restuple := self.watch(instance, owner))[0]:
            self.reload_file()
            if self.callback:
                self.callback(instance, owner)

        if "restuple" in locals():
            self.watching.update(restuple[1])
        return self.content

    def reload_file(self):
        with open(self.path, 'r') as file:
            if self.path.endswith(".json"):
                self.content = load_json(self.path)
            else:
                self.content = file.read()

    def __call__(self, **kwargs):
        updateMetaNoReload = kwargs.pop("updateMetaNoReload", False)
        if updateMetaNoReload:
            self.prep()

        swapPrepMethod = kwargs.pop("swapPrepMethod", False)
        if swapPrepMethod:
            self.prep = kwargs.pop("prepMethod")
        
        swapCallback = kwargs.pop("swapCallback", False)
        if swapCallback:
            self.callback = kwargs.pop("callback")

    def __del__(self):
        if self.passOverIoOnly:
            self.passOverIoOnly.close()
