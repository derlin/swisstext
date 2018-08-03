# Swisstext Mongo

This package contains common definitions of the MongoDB collections used as part of the SwissText project,
namely:

* _swisstext-cmd_: commandline scripts for scraping Swiss German sentences on the web,
* _swisstext-frontend_: website for managing and validating the generated corpus

## Installation

1. clone the repository
2. run `python setup.py install`

## Collections

The available collections are:

* `seeds`: the keywords used to search for new URLs using a search engine,
* `sentences`: the Swiss-German sentences found,
* `urls`: the URLs clawled so far that contained _at least one_ Swiss German sentence,
* `blacklist`: all other URLs crawled,
* `users`: the users and their roles (for the frontend)

## About the code

This package is required by two different projects: _swisstext-cmd_ uses MongoEngine,
_swisstext-frontend_ uses _Flask-Mongoengine_. The only way I found to make classes reusable by both
is described in [this issue](https://github.com/MongoEngine/flask-mongoengine/issues/309).

In short, the package `swisstext.mongo.abstract` defined "regular" MongoEngine documents, but also set
the meta flag `abstract` to `True`. Thus, they cannot be used as-is.

When using __MongoEngine__, just subclass each abstract class, as done in `swisstext.mongo.models`:

```python
from swisstext.mongo.abstract import AbstractMongoURL
class MongoURL(AbstractMongoURL):
    pass
```

When using __Flask-Mongoengine__, do the same, but use a mixin:

```python
from flask_mongoengine import MongoEngine
db = MongoEngine()

from swisstext.mongo.abstract import AbstractMongoURL

class MongoURL(db.Document, AbstractMongoURL):
    pass
```

