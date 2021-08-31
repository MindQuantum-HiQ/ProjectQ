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
"""Tests for _qubit_operator.py."""
import cmath
import copy
import math
from numbers import Number

import numpy
import pytest
import sympy
from sympy.core.basic import Basic as SympyBase

from projectq import MainEngine
from projectq.backends import ParametricGateBackend
from projectq.cengines import DummyEngine
from projectq.ops import Command

from . import _qubit_operator as qo
from ._exceptions import NotInvertible, NotMergeable
from ._gates import Ph, T, X, Y, Z


Command.__repr__ = Command.__str__


def _id(val):
    if isinstance(val, SympyBase):
        if val.is_number:
            return 'symb({})'.format(val)
        return str(val)
    if isinstance(val, Number):
        return str(val)


def _exp(coefficient):
    # Here, we also force conversion of Sympy.Float, Sympy.Integer to float
    if isinstance(coefficient, Number) or coefficient.is_number:
        return cmath.exp(coefficient)
    return sympy.exp(coefficient)


def test_pauli_operator_product_unchanged():
    correct = {
        ('I', 'I'): (1.0, 'I'),
        ('I', 'X'): (1.0, 'X'),
        ('X', 'I'): (1.0, 'X'),
        ('I', 'Y'): (1.0, 'Y'),
        ('Y', 'I'): (1.0, 'Y'),
        ('I', 'Z'): (1.0, 'Z'),
        ('Z', 'I'): (1.0, 'Z'),
        ('X', 'X'): (1.0, 'I'),
        ('Y', 'Y'): (1.0, 'I'),
        ('Z', 'Z'): (1.0, 'I'),
        ('X', 'Y'): (1.0j, 'Z'),
        ('X', 'Z'): (-1.0j, 'Y'),
        ('Y', 'X'): (-1.0j, 'Z'),
        ('Y', 'Z'): (1.0j, 'X'),
        ('Z', 'X'): (1.0j, 'Y'),
        ('Z', 'Y'): (-1.0j, 'X'),
    }
    assert qo._PAULI_OPERATOR_PRODUCTS == correct


def test_unitary_sentinel():
    x, y = sympy.symbols('x y')
    assert qo.IsUnitaryCoeffOpSentinel(x) == x
    assert not qo.IsUnitaryCoeffOpSentinel(x) != x
    assert qo.IsUnitaryCoeffOpSentinel(x) != y
    assert qo.IsUnitaryCoeffOpSentinel((x + y) ** 2) == (x + y) ** 2
    assert not qo.IsUnitaryCoeffOpSentinel((x + y) ** 2) != (x + y) ** 2

    op = qo.IsUnitaryCoeffOpSentinel((x + y) ** 2)
    with pytest.raises(qo.UnitaryIsSymbolicError):
        op.evalf(subs={x: 1})
    with pytest.raises(qo.UnitaryInverseError):
        op.evalf(subs={x: 1, y: 1})


def test_init_defaults():
    loc_op = qo.QubitOperator()
    assert len(loc_op.terms) == 0


@pytest.mark.parametrize("coefficient", [0.5, 0.6j, numpy.float64(2.303), numpy.complex128(-1j)])
def test_init_tuple(coefficient):
    loc_op = ((0, 'X'), (5, 'Y'), (6, 'Z'))
    qubit_op = qo.QubitOperator(loc_op, coefficient)
    assert len(qubit_op.terms) == 1
    assert qubit_op.terms[loc_op] == coefficient


def test_init_str():
    qubit_op = qo.QubitOperator('X0 Y5 Z12', -1.0)
    correct = ((0, 'X'), (5, 'Y'), (12, 'Z'))
    assert correct in qubit_op.terms
    assert qubit_op.terms[correct] == -1.0


def test_init_str_identity():
    qubit_op = qo.QubitOperator('', 2.0)
    assert len(qubit_op.terms) == 1
    assert () in qubit_op.terms
    assert qubit_op.terms[()] == pytest.approx(2.0)


def test_init_bad_term():
    with pytest.raises(ValueError):
        qo.QubitOperator([])


def test_init_bad_coefficient():
    with pytest.raises(ValueError):
        qo.QubitOperator('X0', "0.5")


def test_init_bad_action():
    with pytest.raises(ValueError):
        qo.QubitOperator('Q0')


def test_init_bad_action_in_tuple():
    with pytest.raises(ValueError):
        qo.QubitOperator(((1, 'Q'),))


def test_init_bad_qubit_num_in_tuple():
    with pytest.raises(qo.QubitOperatorError):
        qo.QubitOperator((("1", 'X'),))


def test_init_bad_tuple():
    with pytest.raises(ValueError):
        qo.QubitOperator(((0, 1, 'X'),))


