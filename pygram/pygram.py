#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import time

from .helper import stringify, clean_dict, clean_dicts, is_a_post
from .errors import NotLoggedInError, AuthenticationError, NotSupportedError


class PyGram:

    HEADERS_CACHE_FILE = './pygram-cache.json'

    _endpoints = {
        'web': 'https://www.instagram.com/web/',
        'graphql': 'https://www.instagram.com/graphql/query/',
    }

    def __init__(self,
                 user=None,
                 password=None,
                 sleep_seconds_between_iterative_requests=0):
        self.logged_in = False
        self.headers = None

        if user and password:
            self._login(user, password)

        self.sleep_seconds_between_iterative_requests = sleep_seconds_between_iterative_requests
        self.known_user_ids = {}

    def like(self, publication):
        if 'shortcode' in publication:
            return self._manage_like('post', publication, 'like')
        return self._manage_like('comment', publication, 'like')

    def unlike(self, publication):
        if 'shortcode' in publication:
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
        requests.post(url, data=data, headers=self.headers).json()

    def delete(self, publication):
        if is_a_post(publication):
            raise NotSupportedError
            # publication_id = publication['id']
            # comment_id = ''
        else:
            publication_id = publication['post_id']
            comment_id = f"{publication['id']}/"
        url = f"{PyGram._endpoints['web']}comments/{publication_id}/delete/{comment_id}"
        requests.post(url, headers=self.headers).json()

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
        profile = requests.get(url).json()['graphql']['user']
        cleaned_profile = clean_dict(profile, [
            'id', 'username', 'full_name', 'profile_pic_url',
            'profile_pic_url_hd', 'is_private', 'is_verified', 'biography',
            'external_url', ('followers_count', ['edge_followed_by', 'count']),
            ('followed_count', ['edge_follow', 'count']), 'is_business_account',
            'business_category_name', 'category_id', 'is_joined_recently',
            'overall_category_name', 'connected_fb_page'
        ])
        return cleaned_profile

    def get_posts(self, user, limit=0):
        user_id = self.get_user_id(user)
        variables = {'id': user_id}
        items = self._get_items('472f257a40c653c64c666ce877d59d2b', variables,
                                limit)
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
        items = self._get_items('33ba35852cb50da46f5b5e889df7d159', variables,
                                limit)
        for item in clean_dicts(items, [
                'id', 'text', ('timestamp', 'created_at'),
            ('author', ['owner', 'username'])
        ]):
            item['post_id'] = publication['id']
            yield item

    def get_followed(self, user, limit=0):
        yield from self._get_user_list(user, 'd04b0a864b4b54837c0d870b0e77e076',
                                       limit)

    def get_followers(self, user, limit=0):
        yield from self._get_user_list(user, 'c76146de99bb02f6415203be841dd25a',
                                       limit)

    def _login(self, user, password):
        if self._load_cached_headers():
            return

        session = requests.Session()
        session.headers = {'cookie': 'ig_cb=1'}
        request = session.get('https://www.instagram.com/web/__mid/')
        cookies = request.cookies.get_dict(domain='.instagram.com')
        session.headers.update({'x-csrftoken': cookies['csrftoken']})
        data = {'username': user, 'password': password}
        request = session.post('https://www.instagram.com/accounts/login/ajax/',
                               data=data,
                               allow_redirects=True)
        cookies = request.cookies.get_dict(domain='.instagram.com')
        try:
            self.headers = {
                'x-csrftoken':
                cookies['csrftoken'],
                'cookie':
                f"csrftoken={cookies['csrftoken']};sessionid={cookies['sessionid']}",
            }
            self._cache_headers()
            self.logged_in = True
        except KeyError:
            raise AuthenticationError

    def _load_cached_headers(self):
        try:
            with open(PyGram.HEADERS_CACHE_FILE, 'r') as input_file:
                self.headers = json.load(input_file)
                self.logged_in = True
                return True
        except FileNotFoundError:
            return False

    def _cache_headers(self):
        with open(PyGram.HEADERS_CACHE_FILE, 'w') as output_file:
            json.dump(self.headers, output_file)

    def _get_items(self, query_hash, variables, limit):
        variables['first'] = limit if limit and limit < 50 else 50
        yielded_items = 0
        has_next_page = True
        done = False
        while has_next_page and not done:
            stringified_variables = stringify(variables)
            url = f"{PyGram._endpoints['graphql']}?query_hash={query_hash}&variables={stringified_variables}"
            data = requests.get(url, headers=self.headers).json()['data']
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
            time.sleep(self.sleep_seconds_between_iterative_requests)

    def _get_user_list(self, user, query_hash, limit):
        if not self.logged_in:
            raise NotLoggedInError

        user_id = self.get_user_id(user)
        variables = {
            'id': user_id,
            'include_reel': False,
            'fetch_mutual': False
        }

        items = self._get_items(query_hash, variables, limit)
        yield from clean_dicts(items, [
            'id', 'username', 'full_name', 'profile_pic_url', 'is_private',
            'is_verified'
        ])

    def _manage_like(self, content_type, item, action):
        item_id = item['id']
        if content_type == 'post':
            url = f"{PyGram._endpoints['web']}likes/{item_id}/{action}/"
        elif content_type == 'comment':
            url = f"{PyGram._endpoints['web']}comments/{action}/{item_id}/"
        requests.post(url, headers=self.headers).json()