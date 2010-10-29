import unittest

class TestPyramidBeakerSessionObject(unittest.TestCase):
    def _makeOne(self, request, **options):
        from pyramid_beaker import BeakerSessionFactoryConfig
        return BeakerSessionFactoryConfig(**options)(request)
        
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
