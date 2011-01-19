import unittest

class TestPyramidBeakerSessionObject(unittest.TestCase):
    def _makeOne(self, request, **options):
        from pyramid_beaker import BeakerSessionFactoryConfig
        return BeakerSessionFactoryConfig(**options)(request)

    def test_instance_conforms(self):
        from zope.interface.verify import verifyObject
        from pyramid.interfaces import ISession
        request = DummyRequest()
        session = self._makeOne(request)
        verifyObject(ISession, session)

    def test_callback(self):
        request = DummyRequest()
        session = self._makeOne(request)
        session['fred'] = 42
        session.save()
        self.assertEqual(session.accessed(), True)
        self.failUnless(len(request.callbacks) > 0)
        response= DummyResponse()
        request.callbacks[0](request, response)
        self.failUnless(response.headerlist)

    def test_new(self):
        request = DummyRequest()
        session = self._makeOne(request)
        self.failUnless(session.new)

    def test___setitem__calls_save(self):
        request = DummyRequest()
        session = self._makeOne(request)
        session['a'] = 1
        self.assertEqual(session.__dict__['_dirty'], True)

    def test___delitem__calls_save(self):
        request = DummyRequest()
        session = self._makeOne(request)
        session['a'] = 1
        del session.__dict__['_dirty']
        del session['a']
        self.assertEqual(session.__dict__['_dirty'], True)

    def test_changed(self):
        request = DummyRequest()
        session = self._makeOne(request)
        session.changed()
        self.assertEqual(session.__dict__['_dirty'], True)
        
    def test_clear(self):
        request = DummyRequest()
        session = self._makeOne(request)
        session['a'] = 1
        session.clear()
        self.failIf('a' in session)
        self.assertEqual(session.__dict__['_dirty'], True)

    def test_update(self):
        request = DummyRequest()
        session = self._makeOne(request)
        session.update({'a':1}, b=2)
        self.failUnless('a' in session)
        self.failUnless('b' in session)
        self.assertEqual(session.__dict__['_dirty'], True)

    def test_setdefault(self):
        request = DummyRequest()
        session = self._makeOne(request)
        session.setdefault('a', 'b')
        self.failUnless('a' in session)
        self.assertEqual(session.__dict__['_dirty'], True)
        
    def test_pop(self):
        request = DummyRequest()
        session = self._makeOne(request)
        session['a'] = 1
        session.__dict__['_dirty'] = False
        result = session.pop('a')
        self.failIf('a' in session)
        self.assertEqual(result, 1)
        self.assertEqual(session.__dict__['_dirty'], True)

    def test_popitem(self):
        request = DummyRequest()
        session = self._makeOne(request)
        session['a'] = 1
        session.__dict__['_dirty'] = False
        result = session.popitem()
        self.failIf('a' in session)
        self.assertEqual(result, ('a', 1))
        self.assertEqual(session.__dict__['_dirty'], True)

    def test_flash_default(self):
        request = DummyRequest()
        session = self._makeOne(request)
        session.flash('msg1')
        session.flash('msg2')
        self.assertEqual(session['_f_'], ['msg1', 'msg2'])
        
    def test_flash_mixed(self):
        request = DummyRequest()
        session = self._makeOne(request)
        session.flash('warn1', 'warn')
        session.flash('warn2', 'warn')
        session.flash('err1', 'error')
        session.flash('err2', 'error')
        self.assertEqual(session['_f_warn'], ['warn1', 'warn2'])

    def test_pop_flash_default_queue(self):
        request = DummyRequest()
        session = self._makeOne(request)
        queue = ['one', 'two']
        session['_f_'] = queue
        result = session.pop_flash()
        self.assertEqual(result, queue)
        self.assertEqual(session.get('_f_'), None)

    def test_pop_flash_nodefault_queue(self):
        request = DummyRequest()
        session = self._makeOne(request)
        queue = ['one', 'two']
        session['_f_error'] = queue
        result = session.pop_flash('error')
        self.assertEqual(result, queue)
        self.assertEqual(session.get('_f_error'), None)

    def test_peek_flash_default_queue(self):
        request = DummyRequest()
        session = self._makeOne(request)
        queue = ['one', 'two']
        session['_f_'] = queue
        result = session.peek_flash()
        self.assertEqual(result, queue)
        self.assertEqual(session.get('_f_'), queue)

    def test_peek_flash_nodefault_queue(self):
        request = DummyRequest()
        session = self._makeOne(request)
        queue = ['one', 'two']
        session['_f_error'] = queue
        result = session.peek_flash('error')
        self.assertEqual(result, queue)
        self.assertEqual(session.get('_f_error'), queue)

    def test_new_csrf_token(self):
        request = DummyRequest()
        session = self._makeOne(request)
        token = session.new_csrf_token()
        self.assertEqual(token, session['_csrft_'])

    def test_get_csrf_token(self):
        request = DummyRequest()
        session = self._makeOne(request)
        session['_csrft_'] = 'token'
        token = session.get_csrf_token()
        self.assertEqual(token, 'token')
        self.failUnless('_csrft_' in session)

    def test_get_csrf_token_new(self):
        request = DummyRequest()
        session = self._makeOne(request)
        token = session.get_csrf_token()
        self.failUnless(token)
        self.assertEqual(session['_csrft_'], token)

