# Masscode Driver
Middleware for interacting with MassCode database

## Installation
You must have masscode installed in order for it to work properly

### Windows Machine
to install masscode, either use `scoop install masscode` or `choco install masscode` if you have scoop/choco

OR see https://masscode.io/

### Package
```bash
pip install masscode-driver
```

## Usage

to initialize
```py
from masscodeDriver import AppLoader

AppLoader({path})
```

### query
to query tags with date range (DateContext available in utils)
```py
generator = Tag.query(
    createdAt=DateContext("2023-01-01", "2023-12-31")
)

for tag in generator:
    print(tag.name)
```

This example demonstrates how to use subqueries
```py
generator = Snippet.query(
    folder=FolderModel( # you can either pass a dict model
        name=AnyMatcher(
            FuzzyContext("python", justcontains=True),
        )
    ),
    tag=Tag.query(name=AnyMatcher(FuzzyContext("a", justcontains=True))), # or pass a generator
)
```

the following code returns a generator, here demonstrates subqueries can also be nested
```py
return Snippet.query(
    folder=FolderModel(
        name=AnyMatcher(
            FuzzyContext("data", justcontains=True),
            FuzzyContext("swing", justcontains=True),
            AnyMatcher(
                "projects", "qt"
            )
        )
    )
)
```

## Example
if the db contains a snippet called "pypi upload"
I can use it to setup this package
```py

from masscodeDriver.apploader import AppLoader
import os
from masscodeDriver.datacls import Snippet
from masscodeDriver.utils import RETURN_FIRST

AppLoader(os.environ["DB"])

snippetfrag =RETURN_FIRST(
    Snippet.fragmentQuery(folder="python",name="pypi upload",language="python"))

exec(snippetfrag["value"])

```

> here is the script
```
import os
import sys
import shutil
from keyring.backends.Windows import WinVaultKeyring

if not os.path.exists("setup.py"):
    print("No setup.py found")
    sys.exit(1)

if os.path.exists(os.path.join(os.getcwd(), "presetup.py")):
    os.system("python presetup.py")

keyring = WinVaultKeyring()

# build if not exist
if not os.path.exists("dist"):
    os.system("python -m build")
# check
if not os.path.exists("dist"):
    print("No dist folder found, please run python setup.py sdist")
    sys.exit(1)

# check dist
os.system("twine check dist/*")

# upload
token = keyring.get_password("PYPI_TOKEN", "__user__")

if token is None:
    print("No PYPI_TOKEN found")
    sys.exit(1)

os.system(f"twine upload dist/* -u __token__ -p {token}")

# clean
shutil.rmtree("dist")

```