def test_init_bad_str():
    with pytest.raises(ValueError):
        qo.QubitOperator('X')


def test_init_bad_qubit_num():
    with pytest.raises(qo.QubitOperatorError):
        qo.QubitOperator('X-1')


def test_isclose_abs_tol():
    a = qo.QubitOperator('X0', -1.0)
    b = qo.QubitOperator('X0', -1.05)
    c = qo.QubitOperator('X0', -1.11)
    assert a.isclose(b, rel_tol=1e-14, abs_tol=0.1)
    assert not a.isclose(c, rel_tol=1e-14, abs_tol=0.1)
    a = qo.QubitOperator('X0', -1.0j)
    b = qo.QubitOperator('X0', -1.05j)
    c = qo.QubitOperator('X0', -1.11j)
    assert a.isclose(b, rel_tol=1e-14, abs_tol=0.1)
    assert not a.isclose(c, rel_tol=1e-14, abs_tol=0.1)


def test_compress():
    a = qo.QubitOperator('X0', 0.9e-12)
    assert not a.is_parametric()
    assert len(a.terms) == 1
    a.compress()
    assert len(a.terms) == 0
    a = qo.QubitOperator('X0', sympy.Float(0.9e-12))
    assert len(a.terms) == 1
    a.compress()
    assert len(a.terms) == 0
    a = qo.QubitOperator('X0', 1.0 + 1j)
    a.compress(0.5)
    assert len(a.terms) == 1
    for term in a.terms:
        assert a.terms[term] == 1.0 + 1j
    a = qo.QubitOperator('X0', 1.0 + sympy.I)
    assert not a.is_parametric()
    a.compress(0.5)
    assert len(a.terms) == 1
    for term in a.terms:
        assert a.terms[term] == 1.0 + sympy.I
    a = qo.QubitOperator('X0', 1.1 + 1j)
    a.compress(1.0)
    assert len(a.terms) == 1
    for term in a.terms:
        assert a.terms[term] == 1.1
    a = qo.QubitOperator('X0', 1.1 + 1j) + qo.QubitOperator('X1', 1.0e-6j)
    a.compress()
    assert len(a.terms) == 2
    for term in a.terms:
        assert isinstance(a.terms[term], complex)
    a.compress(1.0e-5)
    assert len(a.terms) == 1
    for term in a.terms:
        assert isinstance(a.terms[term], complex)
    a.compress(1.0)
    assert len(a.terms) == 1
    for term in a.terms:
        print(a.terms[term], type(a.terms[term]))
        assert isinstance(a.terms[term], float)

    a = qo.QubitOperator('X0', 1.1 + sympy.I) + qo.QubitOperator('X1', 1.0e-6j)
    assert not a.is_parametric()
    a.compress()
    assert len(a.terms) == 2
    for term in a.terms:
        if isinstance(a.terms[term], SympyBase):
            assert a.terms[term].is_complex
        else:
            assert isinstance(a.terms[term], complex)
    a.compress(1.0e-5)
    assert len(a.terms) == 1
    for term in a.terms:
        if isinstance(a.terms[term], SympyBase):
            assert a.terms[term].is_complex
        else:
            assert isinstance(a.terms[term], complex)
    a.compress(1.0)
    assert len(a.terms) == 1
    for term in a.terms:
        if isinstance(a.terms[term], SympyBase):
            assert a.terms[term].is_real
        else:
            assert isinstance(a.terms[term], float)


def test_is_parametric():
    assert not qo.QubitOperator('X0', 1).is_parametric()
    assert not qo.QubitOperator('X0', 1 + 1j).is_parametric()
    assert not qo.QubitOperator('X0', sympy.sympify(1)).is_parametric()
    assert not qo.QubitOperator('X0', sympy.sympify(1 + 1j)).is_parametric()

    x = sympy.symbols('x')
    op = qo.QubitOperator('X0', x)
    assert op.is_parametric()
    assert not (op - op).is_parametric()
    assert not qo.QubitOperator('X0', x / x).is_parametric()
    assert not qo.QubitOperator('X0', x - x).is_parametric()


def test_parametric_evaluate_partial():
    x, y = sympy.symbols('x y')
    op = qo.QubitOperator('X0', x)
    op += qo.QubitOperator('Y1', y)

    partial = op.evaluate(subs={x: 1.12})
    assert partial.is_parametric()

    numeric = partial.evaluate(subs={y: 1})
    assert not numeric.is_parametric()


