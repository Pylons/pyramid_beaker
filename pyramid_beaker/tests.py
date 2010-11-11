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

class Test_session_factory_from_settings(unittest.TestCase):
    def _callFUT(self, settings):
        from pyramid_beaker import session_factory_from_settings
        return session_factory_from_settings(settings)

    def test_it(self):
        settings = {'session.auto':'true', 'session.key':'foo'}
        factory = self._callFUT(settings)
        self.assertEqual(factory._options, {'auto':True, 'key':'foo'})
    
class DummyRequest:
    def __init__(self):
        self.callbacks = []
        self.environ = {}

    def add_response_callback(self, callback):
        self.callbacks.append(callback)

class DummyResponse:
    def __init__(self):
        self.headerlist = []
        
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
        self.assertEqual(default_term, {'expire': 60, 'type': 'memory',
                                      'lock_dir': None})
    
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
