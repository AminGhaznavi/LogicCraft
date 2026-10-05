"""
Comprehensive Unit Tests for LogicCraft Digital Logic Simulator.
Covers basic logic gates, DAG topological sort & cycle detection,
circuit serialization & deserialization, SubCircuitGate nesting,
and GUI headless layout geometry.
"""

import os
import tempfile
import unittest
from src.gates import (
    ANDGate,
    ORGate,
    NOTGate,
    XORGate,
    NANDGate,
    NORGate,
    InputPin,
    OutputPin,
    SubCircuitGate,
)
from src.circuit import Circuit


class TestBasicLogicGates(unittest.TestCase):
    """Verifies truth tables and pin bounds for all primitive logic gates."""

    def test_and_gate_truth_table(self):
        gate = ANDGate()
        for a, b, expected in [
            (False, False, False),
            (False, True, False),
            (True, False, False),
            (True, True, True),
        ]:
            gate.set_input(0, a)
            gate.set_input(1, b)
            self.assertEqual(gate.evaluate(), expected, f"AND failed for ({a}, {b})")

    def test_or_gate_truth_table(self):
        gate = ORGate()
        for a, b, expected in [
            (False, False, False),
            (False, True, True),
            (True, False, True),
            (True, True, True),
        ]:
            gate.set_input(0, a)
            gate.set_input(1, b)
            self.assertEqual(gate.evaluate(), expected, f"OR failed for ({a}, {b})")

    def test_not_gate_truth_table(self):
        gate = NOTGate()
        gate.set_input(0, False)
        self.assertTrue(gate.evaluate())
        gate.set_input(0, True)
        self.assertFalse(gate.evaluate())

    def test_xor_gate_truth_table(self):
        gate = XORGate()
        for a, b, expected in [
            (False, False, False),
            (False, True, True),
            (True, False, True),
            (True, True, False),
        ]:
            gate.set_input(0, a)
            gate.set_input(1, b)
            self.assertEqual(gate.evaluate(), expected, f"XOR failed for ({a}, {b})")

    def test_nand_gate_truth_table(self):
        gate = NANDGate()
        for a, b, expected in [
            (False, False, True),
            (False, True, True),
            (True, False, True),
            (True, True, False),
        ]:
            gate.set_input(0, a)
            gate.set_input(1, b)
            self.assertEqual(gate.evaluate(), expected, f"NAND failed for ({a}, {b})")

    def test_nor_gate_truth_table(self):
        gate = NORGate()
        for a, b, expected in [
            (False, False, True),
            (False, True, False),
            (True, False, False),
            (True, True, False),
        ]:
            gate.set_input(0, a)
            gate.set_input(1, b)
            self.assertEqual(gate.evaluate(), expected, f"NOR failed for ({a}, {b})")

    def test_pin_behavior_and_bounds(self):
        pin_in = InputPin("InA", state=False)
        self.assertFalse(pin_in.evaluate())
        pin_in.set_state(True)
        self.assertTrue(pin_in.evaluate())
        self.assertTrue(pin_in.get_output(0))

        pin_out = OutputPin("OutA")
        pin_out.set_input(0, True)
        self.assertTrue(pin_out.evaluate())
        self.assertTrue(pin_out.output)

        gate = ANDGate()
        with self.assertRaises(IndexError):
            gate.set_input(5, True)
        with self.assertRaises(IndexError):
            gate.get_output(2)


