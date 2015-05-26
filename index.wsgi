import os
import sys
from sae.ext.shell import ShellMiddleware

root = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(root, 'site-packages'))

import pylibmc
sys.modules['memcache'] = pylibmc

import sae
from manage import app

application = sae.create_wsgi_app(ShellMiddleware(app))
