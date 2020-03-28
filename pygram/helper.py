#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json


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
                    new_item[key_name] = new_item[key_name][subkey]

    return new_item


def clean_dicts(items, keys):
    for item in items:
        yield clean_dict(item, keys)

def is_a_post(publication):
    return 'shortcode' in publication