class TestCircuitEvaluationAndTopologicalSort(unittest.TestCase):
    """Verifies Kahn's algorithm, signal evaluation, and cycle detection."""

    def test_branched_dag_evaluation(self):
        c = Circuit(name="BranchedDAG")
        in_a = c.add_gate(InputPin("A", True), "a")
        in_b = c.add_gate(InputPin("B", False), "b")
        xor_g = c.add_gate(XORGate("XOR"), "xor")
        and_g = c.add_gate(ANDGate("AND"), "and")
        out_s = c.add_gate(OutputPin("Sum"), "sum")
        out_c = c.add_gate(OutputPin("Carry"), "carry")

        c.connect(in_a, xor_g, 0)
        c.connect(in_b, xor_g, 1)
        c.connect(in_a, and_g, 0)
        c.connect(in_b, and_g, 1)
        c.connect(xor_g, out_s, 0)
        c.connect(and_g, out_c, 0)

        res = c.evaluate()
        self.assertEqual(res, {"Sum": True, "Carry": False})

    def test_direct_cycle_detection(self):
        c = Circuit(name="DirectCycle")
        n1 = c.add_gate(NOTGate("N1"), "n1")
        n2 = c.add_gate(NOTGate("N2"), "n2")
        c.connect(n1, n2, 0)
        c.connect(n2, n1, 0)
        with self.assertRaises(ValueError):
            c.evaluate()

    def test_indirect_cycle_detection(self):
        c = Circuit(name="IndirectCycle")
        n1 = c.add_gate(NOTGate("N1"), "n1")
        n2 = c.add_gate(NOTGate("N2"), "n2")
        n3 = c.add_gate(NOTGate("N3"), "n3")
        c.connect(n1, n2, 0)
        c.connect(n2, n3, 0)
        c.connect(n3, n1, 0)
        with self.assertRaises(ValueError):
            c.evaluate()

    def test_invalid_connections(self):
        c = Circuit(name="InvalidConn")
        g1 = c.add_gate(NOTGate("N1"), "n1")
        with self.assertRaises(KeyError):
            c.connect(g1, "non_existent_gate", 0)
        with self.assertRaises(IndexError):
            c.connect(g1, g1, 99)



class TestSerialization(unittest.TestCase):
    """Verifies JSON file and dictionary serialization and deserialization."""

    def test_serialization_dict_roundtrip(self):
        c = Circuit(name="RoundtripCircuit")
        in_a = c.add_gate(InputPin("A", True), "a")
        in_b = c.add_gate(InputPin("B", True), "b")
        and_g = c.add_gate(ANDGate("AND"), "and")
        out = c.add_gate(OutputPin("Out"), "out")

        c.connect(in_a, and_g, 0)
        c.connect(in_b, and_g, 1)
        c.connect(and_g, out, 0)

        d = c.to_dict()
        reconstructed = Circuit.from_dict(d)
        self.assertEqual(reconstructed.evaluate(), {"Out": True})

    def test_save_and_load_file(self):
        c = Circuit(name="TempFileCircuit")
        in_a = c.add_gate(InputPin("A", False), "a")
        not_g = c.add_gate(NOTGate("NOT"), "not")
        out = c.add_gate(OutputPin("Out"), "out")

        c.connect(in_a, not_g, 0)
        c.connect(not_g, out, 0)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
            temp_path = tf.name

        try:
            c.save_to_file(temp_path)
            loaded = Circuit.load_from_file(temp_path)
            self.assertEqual(loaded.evaluate(), {"Out": True})
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_load_root_half_adder_json(self):
        if os.path.exists("half_adder.json"):
            ha = Circuit.load_from_file("half_adder.json")
            self.assertIn("xor_sum", ha.gates)
            self.assertIn("and_carry", ha.gates)
            res = ha.evaluate()
            self.assertIn("Sum", res)
            self.assertIn("Carry", res)