def test_isclose_rel_tol():
    a = qo.QubitOperator('X0', 1)
    b = qo.QubitOperator('X0', 2)
    c = qo.QubitOperator('X0', sympy.Float(2))
    assert a.isclose(b, rel_tol=2.5, abs_tol=0.1)
    assert a.isclose(c, rel_tol=2.5, abs_tol=0.1)
    # Test symmetry
    assert a.isclose(b, rel_tol=1, abs_tol=0.1)
    assert b.isclose(a, rel_tol=1, abs_tol=0.1)
    assert a.isclose(c, rel_tol=1, abs_tol=0.1)
    assert c.isclose(a, rel_tol=1, abs_tol=0.1)


@pytest.mark.parametrize('coeff', [-1j, -sympy.I], ids=_id)
@pytest.mark.parametrize('factor', [0, sympy.Integer(0), sympy.Float(0.0)], ids=_id)
def test_isclose_zero_terms(coeff, factor):
    op = qo.QubitOperator(((1, 'Y'), (0, 'X')), coeff) * factor
    assert op.isclose(qo.QubitOperator((), 0.0), rel_tol=1e-12, abs_tol=1e-12)
    assert qo.QubitOperator((), 0.0).isclose(op, rel_tol=1e-12, abs_tol=1e-12)


@pytest.mark.parametrize('coeff1', [-0.1j, -0.1 * sympy.I], ids=_id)
@pytest.mark.parametrize('coeff2', [-0.1j, -0.1 * sympy.I], ids=_id)
def test_isclose_different_terms(coeff1, coeff2):
    a = qo.QubitOperator(((1, 'Y'),), coeff1)
    b = qo.QubitOperator(((1, 'X'),), coeff2)
    assert a.isclose(b, rel_tol=1e-12, abs_tol=0.2)
    assert not a.isclose(b, rel_tol=1e-12, abs_tol=0.05)
    assert b.isclose(a, rel_tol=1e-12, abs_tol=0.2)
    assert not b.isclose(a, rel_tol=1e-12, abs_tol=0.05)


@pytest.mark.parametrize('coeff1', [-0.1j, -0.1 * sympy.I], ids=_id)
@pytest.mark.parametrize('coeff2', [-0.1j, -0.1 * sympy.I], ids=_id)
def test_isclose_different_num_terms(coeff1, coeff2):
    a = qo.QubitOperator(((1, 'Y'),), coeff1)
    a += qo.QubitOperator(((2, 'Y'),), -0.1j)
    b = qo.QubitOperator(((1, 'X'),), coeff2)
    assert not b.isclose(a, rel_tol=1e-12, abs_tol=0.05)
    assert not a.isclose(b, rel_tol=1e-12, abs_tol=0.05)


@pytest.mark.parametrize(
    'coeff1, coeff2, ref',
    [
        (sympy.Symbol('x'), 0.6, False),
        (0.6, sympy.Symbol('x'), False),
        (sympy.Symbol('x'), sympy.Symbol('y'), False),
        (sympy.Symbol('x'), sympy.Symbol('x'), True),
    ],
    ids=_id,
)
def test_isclose_parametric_common_terms(coeff1, coeff2, ref):
    a = qo.QubitOperator(((1, 'Y'),), coeff1)
    b = qo.QubitOperator(((1, 'Y'),), coeff2)
    assert a.isclose(b) == ref


@pytest.mark.parametrize(
    'coeff1, coeff2, ref',
    [
        (sympy.Symbol('x'), 0.6, False),
        (0.6, sympy.Symbol('x'), False),
        (0, sympy.Float(0.0), True),
        (sympy.Float(0.0), 0.0, True),
        (sympy.Float(0.0), sympy.Float(0.0), True),
        (sympy.Symbol('x'), sympy.Symbol('y'), False),
        (sympy.Symbol('x'), sympy.Symbol('x'), False),
    ],
    ids=_id,
)
def test_isclose_parametric_different_terms(coeff1, coeff2, ref):
    a = qo.QubitOperator(((1, 'X'),), coeff1)
    b = qo.QubitOperator(((1, 'Y'),), coeff2)
    assert a.isclose(b) == ref


@pytest.mark.parametrize(
    'coeff, coeff_inv',
    [
        (cmath.exp(0.6j), cmath.exp(-0.6j)),
        (sympy.exp(0.6j), cmath.exp(-0.6j)),
        (sympy.exp(0.6 * sympy.I), cmath.exp(-0.6 * sympy.I)),
        (sympy.exp(sympy.Symbol('x') * sympy.I), sympy.exp(-sympy.Symbol('x') * sympy.I)),
    ],
    ids=_id,
)
def test_get_inverse(coeff, coeff_inv):
    qo0 = qo.QubitOperator("X1 Z2", coeff)
    qo1 = qo.QubitOperator("", 1j)
    assert qo0.get_inverse().isclose(qo.QubitOperator("X1 Z2", coeff_inv))
    assert qo1.get_inverse().isclose(qo.QubitOperator("", -1j))

    qo0 += qo1
    with pytest.raises(NotInvertible):
        qo0.get_inverse()


