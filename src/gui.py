"""
LogicCraft - Interactive Visual GUI using Pygame
Visualizes logic circuits, gate nodes, wires, toggle switches, and glowing LEDs in real time.
"""

import math
from typing import Dict, List, Optional, Tuple
import pygame
from src.gates import InputPin, OutputPin, SubCircuitGate
from src.circuit import Circuit


# Color Palette (Catppuccin / Modern Dark Theme)
BG_COLOR = (30, 30, 46)          # #1E1E2E
GRID_COLOR = (40, 40, 60)        # #28283C
HEADER_BG = (24, 24, 37)         # #181825
HEADER_TEXT = (205, 214, 244)    # #CDD6F4
NODE_BG = (49, 50, 68)           # #313244
NODE_HEADER_BG = (69, 71, 90)    # #45475A
NODE_BORDER = (137, 180, 250)    # #89B4FA
NODE_BORDER_HOVER = (245, 194, 231)
TEXT_WHITE = (245, 245, 245)
TEXT_MUTED = (166, 173, 200)

WIRE_ACTIVE = (0, 255, 170)      # Bright Neon Cyan/Green
WIRE_INACTIVE = (88, 91, 112)    # Slate Gray
SOCKET_IN = (180, 190, 254)      # Lavender
SOCKET_OUT = (249, 226, 175)     # Soft Gold

SWITCH_ON_BG = (166, 227, 161)   # Green
SWITCH_OFF_BG = (243, 139, 168)  # Red
LED_ON_CORE = (255, 235, 120)    # Glowing Yellow
LED_ON_GLOW = (255, 200, 50, 80)
LED_OFF = (40, 40, 55)


class NodeView:
    """Represents the graphical layout and interaction box of a single gate."""

    def __init__(self, gate_id: str, gate, x: float, y: float) -> None:
        self.gate_id: str = gate_id
        self.gate = gate
        self.x: float = x
        self.y: float = y

        # Sizing
        num_inputs = gate.num_inputs
        num_outputs = len(gate.outputs) if hasattr(gate, "outputs") else 1
        max_pins = max(num_inputs, num_outputs, 1)

        self.width: float = 140.0
        self.height: float = max(80.0, 35.0 + max_pins * 24.0)

        # Drag state
        self.dragging: bool = False
        self.drag_offset_x: float = 0.0
        self.drag_offset_y: float = 0.0

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), int(self.width), int(self.height))

    def get_input_socket_pos(self, index: int) -> Tuple[float, float]:
        """Calculates canvas coordinates for input pin index on left edge."""
        num = self.gate.num_inputs
        spacing = (self.height - 30.0) / (num + 1) if num > 0 else 0
        return (self.x, self.y + 26.0 + (index + 1) * spacing)

    def get_output_socket_pos(self, index: int = 0) -> Tuple[float, float]:
        """Calculates canvas coordinates for output pin index on right edge."""
        num = len(self.gate.outputs) if hasattr(self.gate, "outputs") else 1
        spacing = (self.height - 30.0) / (num + 1) if num > 0 else 0
        return (self.x + self.width, self.y + 26.0 + (index + 1) * spacing)

    def get_toggle_rect(self) -> Optional[pygame.Rect]:
        """Returns bounding box for toggle switch if this is an InputPin."""
        if isinstance(self.gate, InputPin):
            return pygame.Rect(int(self.x + 20), int(self.y + 36), int(self.width - 40), 30)
        return None

    def contains(self, px: float, py: float) -> bool:
        return self.rect.collidepoint(int(px), int(py))


