"""
LogicCraft - Circuit Graph Manager & Evaluation Engine
Handles gate registration, wire routing, dependency resolution, and evaluation.
"""

from collections import deque
import json
from typing import Any, Dict, List, NamedTuple, Optional, Type
from src.gates import LogicGate, InputPin, OutputPin
import src.gates as gates_module


class Connection(NamedTuple):
    from_gate_id: str
    to_gate_id: str
    to_input_index: int
    from_output_index: int = 0


class Circuit:
    """
    Circuit manages a directed acyclic graph (DAG) of logic gates.
    """

    def __init__(self, name: str = "Circuit") -> None:
        self.name: str = name
        self.gates: Dict[str, LogicGate] = {}
        self.connections: List[Connection] = []
        self._id_counter: int = 0

    def add_gate(self, gate: LogicGate, gate_id: Optional[str] = None) -> str:
        """
        Adds a logic gate to the circuit and returns its unique ID.
        """
        if gate_id is None:
            self._id_counter += 1
            gate_id = f"{gate.name.lower()}_{self._id_counter}"

        if gate_id in self.gates:
            raise ValueError(f"Gate with ID '{gate_id}' already exists in circuit.")

        self.gates[gate_id] = gate
        return gate_id

    def connect(
        self,
        from_gate_id: str,
        to_gate_id: str,
        to_input_index: int,
        from_output_index: int = 0,
    ) -> None:
        """
        Connects an output of from_gate to a specific input index of to_gate.
        """
        if from_gate_id not in self.gates:
            raise KeyError(f"Source gate '{from_gate_id}' not found in circuit.")
        if to_gate_id not in self.gates:
            raise KeyError(f"Destination gate '{to_gate_id}' not found in circuit.")

        to_gate = self.gates[to_gate_id]
        if to_input_index < 0 or to_input_index >= to_gate.num_inputs:
            raise IndexError(
                f"Gate '{to_gate_id}' ({to_gate.name}) has {to_gate.num_inputs} inputs. "
                f"Index {to_input_index} is invalid."
            )

        # Ensure no duplicate connection to the same destination pin
        for conn in self.connections:
            if conn.to_gate_id == to_gate_id and conn.to_input_index == to_input_index:
                raise ValueError(
                    f"Pin {to_input_index} on '{to_gate_id}' is already connected to '{conn.from_gate_id}'."
                )

        self.connections.append(
            Connection(from_gate_id, to_gate_id, to_input_index, from_output_index)
        )

    def _topological_sort(self) -> List[str]:
        """
        Returns gate IDs sorted in topological order using Kahn's algorithm.
        Raises ValueError if a cycle is detected.
        """
        # in_degree represents number of incoming connections to a gate
        in_degree: Dict[str, int] = {gid: 0 for gid in self.gates}
        adj: Dict[str, List[str]] = {gid: [] for gid in self.gates}

        for conn in self.connections:
            in_degree[conn.to_gate_id] += 1
            adj[conn.from_gate_id].append(conn.to_gate_id)

        # Start with all nodes that have 0 incoming edges (e.g. InputPins)
        queue = deque([gid for gid, deg in in_degree.items() if deg == 0])
        sorted_order: List[str] = []

        while queue:
            current_id = queue.popleft()
            sorted_order.append(current_id)

            for neighbor_id in adj[current_id]:
                in_degree[neighbor_id] -= 1
                if in_degree[neighbor_id] == 0:
                    queue.append(neighbor_id)

        if len(sorted_order) != len(self.gates):
            raise ValueError("Cycle detected in circuit graph. Cannot evaluate.")

        return sorted_order

    def evaluate(self) -> Dict[str, bool]:
        """
        Evaluates signal propagation in topological order.
        Returns a dictionary mapping OutputPin identifiers/names to their boolean values.
        """
        eval_order = self._topological_sort()

        # Map to quickly find outgoing connections from a gate
        outgoing: Dict[str, List[Connection]] = {gid: [] for gid in self.gates}
        for conn in self.connections:
            outgoing[conn.from_gate_id].append(conn)

        # Clear inputs for non-InputPin gates
        for gid, gate in self.gates.items():
            if not isinstance(gate, InputPin):
                gate.clear_inputs()

        # Evaluate and propagate signals
        for gid in eval_order:
            gate = self.gates[gid]
            gate.evaluate()

            for conn in outgoing[gid]:
                signal = gate.get_output(conn.from_output_index)
                dest_gate = self.gates[conn.to_gate_id]
                dest_gate.set_input(conn.to_input_index, signal)

        # Collect OutputPin results
        results: Dict[str, bool] = {}
        for gid, gate in self.gates.items():
            if isinstance(gate, OutputPin):
                key = gate.name if gate.name != "OutputPin" else gid
                results[key] = gate.output

        return results

    def get_gate(self, gate_id: str) -> LogicGate:
        """Retrieves gate by ID."""
        return self.gates[gate_id]

    def to_dict(self) -> Dict[str, Any]:
        """Serializes circuit structure into a Python dictionary."""
        gates_data = []
        for gid, gate in self.gates.items():
            g_dict: Dict[str, Any] = {
                "id": gid,
                "type": gate.__class__.__name__,
                "name": gate.name,
            }
            if isinstance(gate, gates_module.InputPin):
                g_dict["state"] = gate.state
            elif isinstance(gate, gates_module.SubCircuitGate):
                g_dict["sub_circuit"] = gate.circuit.to_dict()
                g_dict["input_pin_ids"] = gate.input_pin_ids
                g_dict["output_pin_ids"] = gate.output_pin_ids
            gates_data.append(g_dict)

        conns_data = [
            {
                "from_gate_id": conn.from_gate_id,
                "to_gate_id": conn.to_gate_id,
                "to_input_index": conn.to_input_index,
                "from_output_index": conn.from_output_index,
            }
            for conn in self.connections
        ]

        return {
            "name": self.name,
            "gates": gates_data,
            "connections": conns_data,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Circuit":
        """Reconstructs a Circuit instance from a dictionary."""
        circuit = cls(name=data.get("name", "Circuit"))

        gate_classes: Dict[str, Type[gates_module.LogicGate]] = {
            "InputPin": gates_module.InputPin,
            "OutputPin": gates_module.OutputPin,
            "ANDGate": gates_module.ANDGate,
            "ORGate": gates_module.ORGate,
            "NOTGate": gates_module.NOTGate,
            "XORGate": gates_module.XORGate,
            "NANDGate": gates_module.NANDGate,
            "NORGate": gates_module.NORGate,
            "SubCircuitGate": gates_module.SubCircuitGate,
        }

        for g_data in data.get("gates", []):
            gid = g_data["id"]
            g_type = g_data["type"]
            g_name = g_data.get("name", g_type)

            if g_type not in gate_classes:
                raise ValueError(f"Unknown gate type: '{g_type}'")

            gate_cls = gate_classes[g_type]

            if g_type == "InputPin":
                gate = gates_module.InputPin(name=g_name, state=g_data.get("state", False))
            elif g_type == "SubCircuitGate":
                sub_circuit = cls.from_dict(g_data["sub_circuit"])
                gate = gates_module.SubCircuitGate(
                    circuit=sub_circuit,
                    name=g_name,
                    input_pin_ids=g_data.get("input_pin_ids"),
                    output_pin_ids=g_data.get("output_pin_ids"),
                )
            else:
                gate = gate_cls(name=g_name)

            circuit.add_gate(gate, gate_id=gid)

        for conn in data.get("connections", []):
            circuit.connect(
                from_gate_id=conn["from_gate_id"],
                to_gate_id=conn["to_gate_id"],
                to_input_index=conn["to_input_index"],
                from_output_index=conn.get("from_output_index", 0),
            )

        return circuit

    def save_to_file(self, filename: str) -> None:
        """Serializes and saves circuit to a JSON file."""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, filename: str) -> "Circuit":
        """Loads and reconstructs a Circuit from a JSON file."""
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
