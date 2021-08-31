# -*- coding: utf-8 -*-
# pylint: skip-file

"""Showcase most of the quantum gates available in ProjectQ."""

import matplotlib.pyplot as plt

from projectq import MainEngine
from projectq.backends import CircuitDrawer
from projectq.ops import (
    CNOT,
    QFT,
    All,
    Barrier,
    BasicMathGate,
    C,
    Entangle,
    H,
    Measure,
    Ph,
    QubitOperator,
    Rx,
    Ry,
    Rz,
    S,
    SqrtSwap,
    SqrtX,
    Swap,
    T,
    Tensor,
    TimeEvolution,
    Toffoli,
    X,
    Y,
    Z,
    get_inverse,
)


def zoo_profile():
    """Generate and display the zoo of quantum gates."""
    # create a main compiler engine with a drawing backend
    drawing_engine = CircuitDrawer()
    locations = {0: 1, 1: 2, 2: 0, 3: 3}
    drawing_engine.set_qubit_locations(locations)
    main_eng = MainEngine(drawing_engine)
    qureg = main_eng.allocate_qureg(4)

    # define a zoo of gates
    te_gate = TimeEvolution(0.5, 0.1 * QubitOperator('X0 Y2'))

    def add(x, y):
        return x, y + 1

    zoo = [
        (X, 3),
        (Y, 2),
        (Z, 0),
        (Rx(0.5), 2),
        (Ry(0.5), 1),
        (Rz(0.5), 1),
        (Ph(0.5), 0),
        (S, 3),
        (T, 2),
        (H, 1),
        (Toffoli, (0, 1, 2)),
        (Barrier, [2, 0, 1, 3]),
        (Swap, (0, 3)),
        (SqrtSwap, (0, 1)),
        (get_inverse(SqrtSwap), (1, 3)),
        (SqrtX, 2),
        (C(get_inverse(SqrtX)), (0, 2)),
        (C(Ry(0.5)), (2, 3)),
        (CNOT, (2, 1)),
        (Entangle, [2, 0, 1, 3]),
        (te_gate, [2, 1, 0, 3]),
        (QFT, None),
        (Tensor(H), None),
        (BasicMathGate(add), (1, 3)),
        (All(Measure), None),
    ]

    # apply them
    for gate, pos in zoo:
        if pos is None:
            gate | qureg
        elif isinstance(pos, tuple):
            gate | tuple(qureg[i] for i in pos)
        elif isinstance(pos, list):
            gate | [qureg[i] for i in pos]
        else:
            gate | qureg[pos]

    main_eng.flush()

    drawing_engine.draw(figsize=[10, 4.8], drawing_order=locations)
    plt.xlim(0, 1)
    plt.show()


if __name__ == "__main__":
    zoo_profile()
