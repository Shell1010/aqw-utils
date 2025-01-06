from ..packet_capture import PacketCapture, PacketType, GameEvent
import logging
from typing import List, Optional
import curses
from ..ui import Box

class RawLogs:
    def __init__(self, window: "curses.window", packet_capture: PacketCapture):
        self.window = window
        self.packet_capture = packet_capture


