# -*- coding: utf-8 -*-
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

"""Contains the basic building block for parametric (ie. symbolic) gate classes."""

import math
from numbers import Number

import sympy
from sympy.core.basic import Basic as SympyBase

from .._base import BasicGate, NotMergeable


class InvalidAngle(Exception):
    """Exception thrown when an invalid angle value is encountered (e.g. complex number)."""


class ParametricGate(BasicGate):
    """
    Base class for all parametric gates.

    A parametric gate is a gate for which one or more of its parameters are left undefined until some later point
    where it is to be evaluated.
    """

    def __init__(self, **kwargs):
        """
        Initialize a ParametricGate object.

        Args:
            **kwargs: Arbitrary keyword arguments.
                Each keyword define the name of one attribute that may be parametric. The value may be either a
                string, a symbol (sympy.Symbol) or an expression.
        """
        super().__init__()
        self.params = list(kwargs)
        self.__dict__.update({k: v if not isinstance(v, str) else sympy.Symbol(v) for k, v in kwargs.items()})

    def __str__(self):
        """Return a string representation of the object."""
        raise NotImplementedError('This gate does not implement __str__.')

    def is_parametric(self):
        """
        Check whether the gate instance is parametric (ie. has free parameters).

        This definition is to support gates for which a single class is used to represent both numeric and parametric
        cases.

        Returns:
            True if the gate is parametric, False otherwise.

        Note:
            Parameters that derive from sympy.core.basic.Basic are considered to be parametric, even if of the types
            sympy.Float or sympy.Integer for example. This is due to the fact that normal operations on those types
            (+, *, etc.) will lead to symbolic expressions and not numeric values.
        """
        # pylint: disable=no-self-use
        for name in self.params:
            param = getattr(self, name)
            if isinstance(param, SympyBase) and not param.is_number:
                return True
        return False


class ParametricGateReal(ParametricGate):
    """Base class for all parametric gates which should *only* have real parameters."""

    # pylint: disable=abstract-method
    def evaluate(self, subs=None):
        """
        Evaluate all the attributes of a ParametricGateReal instance given some substitution.

        This method will attempt to cast all numbers and successful substitutions to float numbers.

        Args:
            subs (dict): Symbol substitutions to perform

        Returns:
            New gate instance with its attributes evaluated given the substitutions.

        Note:
            No attempt is made to check that the substitutions only result in real numbers!

            Only substitutions meaningful for each stored attributes are considered; any superfluous are silently
            ignored.
            e.g. if self.angle = '2*x', the call self.evaluate(y=1) will not change the value of self.angle

            Also note that whenever possible, this function will attempt to convert sympy expressions to float
            (e.g. sympy.Float or sympy.Integer)
        """
        values = {}
        for name in self.params:
            param = getattr(self, name)
            if isinstance(param, Number) or param.is_number:
                values[name] = float(param)
            else:
                substituted = param.evalf(subs=subs)
                try:
                    values[name] = float(substituted)
                except TypeError:
                    values[name] = substituted

        # Use klass here instead of __class__ because we need to resolve the
        # dispatch class (if it exists) instead of the current class.
        return self.klass(**values)


class ParametricGateCmplx(ParametricGate):
    """Base class for all parametric gates which may have real and complex parameters."""

    # pylint: disable=abstract-method
    def evaluate(self, subs=None):
        """
        Evaluate all the attributes of a ParametricGate instance given some substitution.

        This method will attempt to cast all numbers and successful substitutions to complex numbers.

        Args:
            subs (dict): Symbol substitutions to perform

        Returns:
            New gate instance with its attributes evaluated given the substitutions.

        Note:
            Only substitutions meaningful for each stored attributes are considered; any superfluous are silently
            ignored.
            e.g. if self.angle = '2*x', the call self.evaluate(y=1) will not change the value of self.angle

            Also note that whenever possible, this function will attempt to convert sympy expressions to float
            (e.g. sympy.Float or sympy.Integer)
        """
        values = {}
        for name in self.params:
            param = getattr(self, name)
            if isinstance(param, Number) or param.is_number:
                values[name] = complex(param)
            else:
                substituted = param.evalf(subs=subs)
                try:
                    values[name] = complex(substituted)
                except TypeError:
                    values[name] = substituted

        # Use klass here instead of __class__ because we need to resolve the
        # dispatch class (if it exists) instead of the current class.
        return self.klass(**values)