def test_get_inverse_parametric():
    x = sympy.symbols('x')
    qo0 = qo.QubitOperator("X1 Z2", sympy.exp(0.6j * x))

    qo0_inv = qo0.get_inverse()
    assert qo0_inv == qo.QubitOperator("X1 Z2", sympy.exp(-0.6j * x))

    with pytest.raises(qo.UnitaryIsSymbolicError):
        qo0_inv.evaluate()

    assert qo0_inv.evaluate(subs={x: 1}).isclose(qo.QubitOperator("X1 Z2", cmath.exp(-0.6j)))


def test_get_merged():
    qo0 = qo.QubitOperator("X1 Z2", 1j)
    qo1 = qo.QubitOperator("Y3", 1j)
    assert qo0.isclose(qo.QubitOperator("X1 Z2", 1j))
    assert qo1.isclose(qo.QubitOperator("Y3", 1j))
    assert qo0.get_merged(qo1).isclose(qo.QubitOperator("X1 Z2 Y3", -1))
    with pytest.raises(NotMergeable):
        qo1.get_merged(T)
    qo2 = qo0 + qo1
    with pytest.raises(NotMergeable):
        qo2.get_merged(qo0)
    with pytest.raises(NotMergeable):
        qo0.get_merged(qo2)


def test_get_merged_parametric():
    x = sympy.symbols('x')
    qo0 = qo.QubitOperator("X1 Z2", 1j)
    qo1 = qo.QubitOperator("Y3", x)

    merged = qo0.get_merged(qo1)
    assert qo0.isclose(qo.QubitOperator("X1 Z2", 1j))
    assert merged.isclose(qo.QubitOperator("X1 Z2 Y3", 1j * x))
    assert merged.evaluate(subs={x: 1j}).isclose(qo.QubitOperator("X1 Z2 Y3", -1))
    with pytest.raises(NotMergeable):
        qo1.get_merged(T)
    qo2 = qo0 + qo1
    with pytest.raises(NotMergeable):
        qo2.get_merged(qo0)
    with pytest.raises(NotMergeable):
        qo0.get_merged(qo2)


def test_or_one_qubit():
    x, y, z = sympy.symbols('x y z')
    saving_backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=saving_backend, engine_list=[])
    qureg = eng.allocate_qureg(3)
    eng.flush()
    identity = qo.QubitOperator("", 1j)
    x_op = qo.QubitOperator("X1", _exp(0.5j))
    y_op = qo.QubitOperator("Y2", _exp(0.6j))
    z_op = qo.QubitOperator("Z0", _exp(4.5j))
    identity | qureg
    eng.flush()
    x_op | qureg
    eng.flush()
    y_op | qureg
    eng.flush()
    z_op | qureg
    eng.flush()
    assert saving_backend.received_commands[4].gate == Ph(math.pi / 2.0)

    assert saving_backend.received_commands[6].gate == X
    assert saving_backend.received_commands[6].qubits == ([qureg[1]],)
    assert saving_backend.received_commands[7].gate == Ph(0.5)
    assert saving_backend.received_commands[7].qubits == ([qureg[1]],)

    assert saving_backend.received_commands[9].gate == Y
    assert saving_backend.received_commands[9].qubits == ([qureg[2]],)
    assert saving_backend.received_commands[10].gate == Ph(0.6)
    assert saving_backend.received_commands[10].qubits == ([qureg[2]],)

    assert saving_backend.received_commands[12].gate == Z
    assert saving_backend.received_commands[12].qubits == ([qureg[0]],)
    assert saving_backend.received_commands[13].gate == Ph(4.5)
    assert saving_backend.received_commands[13].qubits == ([qureg[0]],)

    backend = ParametricGateBackend()
    eng = MainEngine(backend=backend, engine_list=[])
    qureg = eng.allocate_qureg(3)
    eng.flush()

    x_op = qo.QubitOperator("X1", _exp(0.5 * x))
    y_op = qo.QubitOperator("Y2", _exp(0.6 * y))
    z_op = qo.QubitOperator("Z0", _exp(4.5 * z))

    x_op | qureg
    y_op | qureg
    z_op | qureg
    eng.flush()

    _arg = sympy.arg

    assert backend._received_commands[4].gate == X
    assert backend._received_commands[4].qubits == ([qureg[1]],)
    assert backend._received_commands[5].gate == Ph(_arg(_exp(0.5 * x)))
    assert backend._received_commands[5].qubits == ([qureg[1]],)

    assert backend._received_commands[6].gate == Y
    assert backend._received_commands[6].qubits == ([qureg[2]],)
    assert backend._received_commands[7].gate == Ph(_arg(_exp(0.6 * y)))
    assert backend._received_commands[7].qubits == ([qureg[2]],)

    assert backend._received_commands[8].gate == Z
    assert backend._received_commands[8].qubits == ([qureg[0]],)
    assert backend._received_commands[9].gate == Ph(_arg(_exp(4.5 * z)))
    assert backend._received_commands[9].qubits == ([qureg[0]],)

    other = DummyEngine(save_commands=True)
    other.is_last_engine = True
    backend.send_to(other, subs={x: 1j, y: 1j, z: 1j})

    assert other.received_commands[4].gate == X
    assert other.received_commands[4].qubits[0][0].id == qureg[1].id
    assert other.received_commands[5].gate == Ph(0.5)
    assert other.received_commands[5].qubits[0][0].id == qureg[1].id

    assert other.received_commands[6].gate == Y
    assert other.received_commands[6].qubits[0][0].id == qureg[2].id
    assert other.received_commands[7].gate == Ph(0.6)
    assert other.received_commands[7].qubits[0][0].id == qureg[2].id

    assert other.received_commands[8].gate == Z
    assert other.received_commands[8].qubits[0][0].id == qureg[0].id
    assert other.received_commands[9].gate == Ph(4.5)
    assert other.received_commands[9].qubits[0][0].id == qureg[0].id


