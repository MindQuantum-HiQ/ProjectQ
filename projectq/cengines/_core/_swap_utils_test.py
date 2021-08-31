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

from . import return_swap_depth


def test_return_swap_depth():
    swaps = []
    assert return_swap_depth(swaps) == 0
    swaps += [(0, 1), (0, 1), (1, 2)]
    assert return_swap_depth(swaps) == 3
    swaps.append((2, 3))
    assert return_swap_depth(swaps) == 4
