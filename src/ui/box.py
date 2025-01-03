import curses
from typing import Dict, Optional

class Box:
    def __init__(self, window: "curses.window", y: int, x: int, height: int, width: int, title: Optional[str] = None):
        self.window = window
        self.y = y
        self.x = x
        self.height = height
        self.width = width
        self.content: Dict[str, str] = {}
        self.full_content: Optional[Dict[str, str]] = {}
        self.selected = False  # Whether the box is currently selected
        self.title = title

    def draw(self):
        if self.selected:
            border_attr = curses.color_pair(1) | curses.A_BOLD
        else:
            border_attr = curses.color_pair(2) | curses.A_NORMAL 
        middle_x = self.width // 2   

        for i in range(self.height):
            for j in range(self.width):
                if i == 0 and j == 0:  
                    char = "╭"
                elif i == 0 and j == self.width - 1:  
                    char = "╮"
                elif i == self.height - 1 and j == 0:  
                    char = "╰"
                elif i == self.height - 1 and j == self.width - 1:  
                    char = "╯"
                elif i == 0 or i == self.height - 1:  
                    if self.selected and j == middle_x:
                        char = "┼"
                    else:
                        char = "─"
                elif j == 0 or j == self.width - 1: 
                    char = "│"
                else:
                    continue 
                try:
                    self.window.addch(self.y + i, self.x + j, char, border_attr)
                except curses.error:
                    pass

        if self.title and len(self.title) < self.width - 4:
            try:
                title_x = self.x + 2
                self.window.addstr(self.y, title_x, self.title, border_attr)
            except:
                pass
        content_y = self.y + 1
        for key, value in self.content.items():
            if content_y < self.y + self.height - 1:  
                try:
                    if self.selected:
                        self.window.addstr(content_y, self.x + 1, f"{key}:", curses.color_pair(2) | curses.A_BOLD )

                        key_width = len(f"{key}:")
                        self.window.addstr(content_y, self.x + 1 + key_width, f" {value}"[:self.width - 2 - key_width], curses.A_BOLD)
                        content_y += 1
                    else:
                        self.window.addstr(content_y, self.x + 1, f"{key}:", curses.color_pair(2) )

                        key_width = len(f"{key}:")
                        self.window.addstr(content_y, self.x + 1 + key_width, f" {value}"[:self.width - 2 - key_width])
                        content_y += 1
                except curses.error:
                    pass


    def update_content(self, content: Dict[str, str], full_content: Optional[Dict[str, str]] = None):
        self.content = content
        if full_content is not None:
            self.full_content = full_content


class DropBox:
    def __init__(self, window: "curses.window", y: int, x: int, height: int, width: int, title: Optional[str] = None):
        self.window = window
        self.y = y
        self.x = x
        self.height = height
        self.width = width
        self.content: Dict[str, Dict[str, str]] = {}
        self.title = title
        self.indent = "  "
        self.selected_index = 0  
        self.headers = []

    def draw(self):
        border_attr = curses.A_NORMAL
        middle_x = self.width // 2   

        for i in range(self.height):
            for j in range(self.width):
                if i == 0 and j == 0:  
                    char = "╭"
                elif i == 0 and j == self.width - 1:  
                    char = "╮"
                elif i == self.height - 1 and j == 0:  
                    char = "╰"
                elif i == self.height - 1 and j == self.width - 1:  
                    char = "╯"
                elif i == 0 or i == self.height - 1:  
                    char = "─"
                elif j == 0 or j == self.width - 1: 
                    char = "│"
                else:
                    continue 
                try:
                    self.window.addch(self.y + i, self.x + j, char, curses.color_pair(2) | border_attr)
                except curses.error:
                    pass

        if self.title and len(self.title) < self.width - 4:
            try:
                title_x = self.x + 2
                self.window.addstr(self.y, title_x, self.title,  curses.color_pair(2) | border_attr)
            except:
                pass

        content_y = self.y + 1
        for i, (header, stats) in enumerate(self.content.items()):
            if content_y < self.y + self.height - 2:
                try:
                    header_style = curses.color_pair(2) | curses.A_REVERSE | curses.A_BOLD if i == self.selected_index else curses.color_pair(2) | curses.A_BOLD
                    self.window.addstr(content_y, self.x + 1, header[:self.width-2], header_style)
                    content_y += 1
                    
                    for key, value in stats.items():
                        if content_y < self.y + self.height - 2:
                            self.window.addstr(content_y, self.x + 1, f"{self.indent}{key}:", curses.color_pair(2) )

                            key_width = len(f"{self.indent}{key}:")
                            self.window.addstr(content_y, self.x + 1 + key_width, f" {value}"[:self.width - 2 - key_width])
                            content_y += 1
                    content_y += 1
                except curses.error:
                    pass

    def update_content(self, content: Dict[str, Dict[str, str]]):
        self.content = content
        self.headers = list(content.keys())

    


    def get_selected_header(self) -> Optional[str]:
        if self.headers:
            return self.headers[self.selected_index]
        return None
