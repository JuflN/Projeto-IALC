from flask_caching import Cache

cache = Cache()

def init_cache(app):
    app.config['CACHE_TYPE'] = 'SimpleCache'
    cache.init_app(app)