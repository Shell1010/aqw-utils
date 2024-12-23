import curses
from dataclasses import dataclass
from typing import Dict
from .packet_capture import PacketCapture
import time


@dataclass
class ItemDrop:
    name: str
    amount: int
    time_dropped: int
    
class DropsPage:
    def __init__(self, window: "curses.window", packet_capture: PacketCapture):
        self.drops: Dict[str, ItemDrop] = {}
        self.window = window
        self.packet_capture = packet_capture
        self.full_content_title = self.window.addstr(20, 2, "Class Full Content", curses.A_BOLD)

    def draw(self):
        self.window.erase()
        height, width = self.window.getmaxyx()
        title = "Drops UI"
        self.window.addstr(1, (width - len(title)) // 2, title, curses.A_BOLD)
        self.window.refresh()

    def handle_input(self):
        key = self.window.getch()
        if key == ord("q"):
            return "quit"
        elif key == ord("\n"):
            return ord("\n")

        return None


    def add_drop(self, drop: ItemDrop):
        pass
