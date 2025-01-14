# -*- coding: utf-8 -*-
#   Copyright 2017 ProjectQ-Framework (www.projectq.ch)
#   Copyright 2021 <Huawei Technologies Co., Ltd>
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
"""
Definitions of some of the most basic quantum gates.

Defines the BasicGate class, the base class of all gates, the BasicRotationGate class, the SelfInverseGate, the
FastForwardingGate, the ClassicalInstruction gate, and the BasicMathGate class.

Gates overload the | operator to allow the following syntax:

.. code-block:: python

    Gate | (qureg1, qureg2, qureg2)
    Gate | (qureg, qubit)
    Gate | qureg
    Gate | qubit
    Gate | (qubit,)

This means that for more than one quantum argument (right side of | ), a tuple needs to be made explicitely, while for
one argument it is optional.
"""

import math
import unicodedata
from copy import deepcopy

import numpy as np

from projectq.types import BasicQubit

from ._command import Command, apply_command
from ._exceptions import NotInvertible, NotMergeable

ANGLE_PRECISION = 12
ANGLE_TOLERANCE = 10 ** -ANGLE_PRECISION
RTOL = 1e-10
ATOL = 1e-12


class _ClassDescriptor:
    """
    Class descriptor for BasicGate.

    Descriptor class used to get the correct string representation of a
    gate class if there is a dispatch class present within the hierarchy.
    This is used mostly in `__str__`, `to_string()` and `tex_str()` methods.
    """

    # pylint: disable=too-few-public-methods
    def __get__(self, obj, objtype):
        if (
            issubclass(objtype, DispatchGateClass)
            and len(objtype.__bases__) > 1
            and any(not issubclass(obj, DispatchGateClass) for obj in objtype.__bases__)
        ):
            return objtype.__mro__[1]
        return objtype


