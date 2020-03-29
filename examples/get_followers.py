
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pygram import PyGram

pygram = PyGram('user', 'password')

users = pygram.get_followers('eminem', limit=10)
for user in users:
    print(user)