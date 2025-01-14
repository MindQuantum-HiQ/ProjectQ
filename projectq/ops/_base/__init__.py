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

"""All the basic gates (operations) for ProjectQ"""

from ._basics import (
    ANGLE_PRECISION,
    ANGLE_TOLERANCE,
    ATOL,
    RTOL,
    BasicGate,
    BasicMathGate,
    BasicPhaseGate,
    BasicRotationGate,
    ClassicalInstructionGate,
    FastForwardingGate,
    MatrixGate,
    NotInvertible,
    NotMergeable,
    SelfInverseGate,
)
from ._command import Command, CtrlAll, IncompatibleControlState, apply_command
from ._gates import *
from ._metagates import (
    All,
    C,
    ControlledGate,
    DaggeredGate,
    Tensor,
    get_inverse,
    is_identity,
)
from ._qaagate import QAA
from ._qftgate import QFT, QFTGate
from ._qpegate import QPE
from ._qubit_operator import QubitOperator
from ._shortcuts import *
from ._state_prep import StatePreparation
from ._time_evolution import TimeEvolution
from ._two_angles import BasicAngleGate2, BasicPhaseGate2
from ._uniformly_controlled_rotation import UniformlyControlledRy, UniformlyControlledRz
