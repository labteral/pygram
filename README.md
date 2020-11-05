<h1 align="center">
<b>pygram</b>
</h1>

<h3 align="center">
<b>Unofficial Python client for Instagram</b>
</h3>

<p align="center">
    <a href="https://pepy.tech/project/pygram/"><img alt="Downloads" src="https://img.shields.io/badge/dynamic/json?style=flat-square&maxAge=3600&label=downloads&query=$.total_downloads&url=https://api.pepy.tech/api/projects/pygram"></a>
    <a href="https://pypi.python.org/pypi/pygram/"><img alt="PyPi" src="https://img.shields.io/pypi/v/pygram.svg?style=flat-square"></a>
    <!--<a href="https://github.com/brunneis/pygram/releases"><img alt="GitHub releases" src="https://img.shields.io/github/release/brunneis/pygram.svg?style=flat-square"></a>-->
    <a href="https://github.com/brunneis/pygram/blob/master/LICENSE"><img alt="License" src="https://img.shields.io/github/license/brunneis/pygram.svg?style=flat-square&color=green"></a>
</p>

<p align="center">
    <a href="https://www.buymeacoffee.com/brunneis" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="35px"></a>
</p>


## Installation
```bash
pip install pygram
```

## Methods without mandatory login
### Get user's profile
```python
from pygram import PyGram
pygram = PyGram()

profile = pygram.get_profile('eminem')
```

### Get user's ID
```python
from pygram import PyGram
pygram = PyGram()

user_id = pygram.get_user_id('eminem')
```

### Get user's posts
```python
from pygram import PyGram
pygram = PyGram()

posts = pygram.get_posts('eminem', limit=10)
for post in posts:
    print(post)
```

### Get post's comments
```python
from pygram import PyGram
pygram = PyGram()

comments = pygram.get_comments(post, limit=10)
for comment in comments:
    print(comment)
```

## Methods with mandatory login
### Login
```python
from pygram import PyGram

pygram = PyGram('user', 'password')
```
> After the first login, a file with the name `pygram-cache.json` will be created in the current directory to avoid logging in again with every instantiation.

### Get user's followers
```python
from pygram import PyGram
pygram = PyGram('user', 'password')

users = pygram.get_followers('eminem', limit=10)
for user in users:
    print(user)
```

### Get users followed by a user
```python
from pygram import PyGram
pygram = PyGram('user', 'password')

users = pygram.get_followed('drdre', limit=10)
for user in users:
    print(user)
```

### Like a post / comment
```python
from pygram import PyGram
pygram = PyGram('user', 'password')

last_post = next(pygram.get_posts('eminem', limit=1))
pygram.like(last_post)
```

### Unlike a post / comment
```python
from pygram import PyGram
pygram = PyGram('user', 'password')

last_post = next(pygram.get_posts('eminem', limit=1))
pygram.unlike(last_post)
```

### Comment a post / comment
```python
from pygram import PyGram
pygram = PyGram('user', 'password')

pygram.comment(post, 'this is the comment')
```

### Delete a comment
```python
from pygram import PyGram
pygram = PyGram('user', 'password')

pygram.delete(comment)
```