class BasicGate:
    """
    Base class of all gates. (Don't use it directly but derive from it).

    Attributes:
        klass: Access to the real base class of any BasicGate (takes care of
            dispatch classes in case of separate parametric and numeric gate
            classes).
    """

    klass = _ClassDescriptor()

    def __init__(self):
        """
        Initialize a basic gate.

        Note:
            Set interchangeable qubit indices!
            (gate.interchangeable_qubit_indices)

            As an example, consider

            .. code-block:: python

                ExampleGate | (a,b,c,d,e)

            where a and b are interchangeable. Then, call this function as follows:

            .. code-block:: python

                self.set_interchangeable_qubit_indices([[0,1]])

            As another example, consider

            .. code-block:: python

                ExampleGate2 | (a,b,c,d,e)

            where a and b are interchangeable and, in addition, c, d, and e are interchangeable among
            themselves. Then, call this function as

            .. code-block:: python

                self.set_interchangeable_qubit_indices([[0,1],[2,3,4]])
        """
        self.interchangeable_qubit_indices = []

    def get_inverse(self):  # pylint: disable=no-self-use
        """
        Return the inverse gate.

        Standard implementation of get_inverse:

        Raises:
            NotInvertible: inverse is not implemented
        """
        # pylint: disable=no-self-use
        raise NotInvertible("BasicGate: No get_inverse() implemented.")

    def get_merged(self, other):  # pylint: disable=no-self-use
        """
        Return this gate merged with another gate.

        Standard implementation of get_merged:

        Raises:
            NotMergeable: merging is not implemented
        """
        # pylint: disable=no-self-use
        raise NotMergeable("BasicGate: No get_merged() implemented.")

    @staticmethod
    def make_tuple_of_qureg(qubits):
        """
        Convert quantum input of "gate | quantum input" to internal formatting.

        A Command object only accepts tuples of Quregs (list of Qubit objects) as qubits input parameter. However,
        with this function we allow the user to use a more flexible syntax:

            1) Gate | qubit
            2) Gate | [qubit0, qubit1]
            3) Gate | qureg
            4) Gate | (qubit, )
            5) Gate | (qureg, qubit)

        where qubit is a Qubit object and qureg is a Qureg object. This function takes the right hand side of | and
        transforms it to the correct input parameter of a Command object which is:

            1) -> Gate | ([qubit], )
            2) -> Gate | ([qubit0, qubit1], )
            3) -> Gate | (qureg, )
            4) -> Gate | ([qubit], )
            5) -> Gate | (qureg, [qubit])

        Args:
            qubits: a Qubit object, a list of Qubit objects, a Qureg object, or a tuple of Qubit or Qureg objects (can
                be mixed).
        Returns:
            Canonical representation (tuple<qureg>): A tuple containing Qureg (or list of Qubits) objects.
        """
        if not isinstance(qubits, tuple):
            qubits = (qubits,)

        qubits = list(qubits)

        for i, qubit in enumerate(qubits):
            if isinstance(qubit, BasicQubit):
                qubits[i] = [qubit]

        return tuple(qubits)

    def generate_command(self, qubits):
        """
        Generate a command.

        The command object created consists of the gate and the qubits being acted upon.

        Args:
            qubits: see BasicGate.make_tuple_of_qureg(qubits)

        Returns:
            A Command object containing the gate and the qubits.
        """
        qubits = self.make_tuple_of_qureg(qubits)

        engines = [q.engine for reg in qubits for q in reg]
        eng = engines[0]
        if not all(e is eng for e in engines):
            raise ValueError('All qubits must belong to the same engine!')
        return Command(eng, self, qubits)

    def __or__(self, qubits):
        """
        Operator| overload which enables the syntax Gate | qubits.

        Example:
            1) Gate | qubit
            2) Gate | [qubit0, qubit1]
            3) Gate | qureg
            4) Gate | (qubit, )
            5) Gate | (qureg, qubit)

        Args:
            qubits: a Qubit object, a list of Qubit objects, a Qureg object, or a tuple of Qubit or Qureg objects (can
                    be mixed).
        """
        cmd = self.generate_command(qubits)
        apply_command(cmd)

    def __eq__(self, other):
        """
        Equal operator.

        Return True if instance of the same class, unless other is an instance of :class:MatrixGate, in which case
        equality is to be checked by testing for existence and (approximate) equality of matrix representations.
        """
        if isinstance(other, self.__class__):
            return True
        if isinstance(other, MatrixGate):
            return NotImplemented
        return False

    def __str__(self):
        """Return a string representation of the object."""
        raise NotImplementedError('This gate does not implement __str__.')

    def to_string(self, symbols=False):  # pylint: disable=unused-argument
        """
        Return a string representation of the object.

        Achieve same function as str() but can be extended for configurable representation
        """
        # pylint: disable=unused-argument
        return str(self)

    def __hash__(self):
        """Compute the hash of the object."""
        return hash(str(self))

    def is_identity(self):
        """Return True if the gate is an identity gate. In this base class, always returns False."""
        # pylint: disable=no-self-use
        return False

    def is_parametric(self):
        """
        Check whether the gate instance is parametric (ie. has free parameters).

        Returns:
            True if the gate is parametric, False otherwise.
        """
        # pylint: disable=no-self-use
        return False


class MatrixGate(BasicGate):
    """
    Define a gate class whose instances are defined by a matrix.

    Note:
        Use this gate class only for gates acting on a small numbers of qubits.  In general, consider instead using
        one of the provided ProjectQ gates or define a new class as this allows the compiler to work symbolically.

    Example:
        .. code-block:: python

            gate = MatrixGate([[0, 1], [1, 0]])
            gate | qubit
    """

    def __init__(self, matrix=None):
        """
        Initialize a MatrixGate object.

        Args:
            matrix(numpy.matrix): matrix which defines the gate. Default: None
        """
        super().__init__()
        self._matrix = np.matrix(matrix) if matrix is not None else None

    @property
    def matrix(self):
        """Access to the matrix property of this gate."""
        return self._matrix

    @matrix.setter
    def matrix(self, matrix):
        """Set the matrix property of this gate."""
        self._matrix = np.matrix(matrix)

    def __eq__(self, other):
        """
        Equal operator.

        Return True only if both gates have a matrix respresentation and the matrices are (approximately)
        equal. Otherwise return False.
        """
        if not hasattr(other, 'matrix'):
            return False
        if not isinstance(self.matrix, np.matrix) or not isinstance(other.matrix, np.matrix):
            raise TypeError("One of the gates doesn't have the correct type (numpy.matrix) for the matrix attribute.")
        if self.matrix.shape == other.matrix.shape and np.allclose(
            self.matrix, other.matrix, rtol=RTOL, atol=ATOL, equal_nan=False
        ):
            return True
        return False

    def __str__(self):
        """Return a string representation of the object."""
        return "MatrixGate(" + str(self.matrix.tolist()) + ")"

    def __hash__(self):
        """Compute the hash of the object."""
        return hash(str(self))

    def get_inverse(self):
        """Return the inverse of this gate."""
        return MatrixGate(np.linalg.inv(self.matrix))


