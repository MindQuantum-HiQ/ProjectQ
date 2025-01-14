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

"""Definition of classes to support gate decomposition using compiler engines."""

from ._decomposition_rule import DecompositionRule
from ._decomposition_rule_set import DecompositionRuleSet
from ._replacer import AutoReplacer, InstructionFilter, NoGateDecompositionError

__all__ = ['DecompositionRule', 'DecompositionRuleSet', 'AutoReplacer', 'InstructionFilter', 'NoGateDecompositionError']