class CircuitGUI:
    """
    Interactive Pygame Canvas for Digital Logic Circuit visual interaction.
    """

    def __init__(self, circuit: Circuit, width: int = 1050, height: int = 680) -> None:
        pygame.init()
        pygame.font.init()

        self.circuit: Circuit = circuit
        self.width: int = width
        self.height: int = height

        self.screen: pygame.Surface = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(f"LogicCraft - {circuit.name}")

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 14, bold=True)
        self.small_font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 12)
        self.header_font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 18, bold=True)

        self.nodes: Dict[str, NodeView] = {}
        self._init_layout()

        # Initial circuit evaluation
        self.circuit.evaluate()

    def _init_layout(self) -> None:
        """Computes automatic layered visual layout for circuit gates."""
        inputs = [gid for gid, g in self.circuit.gates.items() if isinstance(g, InputPin)]
        outputs = [gid for gid, g in self.circuit.gates.items() if isinstance(g, OutputPin)]
        intermediates = [
            gid for gid, g in self.circuit.gates.items()
            if not isinstance(g, (InputPin, OutputPin))
        ]

        layers: List[List[str]] = []
        if inputs:
            layers.append(inputs)

        if intermediates:
            sub_circuits = [gid for gid in intermediates if isinstance(self.circuit.gates[gid], SubCircuitGate)]
            other_gates = [gid for gid in intermediates if not isinstance(self.circuit.gates[gid], SubCircuitGate)]

            if sub_circuits and other_gates:
                layers.append(sub_circuits)
                layers.append(other_gates)
            elif len(intermediates) > 4:
                mid = len(intermediates) // 2
                layers.append(intermediates[:mid])
                layers.append(intermediates[mid:])
            else:
                layers.append(intermediates)

        if outputs:
            layers.append(outputs)

        num_layers = max(len(layers), 1)
        col_width = (self.width - 240) / max(num_layers - 1, 1)

        for col_idx, layer_gids in enumerate(layers):
            x = 80 + col_idx * col_width
            num_nodes = len(layer_gids)
            spacing = (self.height - 180) / max(num_nodes + 1, 1)

            for row_idx, gid in enumerate(layer_gids):
                gate = self.circuit.gates[gid]
                y = 110 + (row_idx + 1) * spacing - 35
                self.nodes[gid] = NodeView(gid, gate, x, y)

    def _draw_bezier_wire(
        self,
        surface: pygame.Surface,
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        active: bool,
    ) -> None:
        """Draws a smooth cubic Bézier wire connecting two pin sockets."""
        x1, y1 = p1
        x2, y2 = p2
        dx = max(abs(x2 - x1) * 0.5, 30.0)

        points: List[Tuple[float, float]] = []
        steps = 24
        for i in range(steps + 1):
            t = i / steps
            cx1, cy1 = x1 + dx, y1
            cx2, cy2 = x2 - dx, y2

            px = (1 - t) ** 3 * x1 + 3 * (1 - t) ** 2 * t * cx1 + 3 * (1 - t) * t ** 2 * cx2 + t ** 3 * x2
            py = (1 - t) ** 3 * y1 + 3 * (1 - t) ** 2 * t * cy1 + 3 * (1 - t) * t ** 2 * cy2 + t ** 3 * y2
            points.append((px, py))

        color = WIRE_ACTIVE if active else WIRE_INACTIVE
        width = 3 if active else 2
        pygame.draw.lines(surface, color, False, [(int(px), int(py)) for px, py in points], width)


    def _draw_node(self, surface: pygame.Surface, node: NodeView, mouse_pos: Tuple[int, int]) -> None:
        """Renders gate node box, sockets, labels, and interactive switch/LED components."""
        is_hovered = node.contains(mouse_pos[0], mouse_pos[1])
        border_color = NODE_BORDER_HOVER if is_hovered else NODE_BORDER

        # Draw Node Card
        rect = node.rect
        pygame.draw.rect(surface, NODE_BG, rect, border_radius=8)
        pygame.draw.rect(surface, border_color, rect, width=2, border_radius=8)

        # Header bar
        header_rect = pygame.Rect(rect.x, rect.y, rect.width, 24)
        pygame.draw.rect(surface, NODE_HEADER_BG, header_rect, border_top_left_radius=8, border_top_right_radius=8)

        title_surf = self.font.render(node.gate.name, True, TEXT_WHITE)
        surface.blit(title_surf, (rect.x + 8, rect.y + 4))

        # Input Sockets
        for i in range(node.gate.num_inputs):
            sx, sy = node.get_input_socket_pos(i)
            in_val = node.gate.inputs[i] if i < len(node.gate.inputs) else None
            sock_color = WIRE_ACTIVE if in_val else SOCKET_IN
            pygame.draw.circle(surface, sock_color, (int(sx), int(sy)), 5)
            pygame.draw.circle(surface, (20, 20, 30), (int(sx), int(sy)), 5, width=1)

        # Output Sockets
        num_outs = len(node.gate.outputs) if hasattr(node.gate, "outputs") else 1
        for i in range(num_outs):
            sx, sy = node.get_output_socket_pos(i)
            try:
                out_val = node.gate.get_output(i)
            except Exception:
                out_val = False
            sock_color = WIRE_ACTIVE if out_val else SOCKET_OUT
            pygame.draw.circle(surface, sock_color, (int(sx), int(sy)), 5)
            pygame.draw.circle(surface, (20, 20, 30), (int(sx), int(sy)), 5, width=1)

        # Node specific rendering
        if isinstance(node.gate, InputPin):
            btn_rect = node.get_toggle_rect()
            if btn_rect:
                state = node.gate.state
                bg_col = SWITCH_ON_BG if state else SWITCH_OFF_BG
                pygame.draw.rect(surface, bg_col, btn_rect, border_radius=6)
                pygame.draw.rect(surface, (255, 255, 255), btn_rect, width=1, border_radius=6)
                txt = "1 (HIGH)" if state else "0 (LOW)"
                text_col = (20, 20, 20)
                txt_surf = self.small_font.render(txt, True, text_col)
                surface.blit(txt_surf, txt_surf.get_rect(center=btn_rect.center))

        elif isinstance(node.gate, OutputPin):
            out_val = node.gate.output
            led_center = (int(rect.centerx), int(rect.y + 48))
            if out_val:
                glow_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (255, 235, 120, 90), (20, 20), 18)
                surface.blit(glow_surf, (led_center[0] - 20, led_center[1] - 20))
                pygame.draw.circle(surface, LED_ON_CORE, led_center, 10)
            else:
                pygame.draw.circle(surface, LED_OFF, led_center, 10)
            pygame.draw.circle(surface, (180, 180, 180), led_center, 10, width=1)

            val_txt = "HIGH" if out_val else "LOW"
            val_col = (255, 235, 120) if out_val else TEXT_MUTED
            val_surf = self.small_font.render(val_txt, True, val_col)
            surface.blit(val_surf, (rect.x + (rect.width - val_surf.get_width()) // 2, rect.y + 64))

        elif isinstance(node.gate, SubCircuitGate):
            sub_label = self.small_font.render("SubCircuit", True, (137, 180, 250))
            surface.blit(sub_label, (rect.x + 8, rect.y + 28))

        else:
            type_label = self.small_font.render(f"Type: {node.gate.__class__.__name__}", True, TEXT_MUTED)
            surface.blit(type_label, (rect.x + 8, rect.y + 28))

    def run(self) -> None:
        """Runs the interactive Pygame event and animation loop."""
        running = True
        dragging_node: Optional[NodeView] = None

        while running:
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        clicked_toggle = False
                        for node in self.nodes.values():
                            toggle_rect = node.get_toggle_rect()
                            if toggle_rect and toggle_rect.collidepoint(event.pos):
                                if isinstance(node.gate, InputPin):
                                    node.gate.set_state(not node.gate.state)
                                    self.circuit.evaluate()
                                    clicked_toggle = True
                                    break

                        if not clicked_toggle:
                            for node in reversed(list(self.nodes.values())):
                                if node.contains(event.pos[0], event.pos[1]):
                                    node.dragging = True
                                    node.drag_offset_x = node.x - event.pos[0]
                                    node.drag_offset_y = node.y - event.pos[1]
                                    dragging_node = node
                                    break

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1 and dragging_node:
                        dragging_node.dragging = False
                        dragging_node = None

                elif event.type == pygame.MOUSEMOTION:
                    if dragging_node and dragging_node.dragging:
                        dragging_node.x = event.pos[0] + dragging_node.drag_offset_x
                        dragging_node.y = event.pos[1] + dragging_node.drag_offset_y

            # Render canvas
            self.screen.fill(BG_COLOR)

            # Draw grid
            for gx in range(0, self.width, 30):
                pygame.draw.line(self.screen, GRID_COLOR, (gx, 60), (gx, self.height), 1)
            for gy in range(60, self.height, 30):
                pygame.draw.line(self.screen, GRID_COLOR, (0, gy), (self.width, gy), 1)

            # Draw Wires
            for conn in self.circuit.connections:
                src_node = self.nodes.get(conn.from_gate_id)
                dst_node = self.nodes.get(conn.to_gate_id)
                if src_node and dst_node:
                    p1 = src_node.get_output_socket_pos(conn.from_output_index)
                    p2 = dst_node.get_input_socket_pos(conn.to_input_index)
                    try:
                        active = src_node.gate.get_output(conn.from_output_index)
                    except Exception:
                        active = False
                    self._draw_bezier_wire(self.screen, p1, p2, active)

            # Draw Nodes
            for node in self.nodes.values():
                self._draw_node(self.screen, node, mouse_pos)

            # Header bar
            header_rect = pygame.Rect(0, 0, self.width, 60)
            pygame.draw.rect(self.screen, HEADER_BG, header_rect)
            pygame.draw.line(self.screen, (50, 50, 75), (0, 60), (self.width, 60), 2)

            title_txt = self.header_font.render(f"LogicCraft Simulator - {self.circuit.name}", True, HEADER_TEXT)
            self.screen.blit(title_txt, (20, 16))

            hint_txt = self.small_font.render(
                "Click [0/1] Input Switches to toggle | Drag gates to rearrange canvas",
                True,
                TEXT_MUTED,
            )
            self.screen.blit(hint_txt, (self.width - hint_txt.get_width() - 20, 22))

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()