def test_wrong_input():
    eng = MainEngine()
    qureg = eng.allocate_qureg(3)
    op0 = qo.QubitOperator("X1", 0.99)
    with pytest.raises(TypeError):
        op0 | qureg
    op1 = qo.QubitOperator("X2", 1)
    with pytest.raises(ValueError):
        op1 | qureg[1]
    with pytest.raises(TypeError):
        op0 | (qureg[1], qureg[2])
    op2 = op0 + op1
    with pytest.raises(TypeError):
        op2 | qureg


def test_rescaling_of_indices():
    saving_backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=saving_backend, engine_list=[])
    qureg = eng.allocate_qureg(4)
    eng.flush()
    op = qo.QubitOperator("X0 Y1 Z3", 1j)
    op | qureg
    eng.flush()
    assert saving_backend.received_commands[5].gate.isclose(qo.QubitOperator("X0 Y1 Z2", 1j))
    # test that gate creates a new QubitOperator
    assert op.isclose(qo.QubitOperator("X0 Y1 Z3", 1j))


@pytest.mark.parametrize('multiplier', [3, 3.0, sympy.Float(3), 1 + sympy.I, sympy.Symbol('x')])
def test_imul_inplace(multiplier):
    qubit_op = qo.QubitOperator("X1")
    prev_id = id(qubit_op)
    qubit_op *= multiplier
    assert id(qubit_op) == prev_id
    if isinstance(multiplier, Number) or multiplier.is_number:
        assert not qubit_op.is_parametric()
    else:
        assert qubit_op.is_parametric()


@pytest.mark.parametrize(
    "multiplier",
    [0.5, 0.6j, numpy.float64(2.303), numpy.complex128(-1j), sympy.Float(3), 1 + sympy.I, sympy.Symbol('x')],
    ids=_id,
)
def test_imul_scalar(multiplier):
    loc_op = ((1, 'X'), (2, 'Y'))
    qubit_op = qo.QubitOperator(loc_op)
    qubit_op *= multiplier
    if isinstance(multiplier, Number) or multiplier.is_number:
        assert complex(qubit_op.terms[loc_op]) == pytest.approx(complex(multiplier))
    else:
        assert qubit_op.terms[loc_op] - multiplier == 0


@pytest.mark.parametrize(
    'coeff, coeff_ref',
    [
        (0.5, 1.0j * 3.0j * 0.5),
        (sympy.Symbol('x'), 1.0j * 3.0j * sympy.Symbol('x')),
    ],
    ids=_id,
)
def test_imul_qubit_op(coeff, coeff_ref):
    op1 = qo.QubitOperator(((0, 'Y'), (3, 'X'), (8, 'Z'), (11, 'X')), 3.0j)
    op2 = qo.QubitOperator(((1, 'X'), (3, 'Y'), (8, 'Z')), coeff)
    op1 *= op2
    correct_term = ((0, 'Y'), (1, 'X'), (3, 'Z'), (11, 'X'))
    assert len(op1.terms) == 1
    assert correct_term in op1.terms
    assert op1.terms == {correct_term: coeff_ref}


