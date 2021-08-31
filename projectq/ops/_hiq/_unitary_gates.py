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

"""Module containing the definitions of general unitary and related gates."""


import cmath
import math
import unicodedata

import numpy as np
from sympy.core.basic import Basic as SympyBase

from .._base import (
    ANGLE_PRECISION,
    ANGLE_TOLERANCE,
    BasicGate,
    DispatchGateClass,
    R,
    RNum,
    RParam,
)
from .._parametric import ParametricGeneralUnitary, ParametricU2Gate, ParametricU3Gate


def _round_angle(angle, mod_pi):
    rounded_angle = round(float(angle) % (mod_pi * math.pi), ANGLE_PRECISION)
    print(rounded_angle, mod_pi * math.pi - ANGLE_TOLERANCE, ANGLE_TOLERANCE)
    if rounded_angle >= mod_pi * math.pi - ANGLE_TOLERANCE or rounded_angle <= ANGLE_TOLERANCE:
        rounded_angle = 0.0
    return rounded_angle


class GeneralUnitary(BasicGate):
    """Numeric general unitary gate class."""

    def __init__(self, alpha, beta, gamma, delta):
        """
        Initialize a general unitary gate.

        U(α, β, γ, λ) := exp(iα)Rz(β)Ry(γ)Rz(δ)

        Args:
            alpha (float): First angle of rotation (saved modulo 2 * pi)
            beta (float): Second angle of rotation (saved modulo 4 * pi)
            gamma (float): Third angle of rotation (saved modulo 4 * pi)
            delta (float): Third angle of rotation (saved modulo 4 * pi)
        """
        super().__init__()

        self.alpha = _round_angle(alpha, 2)
        self.beta = _round_angle(beta, 4)
        self.gamma = _round_angle(gamma, 4)
        self.delta = _round_angle(delta, 4)

    def __str__(self):
        """
        Return the string representation of a ParametricGeneralUnitary gate.

        Returns the class name and the angle as

        .. code-block:: python

            [CLASSNAME]([ANGLE1],[ANGLE2],[ANGLE3],[ANGLE4])
        """
        return self.to_string()

    def to_string(self, symbols=False):
        """
        Return the string representation of a numeric U3 gate.

        Args:
            symbols (bool): uses the pi character and round the angle for a more user friendly display if True, full
                            angle written in radian otherwise.
        """
        if symbols:
            alpha = str(round(self.alpha / math.pi, 3)) + unicodedata.lookup("GREEK SMALL LETTER PI")
            beta = str(round(self.beta / math.pi, 3)) + unicodedata.lookup("GREEK SMALL LETTER PI")
            gamma = str(round(self.gamma / math.pi, 3)) + unicodedata.lookup("GREEK SMALL LETTER PI")
            delta = str(round(self.delta / math.pi, 3)) + unicodedata.lookup("GREEK SMALL LETTER PI")
        else:
            alpha, beta, gamma, delta = self.alpha, self.beta, self.gamma, self.delta
        return '{}({},{},{},{})'.format(self.klass.__name__, alpha, beta, gamma, delta)

    def tex_str(self):
        """
        Return the Latex string representation of a GeneralUnitary gate.

        Returns the class name and the angles as a subscript, i.e.

        .. code-block:: latex

            [CLASSNAME]$_[ANGLE]$
        """
        return str(self.klass.__name__) + "$_{{{},{},{},{}}}$".format(self.alpha, self.beta, self.gamma, self.delta)

    def get_inverse(self):
        """Return the inverse of this unitary gate."""
        return self.__class__(-self.alpha, -self.delta, -self.gamma, -self.beta)

    def __eq__(self, other):
        """Return True if same class and same rotation angle."""
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
            (self.alpha == 0.0 or self.alpha == 2 * math.pi)
            or (self.beta == 0.0 or self.beta == 4 * math.pi)
            or (self.gamma == 0.0 or self.gamma == 4 * math.pi)
            or (self.delta == 0.0 or self.delta == 4 * math.pi)
        )

    @property
    def matrix(self):
        """Access to the matrix property of this gate."""
        bdp = self.beta + self.delta
        bdm = self.beta - self.delta
        cosg = cmath.cos(self.gamma / 2)
        sing = cmath.sin(self.gamma / 2)
        return cmath.exp(1j * self.alpha) * np.matrix(
            [
                [cmath.exp(-0.5j * bdp) * cosg, -cmath.exp(-0.5j * bdm) * sing],
                [cmath.exp(0.5j * bdm) * sing, cmath.exp(0.5j * bdp) * cosg],
            ]
        )


# ==============================================================================


class U(DispatchGateClass):
    """Dispatch gate class for the general unitary gate."""

    def __new__(cls, alpha=None, beta=None, gamma=None, delta=None):
        """Create a U gate, dispatching to either a numeric or parametric implementation."""
        if None not in (alpha, beta, gamma, delta):
            if (
                isinstance(alpha, SympyBase)
                or isinstance(beta, SympyBase)
                or isinstance(gamma, SympyBase)
                or isinstance(delta, SympyBase)
            ):
                # NB: here we do not consider sympy.Float and sympy.Integer as numbers since operation on them such as
                #     +, *, etc. will lead to expressions and not simple numbers
                return super().__new__(UParam)
            return super().__new__(UNum)

        # This statement is only for copy and deepcopy operations
        return super().__new__(cls)

    def __init__(self, alpha, beta, gamma, delta):
        """Initialize a U gate, dispatching to either a numeric or parametric implementation."""
        # pylint: disable=useless-super-delegation,too-many-function-args
        super().__init__(alpha, beta, gamma, delta)


