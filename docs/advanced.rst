.. _advanced:

Advanced
========

Here you will find some help and information about some more advanced topics about HiQ-ProjectQ.


.. _partial_compilation:

Partial compilation
+++++++++++++++++++

Partial compilation of quantum circuit was added to HiQ-ProjectQ. While it was previously already possible to store the processed list of commands (using the ``DummyEngine``) for example, there was no compelling reason to do so.

Previously, in applications where a particular quantum circuit is run multiple times with only small variations of the gate parameters (e.g. during the optimisation stage for VQE circuits or during calibration experiments), the quantum circuit had to be re-created at each iteration. That implies running the qubits through the optimiser, mapper and any other compiler engines for each iterations which is rather inefficient.

With the introduction of partial compilation and gates with parametric (or symbolic) parameters, we can now drastically improve performance in situations such as the one mentioned above. In the following, we will be referring to *parametric* gates as gate instances that have at least one attribute that is parametric (or symbolic) and *numeric* gates for those that only possess numeric attributes. We will also be using *parametric* and *symbolic* interchangeably as synonyms.

Symbolic calculations
---------------------

In order to implement symbolic calculations, HiQ-ProjectQ relies on the `SymPy <https://pypi.org/project/sympy/>`__ Python package. Make sure that you have it installed before proceeding further.


Parametric gates
----------------

As mentioned above, a *parametric* gate is one with at least one attribute that is not numeric. In practice, that usually means that one of the gate attribute is not a number but a *sympy* expression or symbol.


Examples of parametric gates can be found below:

.. code-block:: python

   import sympy
   from projectq.cengines import MainEngine, DummyEngine
   from projectq.ops import Rx, Ph

   # Define some symbolic variables
   x, y = sympy.symbols('x y')

   # NB: this MainEngine does not run a simulation, it only stores the commands
   eng = MainEngine(backend=DummyEngine())
   qubit = eng.allocate_qubit()

   Rx(x) | qubit  # Apply a parametric Rx gate to the qubit
   Rx(1.) | qubit  # Apply a numeric Rx gate to the qubit

   # Same thing with the Ph gate
   Ph(y) | qubit
   Ph(2.) | qubit

   eng.flush()

In the above example, note that the syntax for both parametric and numeric case is very similar. Only the type of the parameter passed onto the ``Rx`` and ``Ph`` gates varies. Behind the scenes, parametric and numeric gates are treated the same by the other compiler engines, such as the :class:`~projectq.cengines.LocalOptimizer` or the various mappers for example. This means in particular that the above circuit will result in the following list of commands::

    AllocateQubit | Qureg[0]
    Rx(x + 1.) | Qureg[0]
    Ph(y + 2.) | Qureg[0]
    DeallocateQubit | Qureg[0]

However, as it is, we cannot actually simulate this quantum circuit since the simulator does not support parametric gates. In order to simulate or run this quantum circuit on some hardware, we need to specify the value of `x` and `y`.


Standard gates
~~~~~~~~~~~~~~

Currently, the following gate classes support symbolic attributes: :class:`~projectq.ops.QubitOperator`, :class:`~projectq.ops.TimeEvolution`, :class:`~projectq.ops.R`, :class:`~projectq.ops.Ph`, :class:`~projectq.ops.Rx`, :class:`~projectq.ops.Rxx`, :class:`~projectq.ops.Ry`, :class:`~projectq.ops.Ryy`, :class:`~projectq.ops.Rz`, :class:`~projectq.ops.Rzz`

Custom parametric gates
~~~~~~~~~~~~~~~~~~~~~~~

In order to define your own parametric gate class, simply create a new class that inherits from either :class:`~projectq.ops.ParametricGateReal` or  :class:`~projectq.ops.ParametricGateCmplx`. Those two classes automatically provide the :py:meth:`~projectq.ops.ParametricGate.is_parametric` and :py:meth:`~projectq.ops.ParametricGateReal.evaluate` methods.

When defining your class, you need to call the :py:meth:`~projectq.ops.ParametricGate.__init__` method of the :class:`projectq.ops.ParametricGate` class with the proper keyword arguments. The name of the key defines the name of the attribute and its value the initial value for it.

The example below defines a new parametric gate class ``MyParametricGate`` that has two attributes: ``alpha`` and ``beta``.

.. code-block:: python

   import sympy
   from projectq.ops import ParametricGateCmplx

   class MyGateParam(ParametricGateCmplx):
       def __init__(self, param1, param2):
           super().__init__(alpha=param1, beta=param2)

   # Example of usage:
   x = sympy.Symbol('x')
   MyGateParam(x) | qubit
   MyGateParam(1.) | qubit


And that's it! This class can now be used as any other gate class. Using the new parametric gate backend (see the next section), you will even be able to evaluate instances of ``MyParametricGate`` while applying some substitutions.

