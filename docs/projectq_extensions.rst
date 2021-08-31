.. _extending:

Extending ProjectQ
==================

ProjectQ has been ported to a Python namespace package (see `this link <https://packaging.python.org/guides/packaging-namespace-packages/>`__ for more information). This has the advantage that creating extension packages for ProjectQ has been made much easier than previously. It is now possible to create your own compiler engines or operations and have them seamlessly integrate into ProjectQ.

Below, you will find a complete example of introducing a new compiler engine to ProjectQ and complete Python package setup in order to distribute it to others.


New compiler engine
-------------------

First let's start by creating a new compiler engine. This particular engine will not do anything meaningful; it will just count the number of occurrences of a particular type of gates and otherwise pass on the commands to the next engine.

First create a folder for our new package (e.g. ``gate_counter``). This folder will be the root directory of our new package.

Within this folder, now create the ``projectq`` and the ``projectq/cengines`` folders. After doing so, in a file called ``projectq/cengines/_gate_counter.py``, copy-paste the following code:

.. code-block:: python
    :caption: projectq/cengines/_gate_counter.py

    from projectq.cengines import BasicEngine
    from projectq.ops import BasicGate

    class GateClassCounter(BasicEngine):
    # Constructor: takes either a gate instance or gate class
        def __init__(self, gate):
            self._count = 0
            if isinstance(gate, BasicGate):
                self.gate_class = gate.__class__
            else:
                self.gate_class = gate

        # Access the number of times a gate class has been seen
        @property
        def count(self):
            return self._count

        def receive(self, command_list):
            for cmd in command_list:
                if isinstance(cmd.gate, self.gate_class):
                    self._count += 1
            self.send(command_list)


Other required files
--------------------

Before we create the setup code, we also need to copy the ``projectq/__init__.py`` and ``projectq/cengines/__init__.py`` files from the original ProjectQ distribution to their similar location within our root folder. You can find simplified versions of both of these files below for your convenience.

.. code-block:: python
    :caption: projectq/__init__.py

    __path__ = __import__('pkgutil').extend_path(__path__, __name__)

    from projectq.cengines import MainEngine

.. code-block:: python
    :caption: projectq/cengines/__init__.py

    import sys
    import inspect
    import pkgutil
    from importlib import import_module

    from .core import *


    def dynamic_import(name):
        """
        Dynamically import symbols inside this module
        """
        imported_module = import_module('.' + name, package=__name__)

        if hasattr(imported_module, '__all__'):
            for symbol_name in imported_module.__all__:
                globals().setdefault(symbol_name, getattr(imported_module, symbol_name))
            return

        for attr_name in dir(imported_module):
            module_attr = getattr(imported_module, attr_name)

            # Only automatically import classes that derive from BasicEngine or
            # Exception and that have not already been imported and avoid
            # importing classes from other ProjectQ submodules
            if (
                inspect.isclass(module_attr)
                and issubclass(module_attr, (BasicEngine, Exception))
                and attr_name not in globals()
                and __name__ in module_attr.__module__
            ):
                globals()[attr_name] = module_attr


    _failed_list = []
    for (_, pkg_name, _) in pkgutil.iter_modules(path=__path__):
        if pkg_name.endswith('test') or pkg_name == 'core':
            continue
        try:
            dynamic_import(pkg_name)
        except ImportError:
            _failed_list.append(pkg_name)

    for pkg_name in _failed_list:
        dynamic_import(pkg_name)


Python setup file
-----------------

We can now create the ``setup.py`` file required to tell Python how to install our newly created package.

.. code-block:: python
    :caption: setup.py

    from setuptools import setup, find_packages

    setup(
        name='gate-counter',
        version='0.1',
        install_requires=['projectq'],
        zip_safe=False,
        packages=find_packages())


Installing our package
----------------------

Within the root folder of our package, we now have a total of two folders and four files:

.. code-block:: text

    root
    ├── projectq
    │   ├── __init__.py
    │   └── cengines
    │       ├── __init__.py
    │       └── _gate_counter.py
    └── setup.py

The newly created package can now be installed either using::

  $ python3 setup.py install

or by using Pip::

  $ python3 -m pip install .


.. note::

    If you plan on ever running Python from within the root folder of the package you have written, the ``projectq`` folder contained within it may interfere with Python's search path for modules. In those cases, to avoid any conflicts, we would recommend yout to use an extra level of directories. For example, move the ``projectq`` folder into a ``src`` directory:

    .. code-block:: text

        root
        ├── src
        │   └── projectq
        │       ├── __init__.py
        │       └── cengines
        │           ├── __init__.py
        │           └── _gate_counter.py
        └── setup.py

    You must then modify the ``setup.py`` file as follows:

    .. code-block:: python

    setup(
            ...,
        packages=find_packages(where='src'),
            package_dir={'': 'src'})


Using our package
-----------------

You can now use the new ``GateClassCounter`` compiler engine as you would any other engine as shown in the first line of the example below:

.. code-block:: python
    :emphasize-lines: 1

    from projectq.cengines import MainEngine, GateClassCounter
    from projectq.ops import X, H, Rx, Measure

    counter = GateClassCounter(X)
    eng = MainEngine(engine_list=[counter])

    qubit = eng.allocate_qubit()

    X | qubit
    H | qubit
    Rx(1.2) | qubit
    Measure | qubit
    eng.flush()

    assert counter.count == 1
