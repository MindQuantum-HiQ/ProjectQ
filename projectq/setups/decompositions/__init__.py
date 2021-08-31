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

"""Definition of all basic gate decomposition rules."""

import os
import pkgutil
import sys
from importlib import import_module

# Allow extending this namespace.
__path__ = pkgutil.extend_path(__path__, __name__)


all_defined_decomposition_rules = []
for (_, name, _) in pkgutil.iter_modules([os.path.dirname(__file__)]):
    if name.endswith('test'):
        continue
    imported_module = import_module('.' + name, package=__name__)
    setattr(sys.modules[__name__], name, imported_module)
    all_defined_decomposition_rules.extend(imported_module.all_defined_decomposition_rules)
