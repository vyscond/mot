__author__ = 'Ramon Moraes'
__version__ = '0.0.0'
__description__ = 'Just an ordinary static blog engine'

import os
import sys
import glob
import argparse
import collections
import json
import jinja2
import misaka as m
from datetime import datetime
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name

BASE_PATH = os.path.abspath('.')
POSTS_PATH = os.path.join(BASE_PATH, '_posts')
THEMES_PATH = os.path.join(BASE_PATH, '_themes')

DIST_PATH = os.path.join(BASE_PATH, 'dist')
DIST_PATH_POSTS = os.path.join(DIST_PATH, 'post')
DIST_PATH_STATICS = os.path.join(DIST_PATH, 'bower_components')

THEME_STATICS = 'bower_components'

TINYMATTER_DIVIDER = '------'
POST_TEMPLATE = '''
title: {title}
author: {author}
date: {date}
slug: {slug}
tags: {tags}

{tinymatter}

# Lorem Ispum Lipsum

Lorem ipsum dolor sit amet, dolores noluisse nam et. Ex wisi volumus duo. Choro 
scribentur sea et, pri et essent viderer appetere. Eu mel wisi error mollis.

```python
def generated_by(engine):
    print(engine)

generated_by('mot')
```

Est te veri euismod. At qui soleat discere offendit, diceret consulatu ad qui,
vide tractatos quo. No simul laoreet tibique eam, est ad putant nusquam .
'''

def find_all(path):
    for root, dirs, files in os.walk(path):
        for file in files:
            yield os.path.join(root, file)

class CodeHighlighterRenderer(m.HtmlRenderer):
    def blockcode(self, text, lang):
        if not lang:
            return '\n<pre><code>{}</code></pre>\n'.format(text.strip())
        lexer = get_lexer_by_name(lang, stripall=True)
        formatter = HtmlFormatter()
        return highlight(text, lexer, formatter)

def bootstrap(data):
    with open(os.path.join(BASE_PATH, 'config.json'), 'w') as f:
            dump = json.dumps(data, indent=4)
            f.write(dump)
    os.makedirs(POSTS_PATH, exist_ok=True)
    os.makedirs(THEMES_PATH, exist_ok=True)
    os.makedirs(DIST_PATH, exist_ok=True)

def get_config():
    return json.load(
        open(os.path.join(BASE_PATH, 'config.json')), 
        object_pairs_hook=collections.OrderedDict
    )

class Post(dict):

    def __init__(self, fname=None):
        if fname:
            with open(fname) as f:
                self.update(self.tinymatter(f.read()))
    
    def set_title(self, title):
        self['title'] = title
        self['slug'] = title.lower().replace(' ', '-').replace("'","").replace('"','')
    
    def set_date(self, date=None):
        date = date or datetime.today()
        self['date_slug'] = date.strftime('%Y-%m-%d-%H-%m-%S')
        self['date'] = date.strftime('%d/%m/%Y - %H:%m:%S')

    def save(self):
        filename = '{}-{}.md'.format(self['date_slug'], self['slug'])
        print('blog > creating ', filename)
        # meta = {
        #         'title': title,
        #         'author': get_config()['author'],
        #         'date': date_post,
        #         'tags': 'none',
        #         'slug': title_slug
        #     }
        self['tinymatter'] = TINYMATTER_DIVIDER
        self['author'] = get_config()['author']
        self['tags'] = ''
        with open(os.path.join(POSTS_PATH, filename), 'w') as f:
            f.write(POST_TEMPLATE.format(**self))

    def tinymatter(self, markdown):
        meta, md = markdown.split(TINYMATTER_DIVIDER)
        post = {}
        for entry in meta.split('\n'):
            slc = entry.find(':')
            key = entry[:slc]
            val = entry[slc+1:]
            post[key.strip()] = val.strip()
        # - Rendering content
        post['body'] = {}
        post['body']['md'] = md
        post['body']['html'] = self.render_markdown(md)
        # - Ajust anchor slug
        post['href'] = os.path.join('post', post['slug']) + '.html'
        return post

    def render_markdown(self, md):
        return m.Markdown(CodeHighlighterRenderer(), 
            extensions=('fenced-code',))(md)


class PostManager(object):
    def __init__(self):
        self.posts = [ Post(fname) for fname in glob.glob(os.path.join(POSTS_PATH, '*.md'))]


class Theme(object):
    def __init__(self, name=None):
        #  _themes/[name]/
        name = name or get_config()['theme']
        self.path = os.path.join(THEMES_PATH, name)
        # _themes/[name]/templates
        self.templates_path = os.path.join(self.path, 'templates')
        # - Posts
        self.posts = PostManager().posts
        # renderer
        loader = jinja2.FileSystemLoader(self.templates_path)
        self.templates = jinja2.Environment(loader=loader)
        # os.chdir(self.path)
    
    def build(self):
        self.render_posts()
        self.render_index()
        self.copying_statics()

    def render_posts(self):
        os.makedirs(DIST_PATH_POSTS, exist_ok=True)
        for post in self.posts:            
            path = os.path.join(DIST_PATH_POSTS, post['slug']) + '.html'
            with open(path, 'w') as f:
                html = self.templates.get_template('post.html')
                f.write(html.render(post=post, config=get_config()))

    def render_index(self):
        context = {}
        context['config'] = get_config()
        context['posts'] = self.posts
        with open( os.path.join(DIST_PATH, 'index.html'), 'w') as f:
            html = self.templates.get_template('index.html')
            f.write(html.render(**context))
    
    # TODO define how you gunna build extra pages
    def render_extras(self):
        os.chdir(self.templates_path)
        print(self.templates_path)
        for tmplt_path in find_all(self.templates_path):
            if os.path.basename(tmplt_path) != 'index.html':
                # - Saving
                os.makedirs(os.path.dirname(tmplt_path), exist_ok=True)
                print('--->', tmplt_path)
                html = self.templates.get_template(tmplt_path)
                dist = os.path.join(DIST_PATH, tmplt_path)
                print('saving --->', dist)
                with open(dist, 'w') as f:
                    f.write(html.render(config=get_config))

    def copying_statics(self):
        from distutils.dir_util import copy_tree
        from_dir = os.path.join(self.path, THEME_STATICS)
        copy_tree(from_dir, DIST_PATH_STATICS)

    
