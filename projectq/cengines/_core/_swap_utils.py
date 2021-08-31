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

"""Contain some utilities required by some mappers."""


def return_swap_depth(swaps):
    """
    Return the circuit depth to execute these swaps.

    Args:
        swaps(list of tuples): Each tuple contains two integers representing the two IDs of the qubits involved in the
                               Swap operation.
    Returns:
        Circuit depth to execute these swaps.
    """
    depth_of_qubits = {}
    for qb0_id, qb1_id in swaps:
        if qb0_id not in depth_of_qubits:
            depth_of_qubits[qb0_id] = 0
        if qb1_id not in depth_of_qubits:
            depth_of_qubits[qb1_id] = 0
        max_depth = max(depth_of_qubits[qb0_id], depth_of_qubits[qb1_id])
        depth_of_qubits[qb0_id] = max_depth + 1
        depth_of_qubits[qb1_id] = max_depth + 1
    return max(list(depth_of_qubits.values()) + [0])
