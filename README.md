# LogicCraft ⚡

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://python.org)
[![Pygame CE](https://img.shields.io/badge/Pygame--CE-2.5%2B-brightgreen.svg?logo=pygame&logoColor=white)](https://pyga.me/)
[![Tests Passing](https://img.shields.io/badge/Tests-17%2F17%20Passed-success.svg?logo=github-actions&logoColor=white)](#running-unit-tests)
[![Architecture](https://img.shields.io/badge/Architecture-DAG%20%7C%20Kahn's%20Topological%20Sort-orange.svg)](#architecture--design)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**LogicCraft** is an object-oriented Digital Logic Circuit Simulator written in Python. It models electronic circuits as **Directed Acyclic Graphs (DAGs)**, computes deterministic signal propagation using **Topological Sorting** (Kahn's Algorithm), and provides an interactive visual canvas built with `pygame-ce` featuring real-time signal flows, interactive switches, and glowing LED outputs.

---

## Key Features

- **Graph-Based Evaluation Engine**:
  - Treats logic gates as graph nodes and electrical connections as directed edges.
  - Resolves signal propagation order deterministically via **Kahn's Algorithm** for topological sorting.
  - Built-in cycle detection preventing illegal circular feedback loops.

- **Hierarchical Modular Sub-Circuits**:
  - Encapsulate any circuit into a `SubCircuitGate` black box.
  - Multi-output pin routing support (e.g. `Sum` and `Carry` indexed outputs).
  - Nest sub-circuits hierarchically (e.g., nesting two Half-Adders to compose a 1-Bit Full-Adder).

- **JSON Serialization & Deserialization**:
  - Save circuit topologies and connections to `.json` files (`Circuit.save_to_file()`).
  - Reload circuits dynamically for modular re-use (`Circuit.load_from_file()`).

- **Interactive Pygame GUI**:
  - **Dynamic Wire Color-Coding**: Live active high-voltage (`#00FFAA` neon green) vs low-voltage (`#585B70` slate gray) Bézier wire rendering.
  - **Clickable Toggle Switches**: Click `InputPin`s to toggle states between 0 and 1 with immediate graph re-evaluation.
  - **Glowing LED Indicators**: Output pins render as illuminated status lamps with dynamic glow auras.
  - **Drag-and-Drop Canvas**: Freely move gate nodes across the screen to customize wiring diagrams.
  - **Auto-Layout Engine**: Automatically organizes gates into layered columns (Inputs $\to$ SubCircuits $\to$ Gates $\to$ Outputs).

---

## Architecture & Design

### Node & Graph Model

```
+-----------------------------------------------------------+
|                          Circuit                          |
|  - gates: Dict[str, LogicGate]                            |
|  - connections: List[Connection]                          |
|  - evaluate() -> Dict[str, bool]                          |
+-----------------------------------------------------------+
          | contains                               | evaluates
          v                                        v
+-----------------------------+           +-----------------+
|          LogicGate          |           |   Topological   |
| - inputs: List[bool | None] |           |   Sort Engine   |
| - outputs: List[bool]       |           | (Kahn's In-Deg) |
| - evaluate() -> bool        |           +-----------------+
+-----------------------------+
```

### 1-Bit Full-Adder Sub-Circuit Composition

LogicCraft demonstrates modularity by chaining two 2-input/2-output Half-Adder sub-circuits (`HA1`, `HA2`) with a carry `OR` gate:

```
    A ───────►[ HA1 ]── Sum1 ────►[ HA2 ]── Sum ───► (Sum LED)
    B ───────►[     ]── Carry1 ┐  [     ]
                               │  [     ]── Carry2 ┐
  Cin ─────────────────────────┼─►[     ]          │
                               │                   ▼
                               └──────────────►[ OR Gate ]── Cout ──► (Cout LED)
```

---


## Project Structure

```
LogicCraft/
├── src/
│   ├── __init__.py          # Package exports (gates, Circuit, CircuitGUI)
│   ├── gates.py             # LogicGate ABC, primitive gates, and SubCircuitGate
│   ├── circuit.py           # DAG manager, Kahn's algorithm, JSON persistence
│   └── gui.py               # Interactive Pygame visual GUI with drag & drop
├── tests/
│   ├── __init__.py
│   └── test_circuit.py      # Comprehensive 17-test test suite
├── main.py                  # CLI runner, Half-Adder builder, and GUI launcher
├── requirements.txt         # Project dependencies (pygame-ce)
├── half_adder.json          # Pre-built serialized Half-Adder circuit definition
└── README.md                # Documentation & showcase
```

---

## Installation

Ensure Python 3.10+ is installed:

```bash
git clone https://github.com/your-username/LogicCraft.git
cd LogicCraft
python -m pip install -r requirements.txt
```

---

## Usage Guide

### Interactive Visual GUI

Launch the 1-bit Full-Adder interactive simulation:

```bash
python main.py --gui
```

- **Left-Click** toggle buttons on `A`, `B`, or `Cin` to switch between `0 (LOW)` and `1 (HIGH)`.
- **Click and Drag** gate cards to reposition nodes on the canvas.
- Watch live signals propagate through wires to the glowing `Sum` and `Cout` LEDs.

### CLI Truth Table Verification

Run the automated simulation and print the complete ASCII truth table:

```bash
python main.py
```

Output:
```
=======================================================
                    1-Bit Full Adder
=======================================================
|   A   |   B   |  Cin  |   Sum   |  Cout   |   State   |
|-------+-------+-------+---------+---------+-----------|
|   0   |   0   |   0   |    0    |    0    | S=0, C=0  |
|   0   |   0   |   1   |    1    |    0    | S=1, C=0  |
|   0   |   1   |   0   |    1    |    0    | S=1, C=0  |
|   0   |   1   |   1   |    0    |    1    | S=0, C=1  |
|   1   |   0   |   0   |    1    |    0    | S=1, C=0  |
|   1   |   0   |   1   |    0    |    1    | S=0, C=1  |
|   1   |   1   |   0   |    0    |    1    | S=0, C=1  |
|   1   |   1   |   1   |    1    |    1    | S=1, C=1  |
=======================================================
```

### Running Unit Tests

Run the full automated test suite (17 tests covering all gates, DAG topological sort, cycle detection, SubCircuitGate nesting, JSON serialization, and GUI geometry):

```bash
python -m unittest discover tests
```

---

## License

This project is licensed under the MIT License.