class ParametricAngleGate(ParametricGateReal):
    """Base class for all parametric gates that store an angle parameter."""

    _mod_pi = None  # Needs to be defined by child classes

    def __init__(self, angle):
        """
        Initialize a gate with an angle as parameter.

        Args:
            angle (sympy.Symbol): Angle of rotation
        """
        if isinstance(angle, complex) or (not isinstance(angle, Number) and angle.is_number and not angle.is_real):
            raise InvalidAngle('Cannot have a complex angle!')

        super().__init__(angle=angle)

    def __str__(self):
        """
        Return the string representation of a BasicRotationGate.

        Returns the class name and the angle as

        .. code-block:: python

            [CLASSNAME]([ANGLE])
        """
        return self.to_string()

    def is_parametric(self):
        """
        Check whether the gate instance is parametric (ie. has free parameters).

        Returns:
            True if the gate is parametric, False otherwise.
        """
        # pylint: disable=no-self-use
        return True

    def to_string(self, symbols=False):
        """
        Return the string representation of a ParametricAngleGate.

        Args:
            symbols (bool): No-op (only for compatibility with normal gates)
        """
        # pylint: disable=protected-access,no-member
        return '{}({})'.format(self.klass.__name__, self.angle)

    def tex_str(self):
        """
        Return the Latex string representation of a ParametricAngleGate.

        Returns the class name and the angle as a subscript, i.e.

        .. code-block:: latex

            [CLASSNAME]$_[ANGLE]$
        """
        # pylint: disable=protected-access,no-member
        return '{}$({})$'.format(self.klass.__name__, sympy.latex(self.angle))

    def get_inverse(self):
        """Return the inverse of this rotation gate (negate the angle, return new object)."""
        # pylint: disable=no-member
        return self.__class__(-self.angle)

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
        # pylint: disable=no-member
        # NB: allow merging of parametric and numeric classes -> self.klass
        if isinstance(other, self.klass):
            return self.klass(self.angle + other.angle)
        raise NotMergeable("Can't merge different types of rotation gates.")

    def __eq__(self, other):
        """Return True if same class and same rotation angle."""
        # pylint: disable=no-member
        # Important: self.__class__ and not self.klass!
        #            (although it would probably also work)
        if isinstance(other, self.__class__):
            return self.angle == other.angle
        return False

    def __hash__(self):
        """Compute the hash of the object."""
        return hash(str(self))

    def is_identity(self):
        """Return True if the gate is equivalent to an Identity gate."""
        # pylint: disable=protected-access,no-member
        return (
            sympy.Mod(self.angle, self.__class__._mod_pi * math.pi) == 0
            or sympy.Mod(self.angle, self.__class__._mod_pi * sympy.pi) == 0
        )


class ParametricRotationGate(ParametricAngleGate):
    """
    Define a base class of a parametric rotation gate.

    A rotation gate has a continuous parameter (the angle), labeled 'angle' / self.angle. Its inverse is the same gate
    with the negated argument.  Rotation gates of the same class can be merged by adding the angles.  The continuous
    parameter is modulo 4 * pi, self.angle is in the interval [0, 4 * pi).
    """

    _mod_pi = 4


class ParametricPhaseGate(ParametricAngleGate):
    """
    Define a base class of a parametric phase gate.

    A phase gate has a continuous parameter (the angle), labeled 'angle' / self.angle. Its inverse is the same gate
    with the negated argument.  Phase gates of the same class can be merged by adding the angles.  The continuous
    parameter is modulo 2 * pi, self.angle is in the interval [0, 2 * pi).
    """

    _mod_pi = 2
