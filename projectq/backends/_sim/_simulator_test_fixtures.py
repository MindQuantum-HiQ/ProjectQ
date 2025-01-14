# -*- coding: utf-8 -*-
#   Copyright 2021 ProjectQ-Framework (www.projectq.ch)
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
# pylint: skip-file

"""Test fixtures for simulator tests."""

import pytest

from projectq.cengines import BasicMapperEngine


@pytest.fixture(params=["mapper", "no_mapper"])
def mapper(request):
    """Add a mapper which changes qubit ids by adding 1."""
    if request.param == "mapper":

        class TrivialMapper(BasicMapperEngine):
            """Trivial mapper class."""

            def __init__(self):
                """Initialize a TrivialMapper object."""
                super().__init__()
                self.current_mapping = {}

            def receive(self, command_list):
                """Receive a list of commands and send them to the next engine."""
                for cmd in command_list:
                    for qureg in cmd.all_qubits:
                        for qubit in qureg:
                            if qubit.id == -1:
                                continue
                            elif qubit.id not in self.current_mapping:
                                previous_map = self.current_mapping
                                previous_map[qubit.id] = qubit.id + 1
                                self.current_mapping = previous_map
                    self._send_cmd_with_mapped_ids(cmd)

        return TrivialMapper()
    if request.param == "no_mapper":
        return None
