"""
WSGI config for api project.

It exposes the WSGI callable as a module-level variable named ``app``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/wsgi/
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')

application = get_wsgi_application()

from wsgiref.simple_server import make_server
port = int(os.getenv('PORT', 8000))  # Default to 8000 if PORT is not set
httpd = make_server('0.0.0.0', port, application)
httpd.serve_forever()
