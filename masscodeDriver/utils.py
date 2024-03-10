from dataclasses import dataclass
import datetime
from functools import cached_property
import os
import typing
import uuid
import base64
from thefuzz import fuzz
try:
    import orjson
    orjson_failed =False
except: #noqa
    import json
    orjson_failed = True

def save_json(data, path):
    if orjson_failed:
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    else:
        with open(path, 'wb') as f:
            f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))

def load_json(path):
    if orjson_failed:
        with open(path, 'r') as f:
            return json.load(f)
    else:
        with open(path, 'rb') as f:
            return orjson.loads(f.read())
    

class FileProperty:
    def __init__(self, path, watching=["mdate", "size"]):
        self.path : str = path

        self.watching = {k : None for k in watching}
        self.content = None
        self.checked = False

        self.callback = None
        self.overloadOpen = None

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

class classproperty:
    def __init__(self, getter):
        self.getter = getter

    def __get__(self, instance, owner):
        return self.getter(owner)
    
class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
    


def generate_short_id():
    # Generate a UUID
    unique_uuid = uuid.uuid4()
    
    # Convert the first 6 bytes of the UUID to a base64 string
    # 6 bytes instead of 8 because base64 encoding expands the size by 4/3
    short_base64_id = base64.urlsafe_b64encode(unique_uuid.bytes[:6]).decode('utf-8')
    
    # Trim to 8 characters, removing base64 padding if present
    short_id = short_base64_id.rstrip('=')[:8]
    
    return short_id

def create_timestamp(dt = None):
    if dt is None:
        dt = datetime.datetime.now()

    return int(dt.timestamp() * 1000)

@dataclass(slots=True, frozen=True)
class FuzzyContext:
    query : str
    confidence : float = 0.2
    justcontains : bool = False

    def check(self, query : str):
        if self.justcontains:
            return self.query in query
        
        return fuzz.ratio(self.query, query) >= self.confidence
    
    def check_iter(self, iter : typing.Iterable, limit : int = 1):
        matched = []
        for i in iter:
            if self.check(i):
                matched.append(i)
            
            if limit == 1:
                return i

            if len(matched) >= limit:
                break
                
        return matched

@dataclass(frozen=True)
class DateContext:
    first : typing.Union[datetime.datetime, float, int, str]
    second : typing.Union[datetime.datetime, float, int, datetime.timedelta, str] = None

    def __post_init__(self):
        if isinstance(self.first, str):
            if len(self.first) == 10:
                dt = datetime.datetime.strptime(self.first, "%Y-%m-%d")
            else:
                dt = datetime.datetime.fromisoformat(self.first)
            
            object.__setattr__(self, "first", dt)

        if isinstance(self.second, str):
            if len(self.second) == 10:
                dt = datetime.datetime.strptime(self.second, "%Y-%m-%d")
            else:
                dt = datetime.datetime.fromisoformat(self.second)
        
            object.__setattr__(self, "second", dt)    

        if isinstance(self.first, (int, float)) and self.first >9999999999:
            object.__setattr__(self, "firststampt", self.first)
            object.__setattr__(self, "first", self.first / 1000)
        
        if isinstance(self.second, (int, float)) and self.second >9999999999:
            object.__setattr__(self, "secondstampt", self.second)
            object.__setattr__(self, "second", self.second / 1000)


    @cached_property
    def is_range(self):
        if self.second is None:
            return False
        
        if self.seconddt < self.firstdt:
            return False
        
        return True
    

    def __tstamp(self, t):
        if isinstance(t, datetime.datetime):
            return t.timestamp()

        return t
      
    def __td(self, t):
        if isinstance(t, datetime.datetime):
            return t
        
        if t > 9999999999:
            return datetime.datetime.fromtimestamp(t / 1000)

        return datetime.datetime.fromtimestamp(t)

    @cached_property
    def firststampt(self):
        return int(self.__tstamp(self.first) * 1000)

    @cached_property
    def firstdt(self):
        return self.__td(self.first)

    @cached_property
    def firststamp(self):
        return self.__tstamp(self.first)
    
    @cached_property
    def secondstampt(self):
        return int(self.__tstamp(self.second) * 1000)
    
    @cached_property
    def seconddt(self):
        return self.__td(self.second)
    
    @cached_property
    def secondstamp(self):
        return self.__tstamp(self.second)

    def in_range(self, entry : typing.Union[datetime.datetime, float, int], offset : datetime.timedelta = None):
        if not self.is_range:
            return None
        
        dt = self.__td(entry)

        return (self.firstdt - offset if offset is not None else self.firstdt) <= dt <= (self.seconddt + offset if offset is not None else self.seconddt)

    def is_value(self, entry : typing.Union[datetime.datetime, float, int]):
        return self.firstdt == self.__td(entry)
    
    def is_close(self, entry : typing.Union[datetime.datetime, float, int], offset : datetime.timedelta = datetime.timedelta(hours=1)):
        return self.firstdt - offset <= self.__td(entry) <= self.firstdt + offset

class AnyMatcher(list):
    def __init__(self, *args):
        super().__init__()
        if len(args) == 1 and isinstance(args[0], (set, tuple, list)):
            self.extend(args[0])
        else:
            self.extend(args)


class AllMatcher(list):
    def __init__(self, *args):
        super().__init__()
        if len(args) == 1 and isinstance(args[0], (set, tuple, list)):
            self.extend(args[0])
        else:
            self.extend(args)

def single_match(
    base, 
    compared : typing.Union[typing.Any, FuzzyContext, DateContext, AnyMatcher, AllMatcher]
):
    if isinstance(compared, (str, int, float)) and isinstance(base, (str, int, float)):
        return base == compared

    if isinstance(compared, FuzzyContext):
        return compared.check(base)
    elif isinstance(compared, DateContext) and compared.is_range:
        return compared.in_range(base)
    elif isinstance(compared, DateContext):
        return compared.is_value(base)  

    compared_is_iter = isinstance(compared, (set, list))
    compared_is_prlist =all(isinstance(x, (str, float, int)) for x in compared)

    if not compared_is_iter:
        return base == compared

    is_any = isinstance(compared, AnyMatcher)
    is_all = isinstance(compared, AllMatcher)

    if compared_is_prlist and not is_all:
        if isinstance(base, typing.Iterable) and not isinstance(base, str):
            return any(x in base for x in compared)
        else:
            return base in compared
        
    if compared_is_prlist and is_all:
        return compared[0] == base if not isinstance(base, typing.Iterable) else base == compared

    if is_any:
        return any(single_match(base, x) for x in compared)
    else:
        return all(single_match(base, x) for x in compared)
    

    

def kwargs_match(
    base, 
    getmethod : typing.Callable = lambda x, y: x[y] if isinstance(x, dict) else getattr(x, y),
    limit : int = 1,
    **compared : typing.Dict[str, typing.Union[typing.Any, FuzzyContext, DateContext, AnyMatcher, AllMatcher]]    
):
    if not isinstance(base, typing.Iterator):
        return all(single_match(getmethod(base, k), v) for k, v in compared.items())

    count = 0

    for item in base:

        if all(single_match(getmethod(item, k), v) for k, v in compared.items()):
            yield item

            if limit == 1:
                return

            count += 1

            if limit != -1 and count >= limit:
                break

        
def __return_first(x : typing.Generator):
    try:
        return next(x)
    except StopIteration:
        return None
    
RETURN_FIRST = __return_first