class UParam(U, ParametricGeneralUnitary):
    """Parametric U gate class."""


class UNum(U, GeneralUnitary):
    """Numeric U gate class."""


# ==============================================================================


def U1(theta):
    """
    Diagonal single-qubit gate.

    Args:
        theta (float): Angle of rotation (saved modulo 4 * pi)
    """
    return R(theta)


U1Num = RNum
U1Param = RParam

# ==============================================================================


class U2(DispatchGateClass):
    """Dispatch gate class for the U2 gate."""

    def __new__(cls, phi=None, lamda=None):
        """Create a U2 gate, dispatching to either a numeric or parametric implementation."""
        if None not in (phi, lamda):
            if isinstance(phi, SympyBase) or isinstance(lamda, SympyBase):
                # NB: here we do not consider sympy.Float and sympy.Integer as numbers since operation on them such as
                #     +, *, etc. will lead to expressions and not simple numbers
                return super().__new__(U2Param)
            return super().__new__(U2Num)

        # This statement is only for copy and deepcopy operations
        return super().__new__(cls)

    def __init__(self, phi, lamda):
        """Initialize a U2 gate, dispatching to either a numeric or parametric implementation."""
        # pylint: disable=useless-super-delegation,too-many-function-args
        super().__init__(0.5 * (phi + lamda), phi, np.pi / 2, lamda)


class U2Param(U2, ParametricU2Gate):
    """Parametric U2 gate class."""


class U2Num(U2, GeneralUnitary):
    """Numeric U2 gate class."""

    def __str__(self):
        """
        Return the string representation of a U2Num gate.

        Returns the class name and the angle as

        .. code-block:: python

            [CLASSNAME]([ANGLE1],[ANGLE2])
        """
        return self.to_string()

    def to_string(self, symbols=False):
        """
        Return the string representation of a numeric U2 gate.

        Args:
            symbols (bool): uses the pi character and round the angle for a more user friendly display if True, full
                            angle written in radian otherwise.
        """
        if symbols:
            beta = str(round(self.beta / math.pi, 3)) + unicodedata.lookup("GREEK SMALL LETTER PI")
            delta = str(round(self.delta / math.pi, 3)) + unicodedata.lookup("GREEK SMALL LETTER PI")
        else:
            beta, delta = self.beta, self.delta
        return '{}({},{})'.format(self.klass.__name__, beta, delta)

    def tex_str(self):
        """
        Return the LaTeX string representation of a numeric U2 gate.

        Returns the class name and the angles as a subscript, i.e.

        .. code-block:: latex

            [CLASSNAME]$_[ANGLE]$
        """
        return "{}$({},{})$".format(self.klass.__name__, self.beta, self.delta)


# ==============================================================================


class U3(DispatchGateClass):
    """Dispatch gate class for the U3 gate."""

    def __new__(cls, theta=None, phi=None, lamda=None):
        """Create a U3 gate, dispatching to either a numeric or parametric implementation."""
        if None not in (theta, phi, lamda):
            if isinstance(theta, SympyBase) or isinstance(phi, SympyBase) or isinstance(lamda, SympyBase):
                # NB: here we do not consider sympy.Float and sympy.Integer as numbers since operation on them such as
                #     +, *, etc. will lead to expressions and not simple numbers
                return super().__new__(U3Param)
            return super().__new__(U3Num)

        # This statement is only for copy and deepcopy operations
        return super().__new__(cls)

    def __init__(self, theta, phi, lamda):
        """Initialize a U3 gate, dispatching to either a numeric or parametric implementation."""
        # pylint: disable=useless-super-delegation,too-many-function-args
        super().__init__(0.5 * (phi + lamda), phi, theta, lamda)


class U3Param(U3, ParametricU3Gate):
    """Parametric U3 gate class."""


class U3Num(U3, GeneralUnitary):
    """Numeric U3 gate class."""

    def __str__(self):
        """
        Return the string representation of a U3Num gate.

        Returns the class name and the angle as

        .. code-block:: python

            [CLASSNAME]([ANGLE1],[ANGLE2],[ANGLE3])
        """
        return self.to_string()

    def to_string(self, symbols=False):
        """
        Return the string representation of a numeric U3 gate.

        Args:
            symbols (bool): uses the pi character and round the angle for a more user friendly display if True, full
                            angle written in radian otherwise.
        """
        # pylint: disable=no-member
        if symbols:
            gamma = str(round(self.gamma / math.pi, 3)) + unicodedata.lookup("GREEK SMALL LETTER PI")
            beta = str(round(self.beta / math.pi, 3)) + unicodedata.lookup("GREEK SMALL LETTER PI")
            delta = str(round(self.delta / math.pi, 3)) + unicodedata.lookup("GREEK SMALL LETTER PI")
        else:
            gamma, beta, delta = self.gamma, self.beta, self.delta
        return '{}({},{},{})'.format(self.klass.__name__, gamma, beta, delta)

    def tex_str(self):
        """
        Return the LaTeX string representation of a numeric U3 gate.

        Returns the class name and the angles as a subscript, i.e.

        .. code-block:: latex

            [CLASSNAME]$_[ANGLE]$
        """
        return str(self.klass.__name__) + "$({},{},{})$".format(self.gamma, self.beta, self.delta)
