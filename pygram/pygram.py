#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import time
from random import randint
from .helper import (get_json_from_url, stringify, clean_dict, clean_dicts, is_a_post)
from .errors import (NotLoggedInError, AuthenticationError, NotSupportedError, UnknownError, ActionError)


class PyGram:

    HEADERS_CACHE_FILE = './pygram-cache.json'

    _endpoints = {
        'web': 'https://www.instagram.com/web/',
        'graphql': 'https://www.instagram.com/graphql/query/',
    }

    def __init__(self, user=None, password=None, seconds_between_iterations=None):
        self.user = user
        self.seconds_between_iterations = seconds_between_iterations
        self.known_user_ids = {}
        self.logged_in = False
        self.headers = None

        if user and password:
            self._login(user, password)

    def like(self, publication):
        if is_a_post(publication):
            return self._manage_like('post', publication, 'like')
        return self._manage_like('comment', publication, 'like')

    def unlike(self, publication):
        if is_a_post(publication):
            return self._manage_like('post', publication, 'unlike')
        return self._manage_like('comment', publication, 'unlike')

    def comment(self, publication, text):
        data = {'comment_text': text}
        if is_a_post(publication):
            publication_id = publication['id']
        else:
            publication_id = publication['post_id']
            data['replied_to_comment_id'] = publication['id']
        url = f"{PyGram._endpoints['web']}comments/{publication_id}/add/"
        return get_json_from_url(url, 'post', data=data, headers=self.headers)

    def delete(self, publication):
        if is_a_post(publication):
            raise NotSupportedError
            # publication_id = publication['id']
            # comment_id = ''
        else:
            publication_id = publication['post_id']
            comment_id = f"{publication['id']}/"
        url = f"{PyGram._endpoints['web']}comments/{publication_id}/delete/{comment_id}"
        return get_json_from_url(url, 'post', headers=self.headers)

    def get_user_id(self, user):
        if user in self.known_user_ids:
            user_id = self.known_user_ids[user]
        else:
            user_id = PyGram.get_profile(user)['id']
            self.known_user_ids[user] = user_id
        return user_id

    @staticmethod
    def get_profile(user):
        url = f'https://www.instagram.com/{user}/?__a=1'
        method = 'get'
        try:
            profile = get_json_from_url(url, method)['graphql']['user']
        except KeyError:
            raise ActionError(f'[{method.upper()}] {url}')

        cleaned_profile = clean_dict(profile, [
            'id', 'username', 'full_name', 'profile_pic_url', 'profile_pic_url_hd', 'is_private', 'is_verified',
            'biography', 'external_url', ('followers_count', ['edge_followed_by', 'count']),
            ('followed_count', ['edge_follow', 'count']), 'is_business_account', 'business_category_name',
            'category_id', 'is_joined_recently', 'overall_category_name', 'connected_fb_page'
        ])
        return cleaned_profile

    def get_posts(self, user, limit=0):
        user_id = self.get_user_id(user)
        variables = {'id': user_id}
        items = self._get_items('472f257a40c653c64c666ce877d59d2b', variables, limit)
        yield from clean_dicts(items, [
            'id',
            'shortcode',
            'comments_disabled',
            ('comments_count', ['edge_media_to_comment', 'count']),
            ('timestamp', 'taken_at_timestamp'),
            'display_url',
            ('likes_count', ['edge_media_preview_like', 'count']),
            ('author', ['owner', 'id']),
            'video_url',
            ('video_views_count', 'video_view_count'),
            'is_video',
            ('caption', ['edge_media_to_caption', 'edges', 0, 'node', 'text']),
            'caption_is_edited',
            'location',
        ])

    def get_comments(self, publication, limit=0):
        variables = {'shortcode': publication['shortcode']}
        items = self._get_items('33ba35852cb50da46f5b5e889df7d159', variables, limit)
        for item in clean_dicts(items, ['id', 'text', ('timestamp', 'created_at'), ('author', ['owner', 'username'])]):
            item['post_id'] = publication['id']
            yield item

    def get_followed(self, user, limit=0):
        yield from self._get_user_list(user, 'd04b0a864b4b54837c0d870b0e77e076', limit)

    def get_followers(self, user, limit=0):
        yield from self._get_user_list(user, 'c76146de99bb02f6415203be841dd25a', limit)

    def _login(self, user, password):
        if self._load_cached_headers():
            return

        headers = {'cookie': 'ig_cb=1'}
        request = requests.get('https://www.instagram.com/', headers=headers)
        cookies = request.cookies.get_dict(domain='.instagram.com')
        headers.update({'x-csrftoken': cookies['csrftoken']})
        data = {'username': user, 'password': password}

        request = requests.post('https://www.instagram.com/accounts/login/ajax/', data=data, headers=headers)
        if request.status_code != 200:
            raise AuthenticationError

        cookies = request.cookies.get_dict(domain='.instagram.com')
        if 'sessionid' not in cookies or 'csrftoken' not in cookies:
            raise AuthenticationError

        self.headers = {
            'x-csrftoken': cookies['csrftoken'],
            'cookie': f"csrftoken={cookies['csrftoken']};sessionid={cookies['sessionid']}",
        }
        self._cache_headers()
        self.logged_in = True

    def _load_cached_headers(self):
        try:
            with open(PyGram.HEADERS_CACHE_FILE, 'r') as input_file:
                cache = json.load(input_file)
                if cache['user'] != self.user:
                    return False
                self.headers = cache['headers']
                try:
                    self.logged_in = True
                    next(self.get_followers('instagram', limit=1))
                    return True
                except StopIteration:
                    self.logged_in = False
                    return False
        except FileNotFoundError:
            return False

    def _cache_headers(self):
        with open(PyGram.HEADERS_CACHE_FILE, 'w') as output_file:
            cache = {'user': self.user, 'headers': self.headers}
            json.dump(cache, output_file)

    def _assert_logged_in(self):
        if not self.logged_in:
            raise NotLoggedInError

    def _get_user_list(self, user, query_hash, limit):
        self._assert_logged_in()

        user_id = self.get_user_id(user)
        variables = {'id': user_id, 'include_reel': False, 'fetch_mutual': False}

        items = self._get_items(query_hash, variables, limit)
        yield from clean_dicts(items, ['id', 'username', 'full_name', 'profile_pic_url', 'is_private', 'is_verified'])

    def _get_items(self, query_hash, variables, limit):
        variables['first'] = limit if limit and limit < 50 else 50
        yielded_items = 0
        has_next_page = True
        done = False
        while has_next_page and not done:
            stringified_variables = stringify(variables)
            url = f"{PyGram._endpoints['graphql']}?query_hash={query_hash}&variables={stringified_variables}"
            method = 'get'
            try:
                data = get_json_from_url(url, method, headers=self.headers)['data']
            except KeyError:
                raise ActionError(f'[{method.upper()}] {url}')

            for i in range(2):
                data = data[list(data.keys())[0]]

            page_info = data['page_info']
            nodes = [node['node'] for node in data['edges']]

            for node in nodes:
                yield node
                yielded_items += 1
                if yielded_items == limit:
                    done = True
                    break

            has_next_page = page_info['has_next_page']
            variables['after'] = page_info['end_cursor']

            if self.seconds_between_iterations is None:
                seconds_between_iterations = randint(1, 5)
            else:
                seconds_between_iterations = self.seconds_between_iterations
            time.sleep(seconds_between_iterations)

    def _manage_like(self, content_type, item, action):
        item_id = item['id']
        if content_type == 'post':
            url = f"{PyGram._endpoints['web']}likes/{item_id}/{action}/"
        elif content_type == 'comment':
            url = f"{PyGram._endpoints['web']}comments/{action}/{item_id}/"
        return get_json_from_url(url, 'post', headers=self.headers)