Custom parametric and numeric gates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In some cases, you might want to separate the implementations of parametric and numeric gate classes. In order to keep a unified syntax for both the parametric and numeric cases, you can make use of a *dispatch* class that will instantiate either a parametric or numeric instance of a gate upon construction.

This is better exemplified by the following example:

.. code-block:: python

   import sympy
   from projectq.ops import Rx

   x = sympy.Symbol('x')
   Rx(x)  # parametric instance of an Rx gate
   Rx(1)  # numeric instance of an Rx gate

   print(type(Rx(x)))
   print(type(Rx(1)))

The above code will generate the following output::

   <class 'projectq.ops._gates.RxParam'>
   <class 'projectq.ops._gates.RxNum'>

Notice how both instance have a distinct class. This is achieved by defining both :class:`~projectq.ops.RxParam` and  :class:`~projectq.ops.RxNum` classes as well as a *dispatch* class named :class:`~projectq.ops.Rx`.

In its simplest form, a dispatch class derives from :class:`~projectq.ops.DispatchGateClass` and looks like this:

.. code-block:: python

   from sympy.core.basic import Basic as SympyBase
   from projectq.ops import DispatchGateClass, ParametricGateReal, BasicGate

   class MyGate(DispatchGateClass):
       def __new__(cls, alpha):
           if isinstance(alpha, SympyBase):
           return super().__new__(MyGateParam)
       return super().__new__(MyGateNum)

   class MyGateParam(MyGate, ParametricGateReal):  # note: inherits from dispatch class!
       def __init__(self, alpha):
           super().__init__(alpha=alpha)

       def get_merged(self, other):
           if isinstance(other, self.klass):
               return self.klass(self.alpha + other.alpha)
           raise NotMergeable("Cannot merge!")


   class MyGateNum(MyGate, BasicGate):  # note: inherits from dispatch class!
       def __init__(self, alpha):
           super().__init__()
       self.alpha = alpha

       def get_merged(self, other):
           if isinstance(other, self.klass):
               return self.klass(self.alpha + other.alpha)
           raise NotMergeable("Cannot merge!")

You can then use this gate class as any other in HiQ-ProjectQ. The handling of parametric and numeric cases is performed at and only at construction time. Which implies that users of the numeric gate class will not incur any other performance penalty in the rest of the processing done at later stages during the compilation of the quantum circuit.

Also note how straightforward the implementation of the ``get_merged`` method actually is. This is made possible thanks to the use of the dispatch class as well as the class descriptor :py:data:`~projectq.ops.BasicGate.klass` from the :py:class:`~projectq.ops.BasicGate` class.


Parametric gate backend
-----------------------

The parametric gate backend was introduced to allow the storage of any incoming HiQ-ProjectQ commands. In addition, this backend supports explicitely sending the commands to another engine (that may be a :class:`~projectq.cengines.MainEngine` or some other engine) and applying some substitution for some of the symbols. The documentation of this new backend can be found here: :class:`~projectq.backends.ParametricGateBackend`.

Here we reproduce the previous example using the parametric gate backend:

.. code-block:: python

   import sympy
   from projectq.backends import ParametricGateBackend
   from projectq.cengines import MainEngine
   from projectq.ops import Rx

   # Define some symbolic variables
   x, y = sympy.symbols('x y')

   eng = MainEngine(backend=ParametricGateBackend())
   qubit = eng.allocate_qubit()

   Rx(x) | qubit
   Rx(1.) | qubit

   Ph(y) | qubit
   Ph(2.) | qubit

   eng.flush()

   # ...

   # Do something else

   # ...

   # Create another MainEngine instance to actually simulate the circuit
   other = MainEngine(engine_list=[])

   # Send the circuit the other MainEngine with some substitutions applied
   eng.backend.send_to(other, subs={x: 1., y: 2.})

   other.flush()  # Not actually required since a flush was done on eng previously


In the above case, the second :class:`~projectq.cengines.MainEngine` will actually receive the following commands and will simulate them::

    AllocateQubit | Qureg[0]
    Rx(2.) | Qureg[0]
    Ph(4.) | Qureg[0]
    DeallocateQubit | Qureg[0]


.. note::

   It is not necessary to fully specify **all** the parameters when sending the command from some :class:`~projectq.backends.ParametricGateBackend` to another engine. If any parametric gate attribute is left unspecified, then the result is simply another parametric gate. It is therefore possible to have multiple stages of substitutions.

   Given this, it is therefore possible to have multiple :class:`~projectq.backends.ParametricGateBackend` that send gates between themselves. Only remember that most backends will not know how to handle parametric gates. You will therefore need to fully specify the free parameters if you intend to simulate or run your quantum circuit on some actual hardware.