@pytest.mark.parametrize(
    'coeff, coeff_ref',
    [
        (-1.5, 1.5j),
        (sympy.Symbol('x'), -sympy.Symbol('x') * 1.0j),
    ],
    ids=_id,
)
def test_imul_qubit_op_2(coeff, coeff_ref):
    op3 = qo.QubitOperator(((1, 'Y'), (0, 'X')), -1j)
    op4 = qo.QubitOperator(((1, 'Y'), (0, 'X'), (2, 'Z')), coeff)
    op3 *= op4
    op4 *= op3
    assert ((2, 'Z'),) in op3.terms
    assert op3.terms[((2, 'Z'),)] == coeff_ref


@pytest.mark.parametrize(
    'coeff, coeff_ref',
    [
        (-1.5, (1.5j, -2.25j)),
        (sympy.Symbol('x'), (-sympy.Symbol('x') * 1.0j, -sympy.Symbol('x') ** 2 * 1.0j)),
    ],
    ids=_id,
)
def test_imul_bidir(coeff, coeff_ref):
    op_a = qo.QubitOperator(((1, 'Y'), (0, 'X')), -1j)
    op_b = qo.QubitOperator(((1, 'Y'), (0, 'X'), (2, 'Z')), coeff)
    op_a *= op_b
    op_b *= op_a
    assert ((2, 'Z'),) in op_a.terms
    assert op_a.terms[((2, 'Z'),)] == coeff_ref[0]
    assert ((0, 'X'), (1, 'Y')) in op_b.terms
    assert op_b.terms[((0, 'X'), (1, 'Y'))] == coeff_ref[1]


def test_imul_bad_multiplier():
    op = qo.QubitOperator(((1, 'Y'), (0, 'X')), -1j)
    with pytest.raises(TypeError):
        op *= "1"


@pytest.mark.parametrize('zero', [0, 0.0, sympy.Integer(0), sympy.Float(0)], ids=['0', '0.0', 'sym(0)', 'sym(0.0)'])
def test_mul_by_scalarzero(zero):
    op = qo.QubitOperator(((1, 'Y'), (0, 'X')), -1j) * zero
    assert ((0, 'X'), (1, 'Y')) in op.terms
    assert op.terms[((0, 'X'), (1, 'Y'))] == pytest.approx(0.0)


def test_mul_bad_multiplier():
    op = qo.QubitOperator(((1, 'Y'), (0, 'X')), -1j)
    with pytest.raises(TypeError):
        op = op * "0.5"


@pytest.mark.parametrize(
    'coeff, coeff_ref',
    [
        (0.5, 1.0j * 3.0j * 0.5),
        (sympy.Symbol('x'), 1.0j * 3.0j * sympy.Symbol('x')),
    ],
    ids=_id,
)
def test_mul_out_of_place(coeff, coeff_ref):
    op1 = qo.QubitOperator(((0, 'Y'), (3, 'X'), (8, 'Z'), (11, 'X')), 3.0j)
    op2 = qo.QubitOperator(((1, 'X'), (3, 'Y'), (8, 'Z')), coeff)
    op3 = op1 * op2
    correct_term = ((0, 'Y'), (1, 'X'), (3, 'Z'), (11, 'X'))
    assert op1.isclose(qo.QubitOperator(((0, 'Y'), (3, 'X'), (8, 'Z'), (11, 'X')), 3.0j))
    assert op2.isclose(qo.QubitOperator(((1, 'X'), (3, 'Y'), (8, 'Z')), coeff))
    assert op3.isclose(qo.QubitOperator(correct_term, coeff_ref))


def test_mul_npfloat64():
    op = qo.QubitOperator(((1, 'X'), (3, 'Y')), 0.5)
    res = op * numpy.float64(0.5)
    assert res.isclose(qo.QubitOperator(((1, 'X'), (3, 'Y')), 0.5 * 0.5))


def test_mul_multiple_terms():
    op = qo.QubitOperator(((1, 'X'), (3, 'Y'), (8, 'Z')), 0.5)
    op += qo.QubitOperator(((1, 'Z'), (3, 'X'), (8, 'Z')), 1.2)
    op += qo.QubitOperator(((1, 'Z'), (3, 'Y'), (9, 'Z')), 1.4j)
    res = op * op
    correct = qo.QubitOperator((), 0.5 ** 2 + 1.2 ** 2 + 1.4j ** 2)
    correct += qo.QubitOperator(((1, 'Y'), (3, 'Z')), 2j * 1j * 0.5 * 1.2)
    assert res.isclose(correct)


def test_mul_multiple_terms_parametric():
    x, y = sympy.symbols('x y')
    op = qo.QubitOperator(((1, 'X'), (3, 'Y'), (8, 'Z')), x)
    op += qo.QubitOperator(((1, 'Z'), (3, 'X'), (8, 'Z')), y)
    op += qo.QubitOperator(((1, 'Z'), (3, 'Y'), (9, 'Z')), 1.4j)
    res = op * op
    correct = qo.QubitOperator((), x ** 2 + y ** 2 + 1.4j ** 2)
    correct += qo.QubitOperator(((1, 'Y'), (3, 'Z')), 2j * 1j * x * y)
    assert res.isclose(correct)


