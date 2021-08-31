# -*- coding: utf-8 -*-
#   Copyright 2020 ProjectQ-Framework (www.projectq.ch)
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
"""Contain definitions of the fermionic simulation gate."""

import cmath
import math

import numpy as np
import sympy
from sympy.core.basic import Basic as SympyBase

from .._base import BasicPhaseGate2, DispatchGateClass
from .._parametric import ParametricPhaseGate2

# This is mainly due to the class dispatching that happens for parametric gates
# pylint: disable=too-many-ancestors,no-member

# ==============================================================================


def _cos(angle):
    if isinstance(angle, SympyBase):
        return sympy.cos(angle)
    return math.cos(angle)


def _sin(angle):
    if isinstance(angle, SympyBase):
        return sympy.sin(angle)
    return math.sin(angle)


def _exp(arg):
    if isinstance(arg, SympyBase):
        return sympy.exp(arg)
    return cmath.exp(arg)


# ==============================================================================


class fSim(DispatchGateClass):
    """Fermionic simulation gate."""

    def __new__(cls, theta=None, phi=None):
        """Create an fSim gate, dispatching to either a numeric or parametric implementation."""
        if None not in (theta, phi):
            if isinstance(theta, SympyBase) or isinstance(phi, SympyBase):
                # NB: here we do not consider sympy.Float and sympy.Integer as
                # numbers since operation on them such as +, *, etc. will lead
                # to expressions and not simple numbers
                return super().__new__(fSimParam)
            return super().__new__(fSimNum)

        # This statement is only for copy and deepcopy operations
        return super().__new__(cls)

    def __init__(self, theta, phi):
        """Initialize an fSim gate, dispatching to either a numeric or parametric implementation."""
        # pylint: disable=useless-super-delegation,too-many-function-args
        super().__init__(theta, phi)


# ------------------------------------------------------------------------------


class fSimParam(fSim, ParametricPhaseGate2):
    """Parametric fSim gate class."""

    @property
    def matrix(self):
        """Access to the matrix property of this gate."""
        return sympy.Matrix(
            [
                [1, 0, 0, 0],
                [0, _cos(self.theta), -1j * _sin(self.theta), 0],
                [0, -1j * _sin(self.theta), _cos(self.theta), 0],
                [0, 0, 0, _exp(-1j * self.phi)],
            ]
        )


class fSimNum(fSim, BasicPhaseGate2):
    """Numeric fSim gate class."""

    _mod_pi_theta = 4
    _mod_pi_phi = 4

    @property
    def matrix(self):
        """Access to the matrix property of this gate."""
        return np.matrix(
            [
                [1, 0, 0, 0],
                [0, math.cos(self.theta), -1j * math.sin(self.theta), 0],
                [0, -1j * math.sin(self.theta), math.cos(self.theta), 0],
                [0, 0, 0, cmath.exp(-1j * self.phi)],
            ]
        )


# ==============================================================================
