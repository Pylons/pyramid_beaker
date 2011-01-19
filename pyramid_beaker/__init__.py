import os

from beaker import cache
from beaker.session import SessionObject
from beaker.util import coerce_session_params

from pyramid.interfaces import ISession
from pyramid.settings import asbool
from zope.interface import implements

def BeakerSessionFactoryConfig(**options):
    """ Return a Pyramid session factory using Beaker session settings
    supplied directly as ``**options``"""

    class PyramidBeakerSessionObject(SessionObject):
        implements(ISession)
        _options = options
        _cookie_on_exception = _options.pop('cookie_on_exception', True)
        def __init__(self, request):
            SessionObject.__init__(self, request.environ, **self._options)
            def session_callback(request, response):
                exception = getattr(request, 'exception', None)
                if (exception is None or self._cookie_on_exception
                    and self.accessed()):
                    self.persist()
                    headers = self.__dict__['_headers']
                    if headers['set_cookie'] and headers['cookie_out']:
                        response.headerlist.append(
                            ('Set-Cookie', headers['cookie_out']))
            request.add_response_callback(session_callback)

        # ISession API

        @property
        def new(self):
            return self.last_accessed is None

        changed = SessionObject.save

        # modifying dictionary methods

        @call_save
        def clear(self):
            return self._session().clear()

        @call_save
        def update(self, d, **kw):
            return self._session().update(d, **kw)

        @call_save
        def setdefault(self, k, d=None):
            return self._session().setdefault(k, d)

        @call_save
        def pop(self, k, d=None):
            return self._session().pop(k, d)

        @call_save
        def popitem(self):
            return self._session().popitem()

        __setitem__ = call_save(SessionObject.__setitem__)
        __delitem__ = call_save(SessionObject.__delitem__)

        # Flash API methods
        def flash(self, msg, queue='', allow_duplicate=True):
            storage = self.setdefault('_f_' + queue, [])
            if allow_duplicate or (msg not in storage):
                storage.append(msg)

        def pop_flash(self, queue=''):
            storage = self.pop('_f_' + queue, [])
            return storage

        def peek_flash(self, queue=''):
            storage = self.get('_f_' + queue, [])
            return storage

        # CSRF API methods
        def new_csrf_token(self):
            token = os.urandom(20).encode('hex')
            self['_csrft_'] = token
            return token

        def get_csrf_token(self):
            token = self.get('_csrft_', None)
            if token is None:
                token = self.new_csrf_token()
            return token

    return PyramidBeakerSessionObject


def call_save(wrapped):
    """ By default, in non-auto-mode beaker badly wants people to
    call save even though it should know something has changed when
    a mutating method is called.  This hack should be removed if
    Beaker ever starts to do this by default. """
    def save(session, *arg, **kw):
        value = wrapped(session, *arg, **kw)
        session.save()
        return value
    save.__doc__ = wrapped.__doc__
    return save


def session_factory_from_settings(settings):
    """ Return a Pyramid session factory using Beaker session settings
    supplied from a Paste configuration file"""
    prefixes = ('session.', 'beaker.session.')
    options = {}

    # Pull out any config args meant for beaker session. if there are any
    for k, v in settings.items():
        for prefix in prefixes:
            if k.startswith(prefix):
                option_name = k[len(prefix):]
                if option_name == 'cookie_on_exception':
                    v = asbool(v)
                options[option_name] = v

    options = coerce_session_params(options)
    return BeakerSessionFactoryConfig(**options)

def set_cache_regions_from_settings(settings):
    """ Add cache support to the Pylons application.
    
    The ``settings`` passed to the configurator are used to setup
    the cache options. Cache options in the settings should start
    with either 'beaker.cache.' or 'cache.'.
    
    """
    cache_settings = {'regions':None}
    for key in settings.keys():
        for prefix in ['beaker.cache.', 'cache.']:
            if key.startswith(prefix):
                name = key.split(prefix)[1].strip()
                cache_settings[name] = settings[key].strip()
    if cache_settings['regions']:
        for region in cache_settings['regions'].split(','):
            region = region.strip()
            region_settings = {}
            for key, value in cache_settings.items():
                if key.startswith(region):
                    region_settings[key.split('.')[1]] = value
            region_settings['expire'] = int(region_settings.get('expire', 60))
            if 'lock_dir' not in region_settings:
                region_settings['lock_dir'] = cache_settings.get('lock_dir')
            if 'type' not in region_settings:
                region_settings['type'] = cache_settings.get('type', 'memory')
            if 'url' not in region_settings:
                region_settings['url'] = cache_settings.get('url')
            cache.cache_regions[region] = region_settings
