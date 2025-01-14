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
"""
Contains functions/classes to handle OpenQASM
"""

try:
    from ._parse_qasm_qiskit import read_qasm_file, read_qasm_str
except ImportError:  # pragma: no cover
    try:
        from ._parse_qasm_pyparsing import read_qasm_file, read_qasm_str
    except ImportError:
        ERROR_MSG = (
            'Unable to import either qiskit or pyparsing\nPlease install either of them if you want to use '
            'projectq.libs.qasm (e.g. using the command python -m pip install projectq[qiskit])'
        )

        def read_qasm_file(eng, filename):
            """
            Dummy implementation
            """
            # pylint: disable=unused-argument
            raise RuntimeError(ERROR_MSG)

        def read_qasm_str(eng, qasm_str):
            """
            Dummy implementation
            """
            # pylint: disable=unused-argument
            raise RuntimeError(ERROR_MSG)
