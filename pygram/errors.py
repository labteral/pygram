#!/usr/bin/env python
# -*- coding: utf-8 -*-


class NotLoggedInError(Exception):
    pass


class AuthenticationError(Exception):
    pass


class NotSupportedError(Exception):
    pass


class ActionError(Exception):
    pass


class UnknownError(Exception):
    pass