class SelfInverseGate(BasicGate):  # pylint: disable=abstract-method
    """
    Self-inverse basic gate class.

    Automatic implementation of the get_inverse-member function for self-inverse gates.

    Example:
        .. code-block:: python

            # get_inverse(H) == H, it is a self-inverse gate:
            get_inverse(H) | qubit
    """

    def get_inverse(self):
        """Return the inverse of this gate."""
        return deepcopy(self)


class BasicAngleGate(BasicGate):
    """
    Defines a base class of a gate with an angle parameter.

    A rotation gate has a continuous parameter (the angle), labeled 'angle' / self.angle. Its inverse is the same gate
    with the negated argument.  Rotation gates of the same class can be merged by adding the angles.  The continuous
    parameter is modulo _mod_pi * pi, self.angle is in the interval [0, _mod_pi * pi).
    """

    _mod_pi = None  # Needs to be defined by child classes

    def __init__(self, angle):
        """
        Initialize a basic angle gate.

        Args:
            angle (float): Angle of rotation (saved modulo _mod_pi * pi)
        """
        super().__init__()
        rounded_angle = round(float(angle) % (self.__class__._mod_pi * math.pi), ANGLE_PRECISION)
        if rounded_angle > self.__class__._mod_pi * math.pi - ANGLE_TOLERANCE:
            rounded_angle = 0.0
        self.angle = rounded_angle

    def __str__(self):
        """
        Return the string representation of a BasicRotationGate.

        Returns the class name and the angle as

        .. code-block:: python

            [CLASSNAME]([ANGLE])
        """
        return self.to_string()

    def to_string(self, symbols=False):
        """
        Return the string representation of a BasicRotationGate.

        Args:
            symbols (bool): uses the pi character and round the angle for a more user friendly display if True, full
                            angle written in radian otherwise.
        """
        # pylint: disable=protected-access
        if symbols:
            angle = str(round(self.angle / math.pi, 3)) + unicodedata.lookup("GREEK SMALL LETTER PI")
        else:
            angle = self.angle
        return '{}({})'.format(self.klass.__name__, angle)

    def get_inverse(self):
        """Return the inverse of this rotation gate (negate the angle, return new object)."""
        # pylint: disable=protected-access
        if self.angle == 0:
            return self.__class__(0)
        return self.__class__(-self.angle + self.__class__._mod_pi * math.pi)

    def get_merged(self, other):
        """
        Return self merged with another gate.

        Default implementation handles rotation gate of the same type, where angles are simply added.

        Args:
            other: Rotation gate of same type.

        Raises:
            NotMergeable: For non-rotation gates or rotation gates of different type.

        Returns:
            New object representing the merged gates.
        """
        # NB: allow merging of parametric and numeric classes -> self.klass
        if isinstance(other, self.klass):
            return self.klass(self.angle + other.angle)
        raise NotMergeable("Can't merge different types of rotation gates.")

    def __eq__(self, other):
        """Return True if same class and same rotation angle."""
        # Important: self.__class__ and not self.klass!
        #            (although it should also work)
        if isinstance(other, self.klass):
            return self.angle == other.angle
        return False

    def __hash__(self):
        """Compute the hash of the object."""
        return hash(str(self))

    def is_identity(self):
        """Return True if the gate is equivalent to an Identity gate."""
        # pylint: disable=protected-access
        return self.angle == 0.0 or self.angle == self.__class__._mod_pi * math.pi


class BasicRotationGate(BasicAngleGate):
    """
    Defines a base class of a rotation gate.

    A rotation gate has a continuous parameter (the angle), labeled 'angle' / self.angle. Its inverse is the same gate
    with the negated argument.  Rotation gates of the same class can be merged by adding the angles.  The continuous
    parameter is modulo 4 * pi, self.angle is in the interval [0, 4 * pi).
    """

    _mod_pi = 4

    def tex_str(self):
        """
        Return the Latex string representation of a BasicRotationGate.

        Returns the class name and the angle as a subscript, i.e.

        .. code-block:: latex

            [CLASSNAME]$_[ANGLE]$
        """
        return '{}$_{{{}\\pi}}$'.format(self.klass.__name__, round(self.angle / math.pi, 3))


