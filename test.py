import os
from masscodeDriver.apploader import AppLoader
from masscodeDriver.datacls import Folder, Snippet, Tag
from masscodeDriver.model import FolderModel
from masscodeDriver.utils import AllMatcher, AnyMatcher, DateContext, FuzzyContext
import cProfile
import pstats #noqa

def init_apploader():
    return AppLoader(os.environ["DB"])

def init_snippets():
    list(Snippet.values())

def query_folder():
    q1 = Folder.query(
        name=FuzzyContext("sprin", justcontains=True), limit=3
    )

    q1= list(q1)
    return q1

def snippet_query_generator():
    
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


def fragment_query():
    init_snippets()
    snippetquery = snippet_query_generator()
    for x in Snippet.fragmentQuery(snippetquery, language="python"):
        print(x["label"])


def get_path():
    init_apploader()
    init_snippets()
    q1 = query_folder()
    w = q1[0].path #noqa

os.makedirs("profile", exist_ok=True)
cProfile.run("get_path()", 'profile/1stats')
cProfile.run("fragment_query()", 'profile/2stats')


