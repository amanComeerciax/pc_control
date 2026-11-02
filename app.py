import os
import mimetypes

def app(environ, start_response):
    """
    Vercel WSGI Entrypoint:
    Serves the NeuroRehab static web application and assets with zero external dependencies.
    """
    path = environ.get('PATH_INFO', '/')
    if path == '/' or not path:
        filename = 'index.html'
    else:
        filename = path.lstrip('/')

    # Fallback to index.html for root or SPA routing
    if not os.path.exists(filename):
        filename = 'index.html'

    mime_type, _ = mimetypes.guess_type(filename)
    if not mime_type:
        mime_type = 'text/html' if filename.endswith('.html') else 'application/octet-stream'

    try:
        with open(filename, 'rb') as f:
            content = f.read()
        start_response('200 OK', [
            ('Content-Type', mime_type),
            ('Access-Control-Allow-Origin', '*')
        ])
        return [content]
    except Exception as e:
        start_response('500 Internal Error', [('Content-Type', 'text/plain')])
        return [str(e).encode('utf-8')]

handler = app
application = app
