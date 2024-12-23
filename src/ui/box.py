import curses
from typing import Dict, Optional

class Box:
    def __init__(self, window: "curses.window", y: int, x: int, height: int, width: int):
        self.window = window
        self.y = y
        self.x = x
        self.height = height
        self.width = width
        self.content: Dict[str, str] = {}
        self.full_content: Optional[Dict[str, str]] = {}
        self.selected = False  # Whether the box is currently selected

    def draw(self):
        # Draw box border using the provided characters
        border_attr = curses.A_BOLD if self.selected else curses.A_NORMAL
        middle_y = self.height // 2  # Middle row
        middle_x = self.width // 2   # Middle column

        for i in range(self.height):
            for j in range(self.width):
                if i == 0 and j == 0:  # Top-left corner
                    char = "╔"
                elif i == 0 and j == self.width - 1:  # Top-right corner
                    char = "╗"
                elif i == self.height - 1 and j == 0:  # Bottom-left corner
                    char = "╚"
                elif i == self.height - 1 and j == self.width - 1:  # Bottom-right corner
                    char = "╝"
                elif i == 0 or i == self.height - 1:  # Top or bottom border
                    if self.selected and j == middle_x:
                        char = "╬"  # Replace middle character with ╬
                    else:
                        char = "═"
                elif j == 0 or j == self.width - 1:  # Left or right border
                    char = "║"
                else:
                    continue  # Skip the inner area
                try:
                    self.window.addch(self.y + i, self.x + j, char, border_attr)
                except curses.error:
                    pass

        # Draw content inside the box
        content_y = self.y + 1
        for key, value in self.content.items():
            if content_y < self.y + self.height - 1:  # Ensure we don't overwrite the bottom border
                try:
                    # Ensure content fits within the box width
                    self.window.addstr(content_y, self.x + 1, f"{key}: {value}"[:self.width-2])
                    content_y += 1
                except curses.error:
                    pass

    def update_content(self, content: Dict[str, str], full_content: Optional[Dict[str, str]] = None):
        self.content = content
        if full_content is not None:
            self.full_content = full_content
