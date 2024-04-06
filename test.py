
from pymasscode.dcls import Snippet


w = Snippet.query(Snippet.q.name == "pypi upload", limit =1)
script = w[0].content[0]["value"]
exec(script)
pass