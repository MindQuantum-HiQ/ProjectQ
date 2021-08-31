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

"""Contains definitions of the fermionic simulation gate."""

import math
import unicodedata

from ._basics import ANGLE_PRECISION, ANGLE_TOLERANCE, BasicGate
from ._exceptions import NotMergeable

# ==============================================================================


class BasicAngleGate2(BasicGate):
    """
    Defines a base class of a gate with two angle parameters.

    A rotation gate has a continuous parameter (the angle), labeled 'angle' / self.angle. Its inverse is the same gate
    with the negated argument.  Rotation gates of the same class can be merged by adding the angles.
    The continuous parameter is modulo _mod_pi * pi, self.angle is in the interval [0, _mod_pi * pi).
    """

    _mod_pi_theta = None  # Needs to be defined by child classes
    _mod_pi_phi = None  # Needs to be defined by child classes

    def __init__(self, theta, phi):
        """
        Initialize a basic angle gate.

        Args:
            angle (float): Angle of rotation (saved modulo _mod_pi * pi)
        """
        super().__init__()
        rounded_theta = round(float(theta) % (self.__class__._mod_pi_theta * math.pi), ANGLE_PRECISION)
        if rounded_theta > self.__class__._mod_pi_theta * math.pi - ANGLE_TOLERANCE:
            rounded_theta = 0.0
        rounded_phi = round(float(phi) % (self.__class__._mod_pi_phi * math.pi), ANGLE_PRECISION)
        if rounded_phi > self.__class__._mod_pi_phi * math.pi - ANGLE_TOLERANCE:
            rounded_phi = 0.0
        self.theta = rounded_theta
        self.phi = rounded_phi

    def __str__(self):
        """
        Return the string representation of a BasicRotationGate.

        Returns the class name and the angle as

        .. code-block:: python

            [CLASSNAME]([ANGLE])
        """
        return self.to_string()

    def to_string(self, symbols=False):
        """
        Return the string representation of a BasicRotationGate.

        Args:
            symbols (bool): uses the pi character and round the angle for a more user friendly display if True, full
                            angle written in radian otherwise.
        """
        # pylint: disable=protected-access
        if symbols:
            theta = str(round(self.theta / math.pi, 3)) + unicodedata.lookup("GREEK SMALL LETTER PI")
            phi = str(round(self.phi / math.pi, 3)) + unicodedata.lookup("GREEK SMALL LETTER PI")
        else:
            theta, phi = self.theta, self.phi

        return '{}({},{})'.format(self.klass.__name__, theta, phi)

    def get_inverse(self):
        """Return the inverse of this rotation gate (negate the angle, return new object)."""
        # pylint: disable=protected-access
        if self.is_identity():
            return self.__class__(0, 0)
        return self.__class__(
            -self.theta + self.__class__._mod_pi_theta * math.pi, -self.phi + self.__class__._mod_pi_phi * math.pi
        )

    def get_merged(self, other):
        """
        Return self merged with another gate.

        Default implementation handles rotation gate of the same type, where angles are simply added.

        Args:
            other: Rotation gate of same type.

        Raises:
            NotMergeable: For non-rotation gates or rotation gates of different type.

        Returns:
            New object representing the merged gates.
        """
        # NB: allow merging of parametric and numeric classes -> self.klass
        if isinstance(other, self.klass):
            return self.klass(self.theta + other.theta, self.phi + other.phi)
        raise NotMergeable("Can't merge different types of rotation gates.")

    def __eq__(self, other):
        """Return True if same class and same rotation angle."""
        # Important: self.__class__ and not self.klass!
        #            (although it should also work)
        if isinstance(other, self.klass):
            return self.theta == other.theta and self.phi == other.phi
        return False

    def __hash__(self):
        """Compute the hash of the object."""
        return hash(str(self))

    def is_identity(self):
        """Return True if the gate is equivalent to an Identity gate."""
        # pylint: disable=protected-access
        return (self.theta == 0.0 or self.theta == self.__class__._mod_pi_theta * math.pi) and (
            self.phi == 0.0 or self.phi == self.__class__._mod_pi_phi * math.pi
        )


# ==============================================================================


class BasicPhaseGate2(BasicAngleGate2):
    """
    Defines a base class of a phase gate.

    A phase gate has two continuous parameter (the angles), labeled 'theta' / self.theta and 'phi' / self.phi. Its
    inverse is the same gate with the negated argument.
    Phase gates of the same class can be merged by adding the angles.  The continuous parameters are modulo 2 * pi,
    self.theta and self.phi are in the interval [0, 2 * pi).
    """

    _mod_pi_theta = 2
    _mod_pi_phi = 2

    def tex_str(self):
        """
        Return the Latex string representation of a BasicRotationGate.

        Returns the class name and the angle as a subscript, i.e.

        .. code-block:: latex

            [CLASSNAME]$_[ANGLE]$
        """
        return '{}$({}\\pi,{}\\pi)$'.format(
            self.klass.__name__, round(self.theta / math.pi, 3), round(self.phi / math.pi, 3)
        )
