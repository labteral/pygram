#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import requests
from .errors import ActionError


def get_json_from_url(url, method, data=None, headers=None):
    try:
        result = getattr(requests, method)(url, data=data, headers=headers)
        result_dict = result.json()
        if method == 'post' and result_dict['status'] != 'ok':
            raise ActionError(f'[{method.upper()}] {url}')
        return result_dict
    except json.decoder.JSONDecodeError:
        raise ActionError(f'[{method.upper()}] {url}')


def stringify(input_dict):
    return json.dumps(input_dict, separators=(',', ':'))


def clean_dict(item, keys):
    new_item = {}
    for key in keys:
        if isinstance(key, str) and key in item:
            new_item[key] = item[key]

        elif isinstance(key, tuple):
            key_name, subkeys = key
            if not isinstance(subkeys, list):
                subkeys = [subkeys]

            first_subkey = subkeys[0]
            if first_subkey not in item:
                continue
            new_item[key_name] = item[first_subkey]
            if len(subkeys) > 1:
                for subkey in subkeys[1:]:
                    try:
                        new_item[key_name] = new_item[key_name][subkey]
                    except Exception:
                        pass
    return new_item


def clean_dicts(items, keys):
    for item in items:
        yield clean_dict(item, keys)


def is_a_post(publication):
    return 'shortcode' in publication