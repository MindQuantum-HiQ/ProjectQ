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

"""Parametric base classes for a general unitary and related sub-classes."""

import math
from numbers import Number

import sympy

from ._parametric_base import InvalidAngle, ParametricGateReal


class ParametricGeneralUnitary(ParametricGateReal):
    """Parametric general unitary gate class."""

    def __init__(self, alpha, beta, gamma, delta):
        """
        Initialize a parametric general unitary gate.

        U(α, β, γ, λ) := exp(iα)Rz(β)Ry(γ)Rz(δ)

        Args:
            alpha (sympy.Symbol): First angle of rotation
            beta (sympy.Symbol): Second angle of rotation
            gamma (sympy.Symbol): Third angle of rotation
            delta (sympy.Symbol): Third angle of rotation

        Raises:
            InvalidAngle if the value for one of the angles is not valid (e.g. complex number or single symbol not
            real).
        """
        if isinstance(alpha, complex) or (not isinstance(alpha, Number) and alpha.is_number and not alpha.is_real):
            raise InvalidAngle('Cannot have a complex angle for alpha!')
        if isinstance(beta, complex) or (not isinstance(beta, Number) and beta.is_number and not beta.is_real):
            raise InvalidAngle('Cannot have a complex angle for beta!')
        if isinstance(gamma, complex) or (not isinstance(gamma, Number) and gamma.is_number and not gamma.is_real):
            raise InvalidAngle('Cannot have a complex angle for gamma!')
        if isinstance(delta, complex) or (not isinstance(delta, Number) and delta.is_number and not delta.is_real):
            raise InvalidAngle('Cannot have a complex angle for delta!')

        super().__init__(alpha=alpha, beta=beta, gamma=gamma, delta=delta)

    def __str__(self):
        """
        Return the string representation of a ParametricGeneralUnitary gate.

        Returns the class name and the angle as

        .. code-block:: python

            [CLASSNAME]([ANGLE1],[ANGLE2],[ANGLE3],[ANGLE4])
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
        Return the string representation of a ParametricGeneralUnitary gate.

        Args:
            symbols (bool): No-op (only for compatibility with normal gates)
        """
        # pylint: disable=no-member
        return '{}({},{},{},{})'.format(self.klass.__name__, self.alpha, self.beta, self.gamma, self.delta)

    def tex_str(self):
        """
        Return the Latex string representation of a ParametricGeneralUnitary gate.

        Returns the class name and the angle as a subscript, i.e.

        .. code-block:: latex

            [CLASSNAME]$_[ANGLE]$
        """
        # pylint: disable=no-member
        return '{}$({},{},{},{})$'.format(
            self.klass.__name__,
            sympy.latex(self.alpha),
            sympy.latex(self.beta),
            sympy.latex(self.gamma),
            sympy.latex(self.delta),
        )

    def get_inverse(self):
        """Return the inverse of this gate."""
        # pylint: disable=no-member
        return self.__class__(-self.alpha, -self.delta, -self.gamma, -self.beta)

    def __eq__(self, other):
        """Return True if same class and same rotation angle."""
        # pylint: disable=no-member
        # Important: self.__class__ and not self.klass!
        #            (although it would probably also work)
        if isinstance(other, self.__class__):
            return (self.alpha, self.beta, self.gamma, self.delta) == (
                other.alpha,
                other.beta,
                other.gamma,
                other.delta,
            )
        return False

    def __hash__(self):
        """Compute the hash of the object."""
        return hash(str(self))

    def is_identity(self):
        """Return True if the gate is equivalent to an Identity gate."""
        # pylint: disable=no-member
        return (
            sympy.Mod(self.alpha, 2 * math.pi) == 0
            and sympy.Mod(self.beta, 4 * math.pi) == 0
            and sympy.Mod(self.gamma, 4 * math.pi) == 0
            and sympy.Mod(self.delta, 4 * math.pi) == 0
        ) or (
            sympy.Mod(self.alpha, 2 * sympy.pi) == 0
            and sympy.Mod(self.beta, 4 * sympy.pi) == 0
            and sympy.Mod(self.gamma, 4 * sympy.pi) == 0
            and sympy.Mod(self.delta, 4 * sympy.pi) == 0
        )

    @property
    def matrix(self):
        """Access to the matrix property of this gate."""
        # pylint: disable=no-member
        bdp = self.beta + self.delta
        bdm = self.beta - self.delta
        cosg = sympy.cos(self.gamma / 2)
        sing = sympy.sin(self.gamma / 2)
        return sympy.exp(1j * self.alpha) * sympy.Matrix(
            [
                [sympy.exp(-0.5j * bdp) * cosg, -sympy.exp(-0.5j * bdm) * sing],
                [sympy.exp(0.5j * bdm) * sing, sympy.exp(0.5j * bdp) * cosg],
            ]
        )


class ParametricU2Gate(ParametricGeneralUnitary):
    """Parametric U2 gate class."""

    def __str__(self):
        """
        Return the string representation of a U2Param gate.

        Returns the class name and the angle as

        .. code-block:: python

            [CLASSNAME]([ANGLE1],[ANGLE2])
        """
        return self.to_string()

    def to_string(self, symbols=False):
        """
        Return the string representation of a parametric U2 gate.

        Args:
            symbols (bool): uses the pi character and round the angle for a more user friendly display if True, full
                            angle written in radian otherwise.
        """
        # pylint: disable=no-member
        return '{}({},{})'.format(self.klass.__name__, self.beta, self.delta)

    def tex_str(self):
        """
        Return the LaTeX string representation of a parametric U2 gate.

        Returns the class name and the angles as a subscript, i.e.

        .. code-block:: latex

            [CLASSNAME]$_{[ANGLE1],[ANGLE2]$
        """
        # pylint: disable=no-member
        return "{}$({},{})$".format(self.klass.__name__, sympy.latex(self.beta), sympy.latex(self.delta))


class ParametricU3Gate(ParametricGeneralUnitary):
    """Parametric U3 gate class."""

    def __str__(self):
        """
        Return the string representation of a U3Param gate.

        Returns the class name and the angle as

        .. code-block:: python

            [CLASSNAME]([ANGLE1],[ANGLE2],[ANGLE3])
        """
        return self.to_string()

    def to_string(self, symbols=False):
        """
        Return the string representation of a parametric U3 gate.

        Args:
            symbols (bool): uses the pi character and round the angle for a more user friendly display if True, full
                            angle written in radian otherwise.
        """
        # pylint: disable=no-member
        return '{}({},{},{})'.format(self.klass.__name__, self.gamma, self.beta, self.delta)

    def tex_str(self):
        """
        Return the LaTeX string representation of a parametric U3 gate.

        Returns the class name and the angles as a subscript, i.e.

        .. code-block:: latex

            [CLASSNAME]$_[ANGLE]$
        """
        # pylint: disable=no-member
        return "{}$({},{},{})$".format(
            self.klass.__name__, sympy.latex(self.gamma), sympy.latex(self.beta), sympy.latex(self.delta)
        )
