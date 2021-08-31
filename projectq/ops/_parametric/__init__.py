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

"""Parametric gate classes for ProjectQ"""

from ._parametric_base import (
    InvalidAngle,
    ParametricAngleGate,
    ParametricGate,
    ParametricGateCmplx,
    ParametricGateReal,
    ParametricPhaseGate,
    ParametricRotationGate,
)
from ._parametric_two_angles import ParametricAngleGate2, ParametricPhaseGate2
from ._unitary import ParametricGeneralUnitary, ParametricU2Gate, ParametricU3Gate