class TestSubCircuitGateAndAdders(unittest.TestCase):
    """Tests SubCircuitGate modular composition with Half-Adder and Full-Adder."""

    def _build_half_adder_circuit(self) -> Circuit:
        c = Circuit(name="HalfAdder")
        in_a = c.add_gate(InputPin("A"), "in_a")
        in_b = c.add_gate(InputPin("B"), "in_b")
        xor_g = c.add_gate(XORGate("XOR"), "xor_sum")
        and_g = c.add_gate(ANDGate("AND"), "and_carry")
        out_s = c.add_gate(OutputPin("Sum"), "out_sum")
        out_c = c.add_gate(OutputPin("Carry"), "out_carry")

        c.connect(in_a, xor_g, 0)
        c.connect(in_b, xor_g, 1)
        c.connect(in_a, and_g, 0)
        c.connect(in_b, and_g, 1)
        c.connect(xor_g, out_s, 0)
        c.connect(and_g, out_c, 0)
        return c

    def test_half_adder_subcircuit_all_vectors(self):
        ha_circuit = self._build_half_adder_circuit()
        sub_gate = SubCircuitGate(
            circuit=ha_circuit,
            name="HA",
            input_pin_ids=["in_a", "in_b"],
            output_pin_ids=["out_sum", "out_carry"],
        )

        test_table = [
            (False, False, False, False),
            (False, True, True, False),
            (True, False, True, False),
            (True, True, False, True),
        ]

        for a, b, expected_sum, expected_carry in test_table:
            sub_gate.set_input(0, a)
            sub_gate.set_input(1, b)
            sub_gate.evaluate()
            self.assertEqual(sub_gate.get_output(0), expected_sum, f"Sum failed for ({a},{b})")
            self.assertEqual(sub_gate.get_output(1), expected_carry, f"Carry failed for ({a},{b})")

    def test_full_adder_composition_all_vectors(self):
        """Constructs and tests full 8-vector truth table for 1-bit Full-Adder."""
        fa = Circuit(name="1-Bit Full Adder")
        in_a = fa.add_gate(InputPin("A"), "in_a")
        in_b = fa.add_gate(InputPin("B"), "in_b")
        in_cin = fa.add_gate(InputPin("Cin"), "in_cin")

        ha1 = fa.add_gate(
            SubCircuitGate(
                self._build_half_adder_circuit(),
                "HA1",
                ["in_a", "in_b"],
                ["out_sum", "out_carry"],
            ),
            "ha1",
        )
        ha2 = fa.add_gate(
            SubCircuitGate(
                self._build_half_adder_circuit(),
                "HA2",
                ["in_a", "in_b"],
                ["out_sum", "out_carry"],
            ),
            "ha2",
        )

        or_cout = fa.add_gate(ORGate("OR_Cout"), "or_cout")
        out_sum = fa.add_gate(OutputPin("Sum"), "out_sum")
        out_cout = fa.add_gate(OutputPin("Cout"), "out_cout")

        fa.connect(in_a, ha1, 0)
        fa.connect(in_b, ha1, 1)
        fa.connect(ha1, ha2, 0, from_output_index=0)
        fa.connect(in_cin, ha2, 1)
        fa.connect(ha1, or_cout, 0, from_output_index=1)
        fa.connect(ha2, or_cout, 1, from_output_index=1)
        fa.connect(ha2, out_sum, 0, from_output_index=0)
        fa.connect(or_cout, out_cout, 0)

        pin_a: InputPin = fa.get_gate(in_a)  # type: ignore
        pin_b: InputPin = fa.get_gate(in_b)  # type: ignore
        pin_cin: InputPin = fa.get_gate(in_cin)  # type: ignore

        for a in (False, True):
            for b in (False, True):
                for cin in (False, True):
                    pin_a.set_state(a)
                    pin_b.set_state(b)
                    pin_cin.set_state(cin)

                    total = int(a) + int(b) + int(cin)
                    exp_sum = bool(total % 2)
                    exp_cout = bool(total >= 2)

                    res = fa.evaluate()
                    self.assertEqual(res["Sum"], exp_sum, f"FA Sum failed for A={a}, B={b}, Cin={cin}")
                    self.assertEqual(res["Cout"], exp_cout, f"FA Cout failed for A={a}, B={b}, Cin={cin}")





class TestGUIRenderingAndLayout(unittest.TestCase):
    """Verifies GUI node auto-layout and socket geometry in headless mode."""

    def test_gui_layout_and_geometry(self):
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        from src.gui import CircuitGUI

        c = Circuit(name="GUITest")
        in_a = c.add_gate(InputPin("A", True), "a")
        in_b = c.add_gate(InputPin("B", False), "b")
        xor_g = c.add_gate(XORGate("XOR"), "xor")
        out = c.add_gate(OutputPin("Sum"), "sum")

        c.connect(in_a, xor_g, 0)
        c.connect(in_b, xor_g, 1)
        c.connect(xor_g, out, 0)

        gui = CircuitGUI(c)
        self.assertEqual(len(gui.nodes), 4)

        # Inputs should have x positions to the left of intermediate gates
        self.assertLess(gui.nodes["a"].x, gui.nodes["xor"].x)
        # Intermediate gates should have x positions to the left of outputs
        self.assertLess(gui.nodes["xor"].x, gui.nodes["sum"].x)

        # Toggle button should exist on input pins
        self.assertIsNotNone(gui.nodes["a"].get_toggle_rect())
        # Toggle button should not exist on output pins or XOR gates
        self.assertIsNone(gui.nodes["sum"].get_toggle_rect())
        self.assertIsNone(gui.nodes["xor"].get_toggle_rect())


if __name__ == "__main__":
    unittest.main()


