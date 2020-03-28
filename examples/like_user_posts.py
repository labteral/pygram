
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pygram import PyGram

pygram = PyGram('user', 'password')

posts = pygram.get_posts('eminem', limit=10)
for post in posts:
    pygram.like(post)