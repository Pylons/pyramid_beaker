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
