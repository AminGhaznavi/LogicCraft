"""
LogicCraft - Main CLI Runner & Demonstration
Demonstrates basic gate evaluation, XOR circuits, Half-Adder serialization,
1-bit Full-Adder sub-circuit composition, and Pygame visual GUI launcher.
"""

import argparse
import sys
from typing import List, Tuple
from src.gates import ANDGate, ORGate, NOTGate, XORGate, InputPin, OutputPin, SubCircuitGate
from src.circuit import Circuit
from src.gui import CircuitGUI


def build_half_adder() -> Circuit:
    """Constructs a standard Half-Adder circuit."""
    circuit = Circuit(name="Half Adder")

    in_a = circuit.add_gate(InputPin(name="A"), "in_a")
    in_b = circuit.add_gate(InputPin(name="B"), "in_b")

    xor_gate = circuit.add_gate(XORGate(name="XOR_Sum"), "xor_sum")
    and_carry = circuit.add_gate(ANDGate(name="AND_Carry"), "and_carry")

    out_sum = circuit.add_gate(OutputPin(name="Sum"), "out_sum")
    out_carry = circuit.add_gate(OutputPin(name="Carry"), "out_carry")

    circuit.connect(in_a, xor_gate, 0)
    circuit.connect(in_b, xor_gate, 1)

    circuit.connect(in_a, and_carry, 0)
    circuit.connect(in_b, and_carry, 1)

    circuit.connect(xor_gate, out_sum, 0)
    circuit.connect(and_carry, out_carry, 0)

    return circuit


def build_full_adder_from_half_adders(json_path: str = "half_adder.json") -> Tuple[Circuit, str, str, str]:
    """
    Constructs a 1-bit Full-Adder by loading the Half-Adder JSON file twice
    and wiring them with an OR gate for carry out.
    """
    fa_circuit = Circuit(name="1-Bit Full Adder")

    in_a = fa_circuit.add_gate(InputPin(name="A"), "in_a")
    in_b = fa_circuit.add_gate(InputPin(name="B"), "in_b")
    in_cin = fa_circuit.add_gate(InputPin(name="Cin"), "in_cin")

    ha1_circuit = Circuit.load_from_file(json_path)
    ha2_circuit = Circuit.load_from_file(json_path)

    ha1 = fa_circuit.add_gate(
        SubCircuitGate(
            circuit=ha1_circuit,
            name="HA1",
            input_pin_ids=["in_a", "in_b"],
            output_pin_ids=["out_sum", "out_carry"],
        ),
        "ha1",
    )

    ha2 = fa_circuit.add_gate(
        SubCircuitGate(
            circuit=ha2_circuit,
            name="HA2",
            input_pin_ids=["in_a", "in_b"],
            output_pin_ids=["out_sum", "out_carry"],
        ),
        "ha2",
    )

    or_cout = fa_circuit.add_gate(ORGate(name="OR_Cout"), "or_cout")
    out_sum = fa_circuit.add_gate(OutputPin(name="Sum"), "out_sum")
    out_cout = fa_circuit.add_gate(OutputPin(name="Cout"), "out_cout")

    fa_circuit.connect(in_a, ha1, 0)
    fa_circuit.connect(in_b, ha1, 1)

    fa_circuit.connect(ha1, ha2, 0, from_output_index=0)
    fa_circuit.connect(in_cin, ha2, 1)

    fa_circuit.connect(ha1, or_cout, 0, from_output_index=1)
    fa_circuit.connect(ha2, or_cout, 1, from_output_index=1)

    fa_circuit.connect(ha2, out_sum, 0, from_output_index=0)
    fa_circuit.connect(or_cout, out_cout, 0)

    return fa_circuit, in_a, in_b, in_cin


def run_full_adder_truth_table(circuit: Circuit, in_a_id: str, in_b_id: str, in_cin_id: str) -> None:
    """Evaluates all 8 binary input combinations for a 1-bit Full-Adder."""
    pin_a: InputPin = circuit.get_gate(in_a_id)  # type: ignore
    pin_b: InputPin = circuit.get_gate(in_b_id)  # type: ignore
    pin_cin: InputPin = circuit.get_gate(in_cin_id)  # type: ignore

    test_vectors = [
        (a, b, cin)
        for a in (False, True)
        for b in (False, True)
        for cin in (False, True)
    ]

    print("=" * 55)
    print(f"  {circuit.name.center(51)}")
    print("=" * 55)
    print(f"| {'A':^5} | {'B':^5} | {'Cin':^5} | {'Sum':^7} | {'Cout':^7} | {'State':^9} |")
    print("|" + "-" * 7 + "+" + "-" * 7 + "+" + "-" * 7 + "+" + "-" * 9 + "+" + "-" * 9 + "+" + "-" * 11 + "|")

    for a_val, b_val, cin_val in test_vectors:
        pin_a.set_state(a_val)
        pin_b.set_state(b_val)
        pin_cin.set_state(cin_val)

        results = circuit.evaluate()
        s_val = results.get("Sum", False)
        c_val = results.get("Cout", False)

        a_str = "1" if a_val else "0"
        b_str = "1" if b_val else "0"
        cin_str = "1" if cin_val else "0"
        s_str = "1" if s_val else "0"
        c_str = "1" if c_val else "0"
        state_str = f"S={s_str}, C={c_str}"

        print(f"| {a_str:^5} | {b_str:^5} | {cin_str:^5} | {s_str:^7} | {c_str:^7} | {state_str:^9} |")

    print("=" * 55)
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="LogicCraft Digital Logic Circuit Simulator")
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the interactive Pygame graphical interface.",
    )
    args = parser.parse_args()

    print("\n" + "#" * 55)
    print("#  LogicCraft - Digital Logic Circuit Simulator       #")
    print("#  Modular Graph Simulator & Interactive Canvas        #")
    print("#" * 55 + "\n")

    json_path = "half_adder.json"
    ha_circuit = build_half_adder()
    ha_circuit.save_to_file(json_path)
    print(f"[+] HalfAdder circuit constructed and serialized to '{json_path}'")

    fa_circuit, in_a, in_b, in_cin = build_full_adder_from_half_adders(json_path)
    print(f"[+] FullAdder circuit constructed from 2 chained HalfAdder SubCircuitGates\n")

    if args.gui:
        print("[*] Launching interactive Pygame GUI window...")
        gui = CircuitGUI(fa_circuit)
        gui.run()
    else:
        run_full_adder_truth_table(fa_circuit, in_a, in_b, in_cin)
        print("[i] To launch the interactive Pygame GUI canvas, run:")
        print("    python main.py --gui\n")


if __name__ == "__main__":
    main()


