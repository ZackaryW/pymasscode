
from masscodeDriver.apploader import AppLoader
import os
from masscodeDriver.datacls import Snippet

from masscodeDriver.utils import RETURN_FIRST

AppLoader(os.environ["DB"])

snippetfrag =RETURN_FIRST(
    Snippet.fragmentQuery(folder="python",name="pypi upload",language="python"))

exec(snippetfrag["value"])

pass