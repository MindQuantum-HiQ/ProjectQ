# -*- coding: utf-8 -*-
#   Copyright 2017 ProjectQ-Framework (www.projectq.ch)
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
Definition of the basic set of quantum gates.

Contains definitions of standard gates such as
* Hadamard (H)
* Pauli-X (X / NOT)
* Pauli-Y (Y)
* Pauli-Z (Z)
* S and its inverse (S / Sdagger)
* T and its inverse (T / Tdagger)
* SqrtX gate (SqrtX)
* Swap gate (Swap)
* SqrtSwap gate (SqrtSwap)
* Entangle (Entangle)
* Phase gate (Ph)
* Rotation-X (Rx)
* Rotation-Y (Ry)
* Rotation-Z (Rz)
* Rotation-XX on two qubits (Rxx)
* Rotation-YY on two qubits (Ryy)
* Rotation-ZZ on two qubits (Rzz)
* Phase-shift (R)
* Measurement (Measure)

and meta gates, i.e.,
* Allocate / Deallocate qubits
* Flush gate (end of circuit)
* Barrier
* FlipBits
"""

import cmath
import math

import numpy as np
import sympy
from sympy.core.basic import Basic as SympyBase

from .._parametric import ParametricPhaseGate, ParametricRotationGate
from ._basics import (
    BasicGate,
    BasicPhaseGate,
    BasicRotationGate,
    ClassicalInstructionGate,
    DispatchGateClass,
    FastForwardingGate,
    SelfInverseGate,
)
from ._command import apply_command
from ._metagates import get_inverse

# This is mainly due to the class dispatching that happens for parametric gates
# pylint: disable=too-many-ancestors,no-member


class HGate(SelfInverseGate):
    """Hadamard gate class."""

    def __str__(self):
        """Return a string representation of the object."""
        return "H"

    @property
    def matrix(self):
        """Access to the matrix property of this gate."""
        return 1.0 / cmath.sqrt(2.0) * np.matrix([[1, 1], [1, -1]])


#: Shortcut (instance of) :class:`projectq.ops.HGate`
H = HGate()


class XGate(SelfInverseGate):
    """Pauli-X gate class."""

    def __str__(self):
        """Return a string representation of the object."""
        return "X"

    @property
    def matrix(self):
        """Access to the matrix property of this gate."""
        return np.matrix([[0, 1], [1, 0]])


#: Shortcut (instance of) :class:`projectq.ops.XGate`
X = NOT = XGate()


class YGate(SelfInverseGate):
    """Pauli-Y gate class."""

    def __str__(self):
        """Return a string representation of the object."""
        return "Y"

    @property
    def matrix(self):
        """Access to the matrix property of this gate."""
        return np.matrix([[0, -1j], [1j, 0]])


#: Shortcut (instance of) :class:`projectq.ops.YGate`
Y = YGate()


class ZGate(SelfInverseGate):
    """Pauli-Z gate class."""

    def __str__(self):
        """Return a string representation of the object."""
        return "Z"

    @property
    def matrix(self):
        """Access to the matrix property of this gate."""
        return np.matrix([[1, 0], [0, -1]])


#: Shortcut (instance of) :class:`projectq.ops.ZGate`
Z = ZGate()


class SGate(BasicGate):
    """S gate class."""

    @property
    def matrix(self):
        """Access to the matrix property of this gate."""
        return np.matrix([[1, 0], [0, 1j]])

    def __str__(self):
        """Return a string representation of the object."""
        return "S"


#: Shortcut (instance of) :class:`projectq.ops.SGate`
S = SGate()
#: Inverse (and shortcut) of :class:`projectq.ops.SGate`
Sdag = Sdagger = get_inverse(S)


class TGate(BasicGate):
    """T gate class."""

    @property
    def matrix(self):
        """Access to the matrix property of this gate."""
        return np.matrix([[1, 0], [0, cmath.exp(1j * cmath.pi / 4)]])

    def __str__(self):
        """Return a string representation of the object."""
        return "T"


#: Shortcut (instance of) :class:`projectq.ops.TGate`
T = TGate()
#: Inverse (and shortcut) of :class:`projectq.ops.TGate`
Tdag = Tdagger = get_inverse(T)


class SqrtXGate(BasicGate):
    """Square-root X gate class."""

    @property
    def matrix(self):
        """Access to the matrix property of this gate."""
        return 0.5 * np.matrix([[1 + 1j, 1 - 1j], [1 - 1j, 1 + 1j]])

    def tex_str(self):  # pylint: disable=no-self-use
        """Return the Latex string representation of a SqrtXGate."""
        return r'$\sqrt{X}$'

    def __str__(self):
        """Return a string representation of the object."""
        return "SqrtX"


#: Shortcut (instance of) :class:`projectq.ops.SqrtXGate`
SqrtX = SqrtXGate()


class SwapGate(SelfInverseGate):
    """Swap gate class (swaps 2 qubits)."""

    def __init__(self):
        """Initialize a Swap gate."""
        super().__init__()
        self.interchangeable_qubit_indices = [[0, 1]]

    def __str__(self):
        """Return a string representation of the object."""
        return "Swap"

    @property
    def matrix(self):
        """Access to the matrix property of this gate."""
        # fmt: off
        return np.matrix([[1, 0, 0, 0],
                          [0, 0, 1, 0],
                          [0, 1, 0, 0],
                          [0, 0, 0, 1]])
        # fmt: on


#: Shortcut (instance of) :class:`projectq.ops.SwapGate`
Swap = SwapGate()


class SqrtSwapGate(BasicGate):
    """Square-root Swap gate class."""

    def __init__(self):
        """Initialize a SqrtSwap gate."""
        super().__init__()
        self.interchangeable_qubit_indices = [[0, 1]]

    def __str__(self):
        """Return a string representation of the object."""
        return "SqrtSwap"

    @property
    def matrix(self):
        """Access to the matrix property of this gate."""
        return np.matrix(
            [
                [1, 0, 0, 0],
                [0, 0.5 + 0.5j, 0.5 - 0.5j, 0],
                [0, 0.5 - 0.5j, 0.5 + 0.5j, 0],
                [0, 0, 0, 1],
            ]
        )


#: Shortcut (instance of) :class:`projectq.ops.SqrtSwapGate`
SqrtSwap = SqrtSwapGate()


class EntangleGate(BasicGate):
    """
    Entangle gate class.

    (Hadamard on first qubit, followed by CNOTs applied to all other qubits).
    """

    def __str__(self):
        """Return a string representation of the object."""
        return "Entangle"


#: Shortcut (instance of) :class:`projectq.ops.EntangleGate`
Entangle = EntangleGate()


class DispatchAngleGateClass(DispatchGateClass):
    """Dispatch base class for angle gate classes (phase- and rotation- gates)."""

    def __new__(cls, NumClass, ParamClass, angle):  # noqa: N803
        """Create an AngleGateClass gate, dispatching to either a numeric or parametric implementation."""
        if angle is not None:
            if isinstance(angle, SympyBase):
                # NB: here we do not consider sympy.Float and sympy.Integer as
                # numbers since operation on them such as +, *, etc. will lead
                # to expressions and not simple numbers
                return super().__new__(ParamClass)
            return super().__new__(NumClass)

        # This statement is only for copy and deepcopy operations
        return super().__new__(cls)

    def __init__(self, angle):
        """Initialize an AngleGateClass gate, dispatching to either a numeric or parametric implementation."""
        # pylint: disable=useless-super-delegation,too-many-function-args
        # This is tricky for the linters, as this will in practice call the __init__ method, not of DispatchGateClass
        # but of the class defined in the real class. See e.g. PhParam and Ph below.
        super().__init__(angle)


# Dispatch class for R gates
class Ph(DispatchAngleGateClass):
    """Phase gate (global phase)."""

    def __new__(cls, angle=None):
        """Create a Ph gate, dispatching to either a numeric or parametric implementation."""
        return super().__new__(cls, PhNum, PhParam, angle)


class PhParam(Ph, ParametricPhaseGate):
    """Parametric phase gate realisation."""

    @property
    def matrix(self):
        """Access to the matrix property of this gate."""
        return sympy.Matrix([[sympy.exp(1j * self.angle), 0], [0, sympy.exp(1j * self.angle)]])


class PhNum(Ph, BasicPhaseGate):
    """Numeric phase gate realisation."""

    @property
    def matrix(self):
        """Access to the matrix property of this gate."""
        return np.matrix([[cmath.exp(1j * self.angle), 0], [0, cmath.exp(1j * self.angle)]])


# Dispatch class for Rx gates
class Rx(DispatchAngleGateClass):
    """RotationX gate class."""

    def __new__(cls, angle=None):
        """Create an Rx gate, dispatching to either a numeric or parametric implementation."""
        return super().__new__(cls, RxNum, RxParam, angle)


class RxParam(Rx, ParametricRotationGate):
    """Parametric rotationX gate class."""

    @property
    def matrix(self):
        """Access to the matrix property of this gate."""
        return sympy.Matrix(
            [
                [sympy.cos(0.5 * self.angle), -1j * sympy.sin(0.5 * self.angle)],
                [-1j * sympy.sin(0.5 * self.angle), sympy.cos(0.5 * self.angle)],
            ]
        )


class RxNum(Rx, BasicRotationGate):
    """Numeric rotationX gate class."""

    @property
    def matrix(self):
        """Access to the matrix property of this gate."""
        return np.matrix(
            [
                [math.cos(0.5 * self.angle), -1j * math.sin(0.5 * self.angle)],
                [-1j * math.sin(0.5 * self.angle), math.cos(0.5 * self.angle)],
            ]
        )


# Dispatch class for Ry gates
class Ry(DispatchAngleGateClass):
    """RotationY gate class."""

    def __new__(cls, angle=None):
        """Create an Ry gate, dispatching to either a numeric or parametric implementation."""
        return super().__new__(cls, RyNum, RyParam, angle)


class RyParam(Ry, ParametricRotationGate):
    """Parametric rotationY gate class."""

    @property
    def matrix(self):
        """Access to the matrix property of this gate."""
        return sympy.Matrix(
            [
                [sympy.cos(0.5 * self.angle), -sympy.sin(0.5 * self.angle)],
                [sympy.sin(0.5 * self.angle), sympy.cos(0.5 * self.angle)],
            ]
        )


class RyNum(Ry, BasicRotationGate):
    """Numeric rotationY gate class."""

    @property
    def matrix(self):
        """Access to the matrix property of this gate."""
        return np.matrix(
            [
                [math.cos(0.5 * self.angle), -math.sin(0.5 * self.angle)],
                [math.sin(0.5 * self.angle), math.cos(0.5 * self.angle)],
            ]
        )


# Dispatch class for Rz gates
class Rz(DispatchAngleGateClass):
    """RotationZ gate class."""

    def __new__(cls, angle=None):
        """Create an Rz gate, dispatching to either a numeric or parametric implementation."""
        return super().__new__(cls, RzNum, RzParam, angle)


class RzParam(Rz, ParametricRotationGate):
    """Parametric rotationZ gate class."""

    @property
    def matrix(self):
        """Access to the matrix property of this gate."""
        return sympy.Matrix([[sympy.exp(-0.5 * 1j * self.angle), 0], [0, sympy.exp(0.5 * 1j * self.angle)]])


class RzNum(Rz, BasicRotationGate):
    """Numeric rotationZ gate class."""

    @property
    def matrix(self):
        """Access to the matrix property of this gate."""
        return np.matrix(
            [
                [cmath.exp(-0.5 * 1j * self.angle), 0],
                [0, cmath.exp(0.5 * 1j * self.angle)],
            ]
        )


# Dispatch class for Rxx gates
class Rxx(DispatchAngleGateClass):
    """RotationXX gate class."""

    def __new__(cls, angle=None):
        """Create an Rxx gate, dispatching to either a numeric or parametric implementation."""
        return super().__new__(cls, RxxNum, RxxParam, angle)


class RxxParam(Rxx, ParametricRotationGate):
    """Parametric rotationXX gate class."""

    @property
    def matrix(self):
        """Access to the matrix property of this gate."""
        return sympy.Matrix(
            [
                [sympy.cos(0.5 * self.angle), 0, 0, -1j * sympy.sin(0.5 * self.angle)],
                [0, sympy.cos(0.5 * self.angle), -1j * sympy.sin(0.5 * self.angle), 0],
                [0, -1j * sympy.sin(0.5 * self.angle), sympy.cos(0.5 * self.angle), 0],
                [-1j * sympy.sin(0.5 * self.angle), 0, 0, sympy.cos(0.5 * self.angle)],
            ]
        )


class RxxNum(Rxx, BasicRotationGate):
    """Numeric rotationXX gate class."""

    @property
    def matrix(self):
        """Access to the matrix property of this gate."""
        return np.matrix(
            [
                [cmath.cos(0.5 * self.angle), 0, 0, -1j * cmath.sin(0.5 * self.angle)],
                [0, cmath.cos(0.5 * self.angle), -1j * cmath.sin(0.5 * self.angle), 0],
                [0, -1j * cmath.sin(0.5 * self.angle), cmath.cos(0.5 * self.angle), 0],
                [-1j * cmath.sin(0.5 * self.angle), 0, 0, cmath.cos(0.5 * self.angle)],
            ]
        )


# Dispatch class for Ryy gates
class Ryy(DispatchAngleGateClass):
    """RotationYY gate class."""

    def __new__(cls, angle=None):
        """Create an Ryy gate, dispatching to either a numeric or parametric implementation."""
        return super().__new__(cls, RyyNum, RyyParam, angle)


class RyyParam(Ryy, ParametricRotationGate):
    """Parametric rotationYY gate class."""

    @property
    def matrix(self):
        """Access to the matrix property of this gate."""
        return sympy.Matrix(
            [
                [sympy.cos(0.5 * self.angle), 0, 0, 1j * sympy.sin(0.5 * self.angle)],
                [0, sympy.cos(0.5 * self.angle), -1j * sympy.sin(0.5 * self.angle), 0],
                [0, -1j * sympy.sin(0.5 * self.angle), sympy.cos(0.5 * self.angle), 0],
                [1j * sympy.sin(0.5 * self.angle), 0, 0, sympy.cos(0.5 * self.angle)],
            ]
        )


class RyyNum(Ryy, BasicRotationGate):
    """Numeric rotationYY gate class."""

    @property
    def matrix(self):
        """Access to the matrix property of this gate."""
        return np.matrix(
            [
                [cmath.cos(0.5 * self.angle), 0, 0, 1j * cmath.sin(0.5 * self.angle)],
                [0, cmath.cos(0.5 * self.angle), -1j * cmath.sin(0.5 * self.angle), 0],
                [0, -1j * cmath.sin(0.5 * self.angle), cmath.cos(0.5 * self.angle), 0],
                [1j * cmath.sin(0.5 * self.angle), 0, 0, cmath.cos(0.5 * self.angle)],
            ]
        )


# Dispatch class for Rzz gates
class Rzz(DispatchAngleGateClass):
    """RotationZZ gate class."""

    def __new__(cls, angle=None):
        """Create an Rzz gate, dispatching to either a numeric or parametric implementation."""
        return super().__new__(cls, RzzNum, RzzParam, angle)


class RzzParam(Rzz, ParametricRotationGate):
    """Parametric rotationZZ gate class."""

    @property
    def matrix(self):
        """Access to the matrix property of this gate."""
        return sympy.Matrix(
            [
                [sympy.exp(-0.5 * 1j * self.angle), 0, 0, 0],
                [0, sympy.exp(0.5 * 1j * self.angle), 0, 0],
                [0, 0, sympy.exp(0.5 * 1j * self.angle), 0],
                [0, 0, 0, sympy.exp(-0.5 * 1j * self.angle)],
            ]
        )


class RzzNum(Rzz, BasicRotationGate):
    """Numeric rotationZZ gate class."""

    @property
    def matrix(self):
        """Access to the matrix property of this gate."""
        return np.matrix(
            [
                [cmath.exp(-0.5 * 1j * self.angle), 0, 0, 0],
                [0, cmath.exp(0.5 * 1j * self.angle), 0, 0],
                [0, 0, cmath.exp(0.5 * 1j * self.angle), 0],
                [0, 0, 0, cmath.exp(-0.5 * 1j * self.angle)],
            ]
        )


# Dispatch class for R gates
class R(DispatchAngleGateClass):
    """Phase-shift gate (equivalent to Rz up to a global phase)."""

    def __new__(cls, angle=None):
        """Create an R gate, dispatching to either a numeric or parametric implementation."""
        return super().__new__(cls, RNum, RParam, angle)


class RParam(R, ParametricPhaseGate):
    """Parametric phase-shift gate (equivalent to Rz up to a global phase)."""

    @property
    def matrix(self):
        """Access to the matrix property of this gate."""
        return sympy.Matrix([[1, 0], [0, sympy.exp(1j * self.angle)]])


class RNum(R, BasicPhaseGate):
    """Numeric phase-shift gate (equivalent to Rz up to a global phase)."""

    @property
    def matrix(self):
        """Access to the matrix property of this gate."""
        return np.matrix([[1, 0], [0, cmath.exp(1j * self.angle)]])


class FlushGate(FastForwardingGate):
    """
    Flush gate (denotes the end of the circuit).

    Note:
        All compiler engines (cengines) which cache/buffer gates are obligated to flush and send all gates to the next
        compiler engine (followed by the flush command).

    Note:
        This gate is sent when calling

        .. code-block:: python

            eng.flush()

        on the MainEngine `eng`.
    """

    def __str__(self):
        """Return a string representation of the object."""
        return ""


class MeasureGate(FastForwardingGate):
    """Measurement gate class (for single qubits)."""

    def __str__(self):
        """Return a string representation of the object."""
        return "Measure"

    def __or__(self, qubits):
        """
        Operator| overload which enables the syntax Gate | qubits.

        Previously (ProjectQ <= v0.3.6) MeasureGate/Measure was allowed to be applied to any number of quantum
        registers. Now the MeasureGate/Measure is strictly a single qubit gate.

        Raises:
            RuntimeError: Since ProjectQ v0.6.0 if the gate is applied to multiple qubits.
        """
        num_qubits = 0
        for qureg in self.make_tuple_of_qureg(qubits):
            for qubit in qureg:
                num_qubits += 1
                cmd = self.generate_command(([qubit],))
                apply_command(cmd)
        if num_qubits > 1:  # pragma: no cover
            raise RuntimeError('Measure is a single qubit gate. Use All(Measure) | qureg instead')


#: Shortcut (instance of) :class:`projectq.ops.MeasureGate`
Measure = MeasureGate()


class AllocateQubitGate(ClassicalInstructionGate):
    """Qubit allocation gate class."""

    def __str__(self):
        """Return a string representation of the object."""
        return "Allocate"

    def get_inverse(self):
        """Return the inverse of this gate."""
        return DeallocateQubitGate()


#: Shortcut (instance of) :class:`projectq.ops.AllocateQubitGate`
Allocate = AllocateQubitGate()


class DeallocateQubitGate(FastForwardingGate):
    """Qubit deallocation gate class."""

    def __str__(self):
        """Return a string representation of the object."""
        return "Deallocate"

    def get_inverse(self):
        """Return the inverse of this gate."""
        return Allocate


#: Shortcut (instance of) :class:`projectq.ops.DeallocateQubitGate`
Deallocate = DeallocateQubitGate()


class AllocateDirtyQubitGate(ClassicalInstructionGate):
    """Dirty qubit allocation gate class."""

    def __str__(self):
        """Return a string representation of the object."""
        return "AllocateDirty"

    def get_inverse(self):
        """Return the inverse of this gate."""
        return Deallocate


#: Shortcut (instance of) :class:`projectq.ops.AllocateDirtyQubitGate`
AllocateDirty = AllocateDirtyQubitGate()


class BarrierGate(BasicGate):
    """Barrier gate class."""

    def __str__(self):
        """Return a string representation of the object."""
        return "Barrier"

    def get_inverse(self):
        """Return the inverse of this gate."""
        return Barrier


#: Shortcut (instance of) :class:`projectq.ops.BarrierGate`
Barrier = BarrierGate()


class FlipBits(SelfInverseGate):
    """Gate for flipping qubits by means of XGates."""

    def __init__(self, bits_to_flip):
        """
        Initialize a FlipBits gate.

        Example:
            .. code-block:: python

                qureg = eng.allocate_qureg(2)
                FlipBits([0, 1]) | qureg

        Args:
            bits_to_flip(list[int]|list[bool]|str|int): int or array of 0/1, True/False, or string of 0/1 identifying
               the qubits to flip.  In case of int, the bits to flip are determined from the binary digits, with the
               least significant bit corresponding to qureg[0]. If bits_to_flip is negative, exactly all qubits which
               would not be flipped for the input -bits_to_flip-1 are flipped, i.e., bits_to_flip=-1 flips all qubits.
        """
        super().__init__()
        if isinstance(bits_to_flip, int):
            self.bits_to_flip = bits_to_flip
        else:
            self.bits_to_flip = 0
            for i in reversed(list(bits_to_flip)):
                bit = 0b1 if i == '1' or i == 1 or i is True else 0b0
                self.bits_to_flip = (self.bits_to_flip << 1) | bit

    def __str__(self):
        """Return a string representation of the object."""
        return "FlipBits(" + str(self.bits_to_flip) + ")"

    def __or__(self, qubits):
        """Operator| overload which enables the syntax Gate | qubits."""
        quregs_tuple = self.make_tuple_of_qureg(qubits)
        if len(quregs_tuple) > 1:
            raise ValueError(
                self.__str__() + ' can only be applied to qubits,'
                'quregs, arrays of qubits, and tuples with one'
                'individual qubit'
            )
        for qureg in quregs_tuple:
            for i, qubit in enumerate(qureg):
                if (self.bits_to_flip >> i) & 1:
                    XGate() | qubit

    def __eq__(self, other):
        """Equal operator."""
        if isinstance(other, self.__class__):
            return self.bits_to_flip == other.bits_to_flip
        return False

    def __hash__(self):
        """Compute the hash of the object."""
        return hash(self.__str__())
