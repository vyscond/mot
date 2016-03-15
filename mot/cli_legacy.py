import os
import sys
import glob
import argparse
import collections
import json
import jinja2
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler

import misaka as m
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name

DESCRIPTION = 'Just an ordinary static blog engine'

BASE_PATH = os.path.abspath('.')
POSTS_PATH = os.path.join(BASE_PATH, '_posts')
THEMES_PATH = os.path.join(BASE_PATH, '_themes')
DIST_PATH = os.path.join(BASE_PATH, 'dist')
THEME_STATICS = 'bower_components'

POST_TEMPLATE = '''
title: {title}
author: {author}
date: {date}
slug: {slug}
tags: {tags}
---

# My name is bond

james bond! ;)
'''

def get_config():
    return json.load(
        open(os.path.join(BASE_PATH, 'config.json')), 
        object_pairs_hook=collections.OrderedDict
    )

def tinymatter(md):
    meta, md = md.split('---')
    post = {}
    for entry in meta.split('\n'):
        slc = entry.find(':')
        key = entry[:slc]
        val = entry[slc+1:]
        post[key.strip()] = val.strip()
    post['body'] = {}
    post['body']['md'] = md
    return post

def render_markdown(md):
    return m.Markdown(CodeHighlighterRenderer(), extensions=('fenced-code',))(md)

def get_post(path):
    with open(path) as f:
        post = tinymatter(f.read())
    return post

def get_all_posts():
    paths = [ os.path.join(POSTS_PATH, fname) for fname in os.listdir(POSTS_PATH)] 
    return list(map(get_post, paths))

class CodeHighlighterRenderer(m.HtmlRenderer):
    def blockcode(self, text, lang):
        if not lang:
            return '\n<pre><code>{}</code></pre>\n'.format(text.strip())
        lexer = get_lexer_by_name(lang, stripall=True)
        formatter = HtmlFormatter()
        return highlight(text, lexer, formatter)

class InitAction(argparse.Action):
    def __init__(self, **kwargs):
        super(InitAction, self).__init__(**kwargs)

    def __call__(self, parser, namespace, values, option_strings=None):
        print('{} {} {}'.format(namespace, values, option_strings))
        cfg = collections.OrderedDict()
        cfg['sitename'] = input('site name>') or 'Untitled'
        cfg['payoff'] = input('site payoff>') or 'Payoff'
        cfg['author'] = input('site owner>') or 'anonymuse'
        cfg['theme'] = input('theme>') or 'default'
        cfg['github'] = 'https://github.com/'.format(input('github>'))
        cfg['twitter'] = 'https://twitter.com/'.format(input('twitter>'))
        with open(os.path.join(BASE_PATH, 'config.json'), 'w') as f:
            dump = json.dumps(cfg, indent=4)
            f.write(dump)
        # - Folders
        os.makedirs(POSTS_PATH, exist_ok=True)
        os.makedirs(THEMES_PATH, exist_ok=True)
        os.makedirs(DIST_PATH, exist_ok=True)

class BuildAction(argparse.Action):
    def __init__(self, **kwargs):
        super(BuildAction, self).__init__(**kwargs)
    
    def __call__(self, parser, namespace, values, option_strings=None):
        self.theme_path = os.path.join(THEMES_PATH, get_config()['theme'])
        self.theme_templates_path = os.path.join(self.theme_path, 'templates')
        loader = jinja2.FileSystemLoader(self.theme_templates_path)
        self.theme_env = jinja2.Environment(loader=loader)
        self.posts = get_all_posts()
        # - Two basic templates
        self.render_posts()
        self.render_index()
        # - Alternative pages
        self.render_extras()
        self.copying_statics()

    def render_posts(self):
        dist_post_base_path = os.path.join(DIST_PATH, 'post')
        os.makedirs(dist_post_base_path , exist_ok=True)
        for post in self.posts:
            post['body']['html'] = render_markdown(post['body']['md'])
            post['href'] = os.path.join('post', post['slug']) + '.html'
            path = os.path.join(dist_post_base_path, post['slug']) + '.html'
            html = self.theme_env.get_template('post.html')
            with open(path, 'w') as f:
                f.write(html.render(post=post, config=get_config()))

    def render_index(self):
        index_html = self.theme_env.get_template('index.html')
        context = {}
        context['config'] = get_config()
        context['posts'] = list(self.posts)
        index_html = index_html.render(**context)
        with open( os.path.join(DIST_PATH, 'index.html'), 'w') as f:
            f.write(index_html)
    
    def render_extras(self):
        os.chdir(self.theme_templates_path)
        for tmplt_path in glob.glob(self.theme_templates_path, recursive=True):
            if os.path.basename(tmplt_path) != 'index.html':

                # - Saving
                os.makedirs(os.path.dirname(tmplt_path), exist_ok=True)
                html = self.theme_env.get_template(tmplt_path)
                with open(tmplt_path, 'w') as f:
                    f.write(html.render(config=get_config))


    def copying_statics(self):
        from distutils.dir_util import copy_tree
        from_dir = os.path.join(self.theme_path, THEME_STATICS)
        to_dir   = os.path.join(DIST_PATH, THEME_STATICS)
        copy_tree(from_dir, to_dir)

class ServerAction(argparse.Action):
    def __init__(self, **kwargs):
        super(ServerAction, self).__init__(**kwargs)
    
    def __call__(self, parser, namespace, values, option_strings=None):
        os.chdir(DIST_PATH)
        server_address = ('', 8000)
        httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
        httpd.serve_forever()

class PostNew(argparse.Action):
    def __init__(self, **kwargs):
        super(PostNew, self).__init__(**kwargs)

    def __call__(self, parser, namespace, values, option_strings=None):
        #cfg = get_config()
        title = ''.join(values)
        title_slug = title.lower().replace(' ', '-')
        date = datetime.today()
        date_slug = date.strftime('%Y-%m-%d-%H-%m-%S')
        date_post = date.strftime('%d/%m/%Y - %H:%m:%S')
        filename = '{}-{}.md'.format(date_slug, title_slug)
        print('blog > creating ', filename)
        meta = {
                'title': title,
                'author': get_config()['author'],
                'date': date_post,
                'tags': 'none',
                'slug': title_slug
            }
        with open(os.path.join(POSTS_PATH, filename), 'w') as f:
            f.write( POST_TEMPLATE.format(**meta))

parser = argparse.ArgumentParser(DESCRIPTION)
subparsers = parser.add_subparsers(help='pending')

parser2 = subparsers.add_parser('init', help='%(prog)s initialize new blog')
parser2.add_argument('run', nargs=0, action=InitAction, help=argparse.SUPPRESS)

prsr = subparsers.add_parser('build', help='%(prog)s build new blog')
prsr.add_argument('run', nargs=0, action=BuildAction, help=argparse.SUPPRESS)

prsr = subparsers.add_parser('server', help='%(prog)s build new blog')
prsr.add_argument('run', nargs=0, action=ServerAction, help=argparse.SUPPRESS)

parser3 = subparsers.add_parser('post', help='post management')
parser3.add_argument('--new', action=PostNew, nargs='+', help='new post')

args = parser.parse_args()

