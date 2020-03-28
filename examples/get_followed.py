
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pygram import PyGram

pygram = PyGram('user', 'password')

usernames = pygram.get_followed('drdre', limit=10)
for username in usernames:
    print(username)