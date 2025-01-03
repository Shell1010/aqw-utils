import curses
import time
from typing import Optional, List, Dict, Any
import logging
from src import PacketCapture, ServerSelectionPage, ClassSkillsPage, packet_capture
from src import DropsPage
import toml


class GameMonitor:
    def __init__(self):
        self.packet_capture = PacketCapture()
        self.pages = {}
        self.page_order = ["class_data", "resource_monitor"]  
        self.current_page_index = 0

        conf = toml.load("./config.toml")
        self.is_select = conf['drops'].get("select_server", False)

    def init_curses(self, stdscr: "curses.window"):
        curses.curs_set(0)  
        curses.use_default_colors()
        curses.start_color()
        curses.init_color(curses.COLOR_YELLOW, 1000, 800, 17)
        curses.init_color(curses.COLOR_GREEN, 100, 700, 17)
        curses.init_pair(1, curses.COLOR_YELLOW, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1 )


        stdscr.timeout(100)  
        return stdscr

    def run(self):
        curses.wrapper(self._run)

    def _run(self, stdscr: "curses.window"):
        stdscr = self.init_curses(stdscr)

        self.pages = {
            "server_selection": ServerSelectionPage(stdscr, self.packet_capture),
            "class_data": ClassSkillsPage(stdscr, self.packet_capture),
            "resource_monitor": DropsPage(stdscr, self.packet_capture),
        }

        if self.is_select:

            self.current_page = self.pages["server_selection"]
        else:
            self.current_page = self.pages["class_data"]
            self.packet_capture.start()

        while True:
            self.current_page.draw()

            if self.current_page != self.pages["server_selection"]:
                self.draw_navigation_bar(stdscr)

            next_page = self.handle_input()
            if next_page == "quit":
                break
            elif next_page in self.pages:
                self.current_page = self.pages[next_page]

            time.sleep(0.0005)

    def draw_navigation_bar(self, stdscr: "curses.window"):
        height, width = stdscr.getmaxyx()
        nav_bar_y = height - 1  

        nav_bar = " | ".join(
            [
                f"[{'>>' if i == self.current_page_index else ''}{name.title()}]"
                for i, name in enumerate(self.page_order)
            ]
        )

        nav_bar_x = (width - len(nav_bar)) // 2

        try:
            stdscr.addstr(nav_bar_y, nav_bar_x, nav_bar, curses.A_BOLD)
        except curses.error:
            pass

    def handle_input(self) -> Optional[str]:
        page_or_key = self.current_page.handle_input()

        if isinstance(page_or_key, int):

            if page_or_key == ord("\n"): 
                if self.current_page == self.pages["server_selection"]:
                    logging.debug("Navigating from server_selection to the first page in page_order.")
                    self.current_page = self.pages[self.page_order[0]]
                    self.current_page_index = 0
                    return None
                else:
                    self.current_page_index = (self.current_page_index + 1) % len(self.page_order)
                    self.current_page = self.pages[self.page_order[self.current_page_index]]
                    logging.debug(f"Switched to page: {self.page_order[self.current_page_index]}")
                    return None

            elif page_or_key == ord("q"):
                return "quit"
            
            elif page_or_key == ord("p"):
                logging.debug(f"OUTPUTTED BUFFER: {self.packet_capture.get_buffer()}")
                return None

        if isinstance(page_or_key, str):
            if page_or_key == "quit": 
                return "quit"

            if page_or_key in self.pages:
                self.current_page = self.pages[page_or_key]
                if page_or_key in self.page_order:
                    self.current_page_index = self.page_order.index(page_or_key)
                logging.debug(f"Page switched via page-specific logic to: {page_or_key}")
                return None

        return None

def main():
    monitor = GameMonitor()
    monitor.run()

if __name__ == "__main__":
    import sys

    if '--logging' in sys.argv:
        logging.basicConfig(
            filename='game_monitor_debug.log',
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    main()
