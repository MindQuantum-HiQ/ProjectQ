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

"""ProjectQ module containing all basic gates (operations)"""

import importlib
import pkgutil
from pathlib import Path

# Allow extending this namespace.
__path__ = pkgutil.extend_path(__path__, __name__)

from ._base import *

for (_, pkg_name, _) in pkgutil.iter_modules(path=__path__):
    if pkg_name != '_base':
        imported_module = importlib.import_module('.' + pkg_name, package=__name__)

        if hasattr(imported_module, '__all__'):
            for symbol_name in imported_module.__all__:
                globals().setdefault(symbol_name, getattr(imported_module, symbol_name))
        else:
            for attr_name in dir(imported_module):
                globals().setdefault(attr_name, getattr(imported_module, attr_name))
