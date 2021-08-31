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

"""Contains the definition of a parametric gate with 2 angle parameters."""

import math
from numbers import Number

import sympy

from .._base import NotMergeable
from ._parametric_base import InvalidAngle, ParametricGateReal

# ==============================================================================


class ParametricAngleGate2(ParametricGateReal):
    """Base class for all parametric gates that store two angle parameters."""

    _mod_pi_theta = None  # Needs to be defined by child classes
    _mod_pi_phi = None  # Needs to be defined by child classes

    def __init__(self, theta, phi):
        """
        Initialize a gate with an angle as parameter.

        Args:
            angle (sympy.Symbol): Angle of rotation
        """
        if isinstance(theta, complex) or (not isinstance(theta, Number) and theta.is_number and not theta.is_real):
            raise InvalidAngle('Cannot have a complex angle for theta!')
        if isinstance(phi, complex) or (not isinstance(phi, Number) and phi.is_number and not phi.is_real):
            raise InvalidAngle('Cannot have a complex angle for theta!')

        super().__init__(theta=theta, phi=phi)

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
        Checkswhether the gate instance is parametric (ie. has free parameters).

        Returns:
            True if the gate is parametric, False otherwise.
        """
        # pylint: disable=no-self-use
        return True

    def to_string(self, symbols=False):
        """
        Return the string representation of a ParametricAngleGate.

        Args:
            sSmbols (bool): No-op (only for compatibility with normal gates)
        """
        # pylint: disable=protected-access,no-member
        return '{}({},{})'.format(self.klass.__name__, self.theta, self.phi)

    def tex_str(self):
        """
        Return the Latex string representation of a ParametricAngleGate.

        Returns the class name and the angle as a subscript, i.e.

        .. code-block:: latex

            [CLASSNAME]$_[ANGLE]$
        """
        # pylint: disable=protected-access,no-member
        return '{}$({},{})$'.format(self.klass.__name__, sympy.latex(self.theta), sympy.latex(self.phi))

    def get_inverse(self):
        """Return the inverse of this rotation gate (negate the angle, return new object)."""
        # pylint: disable=no-member
        return self.__class__(-self.theta, -self.phi)

    def get_merged(self, other):
        """
        Return self merged with another gate.

        Default implementation handles rotation gate of the same type, where
        angles are simply added.

        Args:
            other: Rotation gate of same type.

        Raises:
            NotMergeable: For non-rotation gates or rotation gates of
                different type.

        Returns:
            New object representing the merged gates.
        """
        # pylint: disable=no-member
        # NB: allow merging of parametric and numeric classes -> self.klass
        if isinstance(other, self.klass):
            return self.klass(self.theta + other.theta, self.phi + other.phi)
        raise NotMergeable("Can't merge different types of rotation gates.")

    def __eq__(self, other):
        """Return True if same class and same rotation angle."""
        # pylint: disable=no-member
        # Important: self.__class__ and not self.klass!
        #            (although it would probably also work)
        if isinstance(other, self.__class__):
            return self.theta == other.theta and self.phi == other.phi
        return False

    def __hash__(self):
        """Compute the hash of the object."""
        return hash(str(self))

    def is_identity(self):
        """Return True if the gate is equivalent to an Identity gate."""
        # pylint: disable=protected-access,no-member
        return (
            sympy.Mod(self.theta, self.__class__._mod_pi_theta * math.pi) == 0
            and sympy.Mod(self.phi, self.__class__._mod_pi_phi * math.pi) == 0
        ) or (
            sympy.Mod(self.theta, self.__class__._mod_pi_theta * sympy.pi) == 0
            and sympy.Mod(self.phi, self.__class__._mod_pi_phi * sympy.pi) == 0
        )


# ==============================================================================


class ParametricPhaseGate2(ParametricAngleGate2):
    """
    Define a base class of a parametric rotation gate with two angles.

    A rotation gate has two continuous parameter (the angles), labeled 'theta' / self.theta and 'phi' / self.phi. Its
    inverse is the same gate with the negated argument.
    Rotation gates of the same class can be merged by adding the angles.  The continuous parameters are modulo 2 * pi,
    self.theta and self.phi are in the interval [0, 2 * pi).
    """

    _mod_pi_theta = 2
    _mod_pi_phi = 2
