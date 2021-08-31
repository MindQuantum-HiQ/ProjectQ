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
ProjectQ backends classes.
Contains back-ends for ProjectQ.
This includes:
* a debugging tool to print all received commands (CommandPrinter)
* a resource counter (counts gates and keeps track of the maximal width of the
  circuit)
"""
from ._exceptions import (
    DeviceNotHandledError,
    DeviceOfflineError,
    DeviceTooSmall,
    InvalidCommandError,
    JobSubmissionError,
    MidCircuitMeasurementError,
    RequestTimeoutError,
)
from ._json_converter import JSONBackend, calculate_circuit_depth
from ._parametric_backend import DestinationEngineGateUnsupported, ParametricGateBackend
from ._printer import CommandPrinter
from ._qasm import OpenQASMBackend
from ._resource import ResourceCounter
