import curses

from scapy.all import logging
from ..packet_capture import PacketCapture
import toml
from typing import Optional

class ServerSelectionPage:
    def __init__(self, window: "curses.window", packet_capture: PacketCapture):
        self.window = window
        self.packet_capture = packet_capture
        self.selected_idx = 0
        self.servers = list(packet_capture.servers.keys())
        
    def draw(self):
        self.window.erase()
        height, width = self.window.getmaxyx()

        ascii_art = r"""

░█████╗░░██████╗░░██╗░░░░░░░██╗    ██╗░░░██╗████████╗██╗██╗░░░░░░██████╗
██╔══██╗██╔═══██╗░██║░░██╗░░██║    ██║░░░██║╚══██╔══╝██║██║░░░░░██╔════╝
███████║██║██╗██║░╚██╗████╗██╔╝    ██║░░░██║░░░██║░░░██║██║░░░░░╚█████╗░
██╔══██║╚██████╔╝░░████╔═████║░    ██║░░░██║░░░██║░░░██║██║░░░░░░╚═══██╗
██║░░██║░╚═██╔═╝░░░╚██╔╝░╚██╔╝░    ╚██████╔╝░░░██║░░░██║███████╗██████╔╝
╚═╝░░╚═╝░░░╚═╝░░░░░░╚═╝░░░╚═╝░░    ░╚═════╝░░░░╚═╝░░░╚═╝╚══════╝╚═════╝░
        """
        art_lines = ascii_art.split("\n")
        for i, line in enumerate(art_lines):
            self.window.addstr(i, (width - len(line)) // 2, line, curses.color_pair(1))

        title = "Select Server"
        self.window.addstr(
            len(art_lines) + 1, (width - len(title)) // 2, title, curses.color_pair(2) | curses.A_BOLD
        )

        for i, server in enumerate(self.servers):
            y = len(art_lines) + 3 + i
            x = (width - len(server)) // 2
            if i == self.selected_idx:
                self.window.addstr(y, x, server, curses.color_pair(2) | curses.A_REVERSE)
            else:
                self.window.addstr(y, x, server, curses.color_pair(2))

        instructions = "Use ↑/↓ to select, Enter to confirm, q to quit"
        self.window.addstr(height - 2, (width - len(instructions)) // 2, instructions)

        self.window.refresh()

    def handle_input(self) -> Optional[str|int]:
        key = self.window.getch()
        if key == curses.KEY_UP and self.selected_idx > 0:
            self.selected_idx -= 1
        elif key == curses.KEY_DOWN and self.selected_idx < len(self.servers) - 1:
            self.selected_idx += 1
        elif key in (curses.KEY_ENTER, 10, 13):  # Enter key
            selected_server = self.servers[self.selected_idx]
            logging.debug(f"Selected Server: {selected_server}")
            self.packet_capture.start(selected_server)
            return "class_data"
        elif key == ord("q"):
            return "quit"
        elif key == ord("\n"):
            return ord("\n")
        return None
