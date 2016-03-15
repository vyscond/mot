import mot
import os
import argparse
import collections
from http.server import HTTPServer, SimpleHTTPRequestHandler

class InitAction(argparse.Action):
    def __init__(self, **kwargs):
        super(InitAction, self).__init__(**kwargs)

    def __call__(self, parser, namespace, values, option_strings=None):
        # print('{} {} {}'.format(namespace, values, option_strings))
        cfg = collections.OrderedDict()
        cfg['sitename'] = input('site name>') or 'Untitled'
        cfg['payoff'] = input('site payoff>') or 'Payoff'
        cfg['author'] = input('site owner>') or 'anonymuse'
        cfg['theme'] = input('theme>') or 'default'
        cfg['github'] = 'https://github.com/'.format(input('github>'))
        cfg['twitter'] = 'https://twitter.com/'.format(input('twitter>'))
        mot.bootstrap(cfg)

class BuildAction(argparse.Action):
    def __init__(self, **kwargs):
        super(BuildAction, self).__init__(**kwargs)
    
    def __call__(self, parser, namespace, values, option_strings=None):
        mot.Theme().build()

class ServerAction(argparse.Action):
    def __init__(self, **kwargs):
        super(ServerAction, self).__init__(**kwargs)
    
    def __call__(self, parser, namespace, values, option_strings=None):
        os.chdir(mot.DIST_PATH)
        server_address = ('', 8000)
        httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
        httpd.serve_forever()

class PostNew(argparse.Action):
    def __init__(self, **kwargs):
        super(PostNew, self).__init__(**kwargs)

    def __call__(self, parser, namespace, values, option_strings=None):
        print('{} {} {}'.format(namespace, values, option_strings))
        if type(namespace.__dict__['title']) == list:
            title  = ' '.join(namespace.__dict__['title'])
        else:
            title  = namespace.__dict__['title']
        post = mot.Post()
        post.set_title(title)
        post.set_date()
        post.save()

parser = argparse.ArgumentParser(mot.__description__)
subparsers = parser.add_subparsers(help='pending')

parser2 = subparsers.add_parser('init', help='%(prog)s initialize new blog')
parser2.add_argument('run', nargs=0, action=InitAction, help=argparse.SUPPRESS)

prsr = subparsers.add_parser('build', help='%(prog)s build new blog')
prsr.add_argument('run', nargs=0, action=BuildAction, help=argparse.SUPPRESS)

prsr = subparsers.add_parser('server', help='%(prog)s build new blog')
prsr.add_argument('run', nargs=0, action=ServerAction, help=argparse.SUPPRESS)

prsr = subparsers.add_parser('post', help='post management')
prsr.add_argument('new', nargs=1)
prsr.add_argument('title', nargs='+', type=str)
prsr.add_argument('--author', nargs='*', type=str)
prsr.add_argument('--date', nargs='*', type=str)
prsr.add_argument('run', nargs=0, action=PostNew, help='new post')

args = parser.parse_args()

