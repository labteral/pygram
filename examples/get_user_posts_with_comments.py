
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pygram import PyGram

pygram = PyGram()

posts = pygram.get_posts('eminem', limit=10)
for post in posts:
    comments = list(pygram.get_comments(post['shortcode'], limit=10))
    post['comments'] = comments
    print(post)