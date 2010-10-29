from beaker.session import SessionObject
from beaker.util import coerce_session_params

## session.type = file
## session.data_dir = %(here)s/data/sessions/data
## session.lock_dir = %(here)s/data/sessions/lock
## session.key = {{project}}
## session.secret = your_app_secret_string

def BeakerSessionFactoryConfig(**options):
    """ Return a Pyramid session factory using Beaker session settings
    supplied directly as ``**options``"""
    if not 'auto' in options:
        # XXX beaker badly wants people to call save; i don't know
        # why it needs it if they call methods that do mutation
        options['auto'] = True 

    class PyramidBeakerSessionObject(SessionObject):
        _options = options
        def __init__(self, request):
            SessionObject.__init__(self, request.environ, **self._options)
            def session_callback(request, response):
                exception = getattr(request, 'exception', None)
                if  exception is None:
                    if self.accessed():
                        self.persist()
                        if self.__dict__['_headers']['set_cookie']:
                            cook = self.__dict__['_headers']['cookie_out']
                            if cook:
                                response.headerlist.append(('Set-Cookie', cook))
            request.add_response_callback(session_callback)

        @property
        def new(self):
            return self.last_accessed is None

        changed = SessionObject.save

        # XXX modified

    return PyramidBeakerSessionObject
        

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
                options[option_name] = v

    options = coerce_session_params(options)
    return BeakerSessionFactoryConfig(**options)
    
    
