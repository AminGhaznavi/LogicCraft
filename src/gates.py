"""
LogicCraft - Digital Logic Gates
Defines the base LogicGate class and standard logic gate implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.circuit import Circuit


class LogicGate(ABC):
    """
    Abstract Base Class for digital logic gates.
    """

    def __init__(self, name: str, num_inputs: int) -> None:
        self.name: str = name
        self.inputs: List[Optional[bool]] = [None] * num_inputs
        self.output: Optional[bool] = None
        self.outputs: List[Optional[bool]] = [None]

    @property
    def num_inputs(self) -> int:
        return len(self.inputs)

    def set_input(self, index: int, value: bool) -> None:
        """Sets the value of a specific input pin."""
        if index < 0 or index >= len(self.inputs):
            raise IndexError(
                f"Gate '{self.name}' has {len(self.inputs)} inputs. Index {index} is out of bounds."
            )
        self.inputs[index] = value

    def clear_inputs(self) -> None:
        """Resets all input pins and outputs to None."""
        self.inputs = [None] * len(self.inputs)
        self.output = None
        self.outputs = [None] * len(self.outputs)

    def get_output(self, index: int = 0) -> bool:
        """Gets output signal at a given output pin index."""
        if index == 0 and (not self.outputs or self.outputs[0] is None) and self.output is not None:
            return self.output
        if index < 0 or index >= len(self.outputs):
            raise IndexError(f"Gate '{self.name}' has no output pin at index {index}.")
        val = self.outputs[index]
        if val is None:
            if index == 0 and self.output is not None:
                return self.output
            raise ValueError(f"Gate '{self.name}' output pin {index} is not set.")
        return val

    @abstractmethod
    def evaluate(self) -> bool:
        """Evaluates gate output based on current inputs."""
        raise NotImplementedError("Subclasses must implement evaluate()")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', inputs={self.inputs}, output={self.output})"


class InputPin(LogicGate):
    """InputPin acts as a circuit toggle switch or signal source (0 inputs)."""

    def __init__(self, name: str = "InputPin", state: bool = False) -> None:
        super().__init__(name=name, num_inputs=0)
        self.state: bool = state
        self.output: bool = state

    def set_state(self, state: bool) -> None:
        self.state = state
        self.output = state

    def evaluate(self) -> bool:
        self.output = self.state
        return self.output


class OutputPin(LogicGate):
    """OutputPin represents a probe or LED terminal in the circuit (1 input)."""

    def __init__(self, name: str = "OutputPin") -> None:
        super().__init__(name=name, num_inputs=1)

    def evaluate(self) -> bool:
        if self.inputs[0] is None:
            raise ValueError(f"OutputPin '{self.name}' input 0 is not connected or not set.")
        self.output = bool(self.inputs[0])
        return self.output


class ANDGate(LogicGate):
    """2-input AND gate."""

    def __init__(self, name: str = "AND") -> None:
        super().__init__(name=name, num_inputs=2)

    def evaluate(self) -> bool:
        for idx, val in enumerate(self.inputs):
            if val is None:
                raise ValueError(f"ANDGate '{self.name}' input {idx} is not set.")
        self.output = bool(self.inputs[0] and self.inputs[1])
        return self.output


class ORGate(LogicGate):
    """2-input OR gate."""

    def __init__(self, name: str = "OR") -> None:
        super().__init__(name=name, num_inputs=2)

    def evaluate(self) -> bool:
        for idx, val in enumerate(self.inputs):
            if val is None:
                raise ValueError(f"ORGate '{self.name}' input {idx} is not set.")
        self.output = bool(self.inputs[0] or self.inputs[1])
        return self.output


class NOTGate(LogicGate):
    """1-input NOT gate (Inverter)."""

    def __init__(self, name: str = "NOT") -> None:
        super().__init__(name=name, num_inputs=1)

    def evaluate(self) -> bool:
        if self.inputs[0] is None:
            raise ValueError(f"NOTGate '{self.name}' input 0 is not set.")
        self.output = not bool(self.inputs[0])
        return self.output


class XORGate(LogicGate):
    """2-input XOR gate."""

    def __init__(self, name: str = "XOR") -> None:
        super().__init__(name=name, num_inputs=2)

    def evaluate(self) -> bool:
        for idx, val in enumerate(self.inputs):
            if val is None:
                raise ValueError(f"XORGate '{self.name}' input {idx} is not set.")
        self.output = bool(self.inputs[0] ^ self.inputs[1])
        return self.output


class NANDGate(LogicGate):
    """2-input NAND gate."""

    def __init__(self, name: str = "NAND") -> None:
        super().__init__(name=name, num_inputs=2)

    def evaluate(self) -> bool:
        for idx, val in enumerate(self.inputs):
            if val is None:
                raise ValueError(f"NANDGate '{self.name}' input {idx} is not set.")
        self.output = not (self.inputs[0] and self.inputs[1])
        return self.output


class NORGate(LogicGate):
    """2-input NOR gate."""

    def __init__(self, name: str = "NOR") -> None:
        super().__init__(name=name, num_inputs=2)

    def evaluate(self) -> bool:
        for idx, val in enumerate(self.inputs):
            if val is None:
                raise ValueError(f"NORGate '{self.name}' input {idx} is not set.")
        self.output = not (self.inputs[0] or self.inputs[1])
        return self.output


class SubCircuitGate(LogicGate):
    """
    Encapsulates a Circuit object as a modular logic gate.
    Maps SubCircuitGate inputs to inner circuit InputPins, evaluates the circuit,
    and maps inner circuit OutputPins to SubCircuitGate outputs.
    """

    def __init__(
        self,
        circuit: "Circuit",
        name: str = "SubCircuit",
        input_pin_ids: Optional[List[str]] = None,
        output_pin_ids: Optional[List[str]] = None,
    ) -> None:
        self.circuit: "Circuit" = circuit

        if input_pin_ids is not None:
            self.input_pin_ids: List[str] = list(input_pin_ids)
        else:
            self.input_pin_ids = [
                gid for gid, g in circuit.gates.items() if isinstance(g, InputPin)
            ]

        if output_pin_ids is not None:
            self.output_pin_ids: List[str] = list(output_pin_ids)
        else:
            self.output_pin_ids = [
                gid for gid, g in circuit.gates.items() if isinstance(g, OutputPin)
            ]

        super().__init__(name=name, num_inputs=len(self.input_pin_ids))
        self.outputs: List[Optional[bool]] = [None] * len(self.output_pin_ids)

    @property
    def num_outputs(self) -> int:
        return len(self.outputs)

    def evaluate(self) -> bool:
        for idx, val in enumerate(self.inputs):
            if val is None:
                raise ValueError(f"SubCircuitGate '{self.name}' input {idx} is not set.")
            pin_id = self.input_pin_ids[idx]
            pin = self.circuit.get_gate(pin_id)
            if isinstance(pin, InputPin):
                pin.set_state(val)
            else:
                pin.set_input(0, val)

        self.circuit.evaluate()

        for idx, pin_id in enumerate(self.output_pin_ids):
            out_pin = self.circuit.get_gate(pin_id)
            self.outputs[idx] = out_pin.output

        if self.outputs:
            self.output = self.outputs[0]
            return self.output
        self.output = False
        return False