class Test_session_factory_from_settings(unittest.TestCase):
    def _callFUT(self, settings):
        from pyramid_beaker import session_factory_from_settings
        return session_factory_from_settings(settings)

    def test_it(self):
        settings = {'session.auto':'true', 'session.key':'foo'}
        factory = self._callFUT(settings)
        self.assertEqual(factory._options, {'auto':True, 'key':'foo'})

    def test_cookie_on_exception_true(self):
        settings = {'session.cookie_on_exception':'true'}
        factory = self._callFUT(settings)
        self.assertEqual(factory._cookie_on_exception, True)

    def test_cookie_on_exception_false(self):
        settings = {'session.cookie_on_exception':'false'}
        factory = self._callFUT(settings)
        self.assertEqual(factory._cookie_on_exception, False)

class DummyRequest:
    def __init__(self):
        self.callbacks = []
        self.environ = {}

    def add_response_callback(self, callback):
        self.callbacks.append(callback)

class DummyResponse:
    def __init__(self):
        self.headerlist = []
    
class Test_session_cookie_on_exception(unittest.TestCase):

    def _makeOne(self, request, **options):
        from pyramid_beaker import BeakerSessionFactoryConfig
        return BeakerSessionFactoryConfig(**options)(request)

    def test_default_cookie_on_exception_setting(self):
        request = DummyRequest()
        session = self._makeOne(request)
        self.assertEqual(session._cookie_on_exception, True)

    def test_cookie_on_exception_setting(self):
        request = DummyRequest()
        session = self._makeOne(request, cookie_on_exception=False)
        self.assertEqual(session._cookie_on_exception, False)
    
    def _assert_session_persisted(self, request, session, expected):
        # Checking response headers not likely best method of asserting 
        # if Beaker's SessionObject.persist method was called.
        # Not sure of best method of doing this.
        request.exception = True 
        session['use it'] = True
        response = DummyResponse()
        request.callbacks[0](request, response)
        self.assertEqual(len(response.headerlist) == 1, expected)

    def test_request_call_back_without_cookie_on_exception(self):
        request = DummyRequest()
        session = self._makeOne(request)
        self._assert_session_persisted(request, session, True)

    def test_request_call_back_with_cookie_on_exception(self):
        request = DummyRequest()
        session = self._makeOne(request, cookie_on_exception=False)
        self._assert_session_persisted(request, session, False)

class TestCacheConfiguration(unittest.TestCase):
    def _set_settings(self):
        return {'cache.regions':'default_term, second, short_term, long_term',
                'cache.type':'memory',
                'cache.second.expire':'1',
                'cache.short_term.expire':'60',
                'cache.default_term.expire':'300',
                'cache.long_term.expire':'3600',
                }
    
    def test_add_cache_no_regions(self):
        from pyramid_beaker import set_cache_regions_from_settings
        import beaker
        settings = self._set_settings()
        beaker.cache.cache_regions = {}
        settings['cache.regions'] = ''
        set_cache_regions_from_settings(settings)
        self.assertEqual(beaker.cache.cache_regions, {})

    def test_add_cache_single_region_no_expire(self):
        from pyramid_beaker import set_cache_regions_from_settings
        import beaker
        settings = self._set_settings()
        beaker.cache.cache_regions = {}
        settings['cache.regions'] = 'default_term'
        del settings['cache.default_term.expire']
        set_cache_regions_from_settings(settings)
        default_term = beaker.cache.cache_regions.get('default_term')
        self.assertEqual(default_term, {'url': None, 'expire': 60,
                                      'type': 'memory', 'lock_dir': None})
    
    def test_add_cache_multiple_region(self):
        from pyramid_beaker import set_cache_regions_from_settings
        import beaker
        settings = self._set_settings()
        beaker.cache.cache_regions = {}
        settings['cache.regions'] = 'default_term, short_term'
        settings['cache.lock_dir'] = 'foo'
        settings['cache.short_term.expire'] = '60'
        settings['cache.default_term.type'] = 'file'
        settings['cache.default_term.expire'] = '300'
        set_cache_regions_from_settings(settings)
        default_term = beaker.cache.cache_regions.get('default_term')
        short_term = beaker.cache.cache_regions.get('short_term')
        self.assertEqual(short_term.get('expire'),
                         int(settings['cache.short_term.expire']))
        self.assertEqual(short_term.get('lock_dir'), settings['cache.lock_dir'])
        self.assertEqual(short_term.get('type'), 'memory')

        self.assertEqual(default_term.get('expire'),
                         int(settings['cache.default_term.expire']))
        self.assertEqual(default_term.get('lock_dir'),
                         settings['cache.lock_dir'])
        self.assertEqual(default_term.get('type'),
                         settings['cache.default_term.type'])
    
    def test_region_inherit_url(self):
        from pyramid_beaker import set_cache_regions_from_settings
        import beaker
        settings = self._set_settings()
        beaker.cache.cache_regions = {}
        settings['cache.regions'] = 'default_term, short_term'
        settings['cache.lock_dir'] = 'foo'
        settings['cache.url'] = '127.0.0.1'
        settings['cache.short_term.expire'] = '60'
        settings['cache.default_term.type'] = 'file'
        settings['cache.default_term.expire'] = '300'
        set_cache_regions_from_settings(settings)
        default_term = beaker.cache.cache_regions.get('default_term')
        short_term = beaker.cache.cache_regions.get('short_term')
        self.assertEqual(short_term.get('url'), settings['cache.url'])
        self.assertEqual(default_term.get('url'), settings['cache.url'])
