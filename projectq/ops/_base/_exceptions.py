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

"""Contains some exceptions that are common to most projectq.ops modules."""


class NotMergeable(Exception):
    """
    Exception thrown when trying to merge two gates which are not mergeable.

    This exception is also thrown if the merging is not implemented (yet)).
    """


class NotInvertible(Exception):
    """
    Exception thrown when trying to invert a gate which is not invertable.

    This exception is also thrown if the inverse is not implemented (yet).
    """