class BasicPhaseGate(BasicAngleGate):
    """
    Defines a base class of a phase gate.

    A phase gate has a continuous parameter (the angle), labeled 'angle' / self.angle. Its inverse is the same gate
    with the negated argument.  Phase gates of the same class can be merged by adding the angles.  The continuous
    parameter is modulo 2 * pi, self.angle is in the interval [0, 2 * pi).
    """

    _mod_pi = 2

    def tex_str(self):
        """
        Return the Latex string representation of a BasicPhaseGate.

        Returns the class name and the angle as a subscript, i.e.

        .. code-block:: latex

            [CLASSNAME]$_[ANGLE]$
        """
        return '{}$_{{{}}}$'.format(self.klass.__name__, self.angle)


# Classical instruction gates never have control qubits.
class ClassicalInstructionGate(BasicGate):  # pylint: disable=abstract-method
    """
    Classical instruction gate.

    Base class for all gates which are not quantum gates in the typical sense, e.g., measurement,
    allocation/deallocation, ...
    """


class FastForwardingGate(ClassicalInstructionGate):  # pylint: disable=abstract-method
    """
    Base class for fast-forward gates.

    Base class for classical instruction gates which require a fast-forward through compiler engines that cache /
    buffer gates. Examples include Measure and Deallocate, which both should be executed asap, such that Measurement
    results are available and resources are freed, respectively.

    Note:
        The only requirement is that FlushGate commands run the entire circuit. FastForwardingGate objects can be used
        but the user cannot expect a measurement result to be available for all back-ends when calling only
        Measure. E.g., for the IBM Quantum Experience back-end, sending the circuit for each Measure-gate would be too
        inefficient, which is why a final

        .. code-block: python

            eng.flush()

        is required before the circuit gets sent through the API.
    """


class BasicMathGate(BasicGate):
    """
    Base class for all math gates.

    It allows efficient emulation by providing a mathematical representation which is given by the concrete gate which
    derives from this base class.
    The AddConstant gate, for example, registers a function of the form

    .. code-block:: python

        def add(x):
            return (x+a,)

    upon initialization. More generally, the function takes integers as parameters and returns a tuple / list of
    outputs, each entry corresponding to the function input. As an example, consider out-of-place multiplication,
    which takes two input registers and adds the result into a third, i.e., (a,b,c) -> (a,b,c+a*b). The corresponding
    function then is

    .. code-block:: python

        def multiply(a,b,c)
            return (a,b,c+a*b)
    """

    def __init__(self, math_fun):
        """
        Initialize a BasicMathGate by providing the mathematical function that it implements.

        Args:
            math_fun (function): Function which takes as many int values as input, as the gate takes registers. For
                each of these values, it then returns the output (i.e., it returns a list/tuple of output values).

        Example:
            .. code-block:: python

                def add(a,b):
                    return (a,a+b)
                super().__init__(add)

        If the gate acts on, e.g., fixed point numbers, the number of bits per register is also required in order to
        describe the action of such a mathematical gate. For this reason, there is

        .. code-block:: python

            BasicMathGate.get_math_function(qubits)

        which can be overwritten by the gate deriving from BasicMathGate.

        Example:
            .. code-block:: python

                def get_math_function(self, qubits):
                    n = len(qubits[0])
                    scal = 2.**n
                    def math_fun(a):
                        return (int(scal * (math.sin(math.pi * a / scal))),)
                    return math_fun

        """
        super().__init__()

        def math_function(arg):
            return list(math_fun(*arg))

        self._math_function = math_function

    def __str__(self):
        """Return a string representation of the object."""
        return "MATH"

    def get_math_function(self, qubits):  # pylint: disable=unused-argument
        """
        Get the math function associated with a BasicMathGate.

        Return the math function which corresponds to the action of this math gate, given the input to the gate (a
        tuple of quantum registers).

        Args:
            qubits (tuple<Qureg>): Qubits to which the math gate is being applied.

        Returns:
            math_fun (function): Python function describing the action of this gate. (See BasicMathGate.__init__ for
            an example).
        """
        return self._math_function


class DispatchGateClass(BasicGate):
    """Dispatch gate base class."""

    def __str__(self):
        """Return a string representation of the object."""
        # pylint: disable=useless-super-delegation
        return super().__str__()