@pytest.mark.parametrize("multiplier", [0.5, 0.6j, numpy.float64(2.303), numpy.complex128(-1j), sympy.Symbol('x')])
def test_rmul_scalar(multiplier):
    op = qo.QubitOperator(((1, 'X'), (3, 'Y'), (8, 'Z')), 0.5)
    res1 = op * multiplier
    res2 = multiplier * op
    assert res1.isclose(res2)


def test_rmul_bad_multiplier():
    op = qo.QubitOperator(((1, 'X'), (3, 'Y'), (8, 'Z')), 0.5)
    with pytest.raises(TypeError):
        op = "0.5" * op


@pytest.mark.parametrize("divisor", [0.5, 0.6j, numpy.float64(2.303), numpy.complex128(-1j), 2, sympy.Symbol('x')])
def test_truediv_and_div(divisor):
    op = qo.QubitOperator(((1, 'X'), (3, 'Y'), (8, 'Z')), 0.5)
    original = copy.deepcopy(op)
    res = op / divisor
    correct = op * (1.0 / divisor)
    assert res.isclose(correct)
    # Test if done out of place
    assert op.isclose(original)


def test_truediv_bad_divisor():
    op = qo.QubitOperator(((1, 'X'), (3, 'Y'), (8, 'Z')), 0.5)
    with pytest.raises(TypeError):
        op = op / "0.5"


@pytest.mark.parametrize("divisor", [0.5, 0.6j, numpy.float64(2.303), numpy.complex128(-1j), 2, sympy.Symbol('x')])
def test_itruediv_and_idiv(divisor):
    op = qo.QubitOperator(((1, 'X'), (3, 'Y'), (8, 'Z')), 0.5)
    original = copy.deepcopy(op)
    correct = op * (1.0 / divisor)
    op /= divisor
    assert op.isclose(correct)
    # Test if done in-place
    assert not op.isclose(original)


def test_itruediv_bad_divisor():
    op = qo.QubitOperator(((1, 'X'), (3, 'Y'), (8, 'Z')), 0.5)
    with pytest.raises(TypeError):
        op /= "0.5"


@pytest.mark.parametrize('coeff', [1, sympy.Symbol('x')])
def test_iadd_cancellation(coeff):
    term_a = ((1, 'X'), (3, 'Y'), (8, 'Z'))
    term_b = ((1, 'X'), (3, 'Y'), (8, 'Z'))
    a = qo.QubitOperator(term_a, coeff)
    a += qo.QubitOperator(term_b, -coeff)
    print(a.terms)
    assert len(a.terms) == 0


def test_iadd_same_term_mixed():
    x = sympy.Symbol('x')
    term = ((1, 'X'), (3, 'Y'), (8, 'Z'))
    a = qo.QubitOperator(term, 1.0)
    a += qo.QubitOperator(term, 0.5 * x)
    assert len(a.terms) == 1
    assert a.terms[term] - (1 + 0.5 * x) == 0
    a += qo.QubitOperator(term, 0.5 * x)
    assert len(a.terms) == 1
    assert a.terms[term] - (1 + x) == 0


def test_iadd_different_term():
    term_a = ((1, 'X'), (3, 'Y'), (8, 'Z'))
    term_b = ((1, 'Z'), (3, 'Y'), (8, 'Z'))
    a = qo.QubitOperator(term_a, 1.0)
    a += qo.QubitOperator(term_b, 0.5)
    assert len(a.terms) == 2
    assert a.terms[term_a] == pytest.approx(1.0)
    assert a.terms[term_b] == pytest.approx(0.5)
    a += qo.QubitOperator(term_b, 0.5)
    assert len(a.terms) == 2
    assert a.terms[term_a] == pytest.approx(1.0)
    assert a.terms[term_b] == pytest.approx(1.0)


def test_iadd_different_term_mixed():
    x = sympy.Symbol('x')
    term_a = ((1, 'X'), (3, 'Y'), (8, 'Z'))
    term_b = ((1, 'Z'), (3, 'Y'), (8, 'Z'))
    a = qo.QubitOperator(term_a, x)
    a += qo.QubitOperator(term_b, 0.5)
    assert a.is_parametric()
    assert len(a.terms) == 2
    assert a.terms[term_a] == x
    assert a.terms[term_b] == pytest.approx(0.5)
    a += qo.QubitOperator(term_b, 0.5)
    assert a.is_parametric()
    assert len(a.terms) == 2
    assert a.terms[term_a] == x
    assert a.terms[term_b] == pytest.approx(1.0)


