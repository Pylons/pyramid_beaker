pyramid_beaker
==============

A :term:`Beaker` session factory backend for :term:`Pyramid`.

Usage
-----

In the configuration portion of your :term:`Pyramid` app, use the
:func:`pyramid_beaker.BeakerSessionFactoryConfig` function or the
:func:`pyramid_beaker.session_factory_from_settings` function to
create a Pyramid :term:`session factory`.  Subsequently register that
session factory with Pyramid.  At that point, accessing
``request.session`` will provide a Pyramid session using Beaker as a
backend.

:func:`pyramid_beaker.session_factory_from_settings` obtains session
settings from the ``**settings`` dictionary passed to the
Configurator.  It assumes that you've placed session configuration
parameters prefixed with ``session.`` in your Pyramid application's
``.ini`` file.  For example:

.. code-block:: ini

   [app:myapp]
   .. other settings ..
   session.type = file
   session.data_dir = %(here)s/data/sessions/data
   session.lock_dir = %(here)s/data/sessions/lock
   session.key = mykey
   session.secret = mysecret

If your ``.ini`` file has such settings, you can use
:func:`pyramid_beaker.session_factory_from_settings` in your
application's configuration.  For example, let's assume this code is
in the ``__init__.py`` of your Pyramid application that uses an
``.ini`` file with the ``session.`` settings above to obtain its
``**settings`` dictionary.

.. code-block:: python

   from pyramid_beaker import session_factory_from_settings
   from pyramid.configuration import configurator

   def app(global_config, **settings):
       """ This function returns a WSGI application.
       
       It is usually called by the PasteDeploy framework during 
       ``paster serve``.
       """
       zcml_file = settings.get('configure_zcml', 'configure.zcml')
       session_factory = session_factory_from_settings(settings)
       config = Configurator(root_factory=get_root, settings=settings)
       config.begin()
       config.set_session_factory(session_factory)
       # ... other configuration stuff...
       config.end()
       return config.make_wsgi_app()

API
---

.. toctree::
   :maxdepth: 2

   api.rst

Indices and tables
------------------

* :ref:`glossary`
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