def test_iadd_bad_addend():
    op = qo.QubitOperator((), 1.0)
    with pytest.raises(TypeError):
        op += "0.5"


def test_add():
    term_a = ((1, 'X'), (3, 'Y'), (8, 'Z'))
    term_b = ((1, 'Z'), (3, 'Y'), (8, 'Z'))
    a = qo.QubitOperator(term_a, 1.0)
    b = qo.QubitOperator(term_b, 0.5)
    res = a + b + b
    assert len(res.terms) == 2
    assert res.terms[term_a] == pytest.approx(1.0)
    assert res.terms[term_b] == pytest.approx(1.0)
    # Test out of place
    assert a.isclose(qo.QubitOperator(term_a, 1.0))
    assert b.isclose(qo.QubitOperator(term_b, 0.5))


def test_add_bad_addend():
    op = qo.QubitOperator((), 1.0)
    with pytest.raises(TypeError):
        op = op + "0.5"


def test_sub():
    term_a = ((1, 'X'), (3, 'Y'), (8, 'Z'))
    term_b = ((1, 'Z'), (3, 'Y'), (8, 'Z'))
    a = qo.QubitOperator(term_a, 1.0)
    b = qo.QubitOperator(term_b, 0.5)
    res = a - b
    assert len(res.terms) == 2
    assert res.terms[term_a] == pytest.approx(1.0)
    assert res.terms[term_b] == pytest.approx(-0.5)
    res2 = b - a
    assert len(res2.terms) == 2
    assert res2.terms[term_a] == pytest.approx(-1.0)
    assert res2.terms[term_b] == pytest.approx(0.5)


def test_sub_bad_subtrahend():
    op = qo.QubitOperator((), 1.0)
    with pytest.raises(TypeError):
        op = op - "0.5"


def test_isub_different_term():
    term_a = ((1, 'X'), (3, 'Y'), (8, 'Z'))
    term_b = ((1, 'Z'), (3, 'Y'), (8, 'Z'))
    a = qo.QubitOperator(term_a, 1.0)
    a -= qo.QubitOperator(term_b, 0.5)
    assert len(a.terms) == 2
    assert a.terms[term_a] == pytest.approx(1.0)
    assert a.terms[term_b] == pytest.approx(-0.5)
    a -= qo.QubitOperator(term_b, 0.5)
    assert len(a.terms) == 2
    assert a.terms[term_a] == pytest.approx(1.0)
    assert a.terms[term_b] == pytest.approx(-1.0)
    b = qo.QubitOperator(term_a, 1.0)
    b -= qo.QubitOperator(term_a, 1.0)
    assert b.terms == {}


def test_isub_bad_addend():
    op = qo.QubitOperator((), 1.0)
    with pytest.raises(TypeError):
        op -= "0.5"


@pytest.mark.parametrize('coeff', [0.5, sympy.Symbol('x')])
def test_neg(coeff):
    op = qo.QubitOperator(((1, 'X'), (3, 'Y'), (8, 'Z')), coeff)
    -op
    # out of place
    assert op.isclose(qo.QubitOperator(((1, 'X'), (3, 'Y'), (8, 'Z')), coeff))
    correct = -1.0 * op
    assert correct.isclose(-op)


def test_str():
    op = qo.QubitOperator(((1, 'X'), (3, 'Y'), (8, 'Z')), 0.5)
    assert str(op) == "0.5 X1 Y3 Z8"
    op2 = qo.QubitOperator((), 2)
    assert str(op2) == "2 I"


def test_hash():
    op = qo.QubitOperator(((1, 'X'), (3, 'Y'), (8, 'Z')), 0.5)
    assert hash(op) == hash("0.5 X1 Y3 Z8")


def test_str_empty():
    op = qo.QubitOperator()
    assert str(op) == '0'


def test_str_multiple_terms():
    op = qo.QubitOperator(((1, 'X'), (3, 'Y'), (8, 'Z')), 0.5)
    op += qo.QubitOperator(((1, 'Y'), (3, 'Y'), (8, 'Z')), 0.6)
    op += qo.QubitOperator(((1, 'Y'), (3, 'Y'), (8, 'Z')), sympy.Symbol('x'))
    assert str(op) == "0.5 X1 Y3 Z8 +\n(x + 0.6) Y1 Y3 Z8" or str(op) == "(x + 0.6) Y1 Y3 Z8 +\n0.5 X1 Y3 Z8"
    op2 = qo.QubitOperator((), 2)
    assert str(op2) == "2 I"


def test_rep():
    op = qo.QubitOperator(((1, 'X'), (3, 'Y'), (8, 'Z')), 0.5)
    # Not necessary, repr could do something in addition
    assert repr(op) == str(op)
