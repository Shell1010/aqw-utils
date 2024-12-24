import curses
from dataclasses import dataclass
from typing import Dict, Optional
from .packet_capture import GameEvent, PacketCapture, PacketType
from .ui import Box
import time
import logging
import math


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
        self.setup_boxes()

        self.total_gold = 0
        self.total_exp = 0
        self.monster_kills = 0
        self.last_kill_time: Optional[float] = None
        self.item_stats = {}  # {item_name: {"drop_count": int, "quantity_dropped": int, "estimated_drop_rate": float, "kills_until_90": float}}

        self.start_time = time.time()

        self.packet_capture.register_callback(PacketType.MONSTER_DEATH, self.death_update)
        self.packet_capture.register_callback(PacketType.DROP_ITEM, self.drop_update)

    def drop_update(self, event: GameEvent):
        try:
            data = event.data["items"]
            current_time = time.time()
            for item_id, item_data in data.items():
                item_name = item_data["sName"]
                quantity = item_data["iQty"]

                if item_name not in self.item_stats:
                    self.item_stats[item_name] = {
                        "drop_count": 0,
                        "quantity_dropped": 0,
                        "estimated_drop_rate": 0.0,
                        "kills_until_90": float("inf"),
                        "last_drop_time": current_time,
                    }

                self.item_stats[item_name]["drop_count"] += 1
                self.item_stats[item_name]["quantity_dropped"] += quantity
                self.item_stats[item_name]["last_drop_time"] = current_time

            for item_name in list(self.item_stats.keys()):
                if current_time - self.item_stats[item_name]["last_drop_time"] > 3600:
                    del self.item_stats[item_name]

        except Exception as e:
            logging.error(f"Error in processing drop event: {e}")

    def death_update(self, event: GameEvent):
        try:
            data = event.data
            current_time = time.time()

            self.total_gold += data.get("intGold", 0) + data.get("bonusGold", 0)
            self.total_exp += data.get("intExp", 0)
            self.monster_kills += 1
            self.last_kill_time = current_time

            if current_time - self.last_kill_time > 120:
                self.monster_kills = 0

            for item_name, stats in self.item_stats.items():
                drop_count = stats["drop_count"]
                if self.monster_kills > 0:
                    stats["estimated_drop_rate"] = (drop_count / self.monster_kills) * 100
                    p = drop_count / self.monster_kills
                    if p > 0:
                        stats["kills_until_90"] = math.ceil(math.log(1 - 0.9) / math.log(1 - p))
                    else:
                        stats["kills_until_90"] = float("inf")

            logging.debug(f"Monster death data: {data}")
            logging.debug(f"Total gold: {self.total_gold}, Total experience: {self.total_exp}")
        except Exception as e:
            logging.error(f"Error in processing monster death event: {e}")

    def get_rates(self) -> Dict[str, float]:
        current_time = time.time()

        if self.last_kill_time and current_time - self.last_kill_time > 60:
            self.total_exp = 0
            self.total_gold = 0
            return {"gps": 0, "gpm": 0, "gph": 0, "eps": 0, "epm": 0, "eph": 0}

        elapsed_time = current_time - self.start_time
        if elapsed_time == 0:  
            return {"gps": 0, "gpm": 0, "gph": 0, "eps": 0, "epm": 0, "eph": 0}

        gps = self.total_gold / elapsed_time
        gpm = gps * 60
        gph = gps * 3600

        eps = self.total_exp / elapsed_time
        epm = eps * 60
        eph = eps * 3600

        return {"gps": gps, "gpm": gpm, "gph": gph, "eps": eps, "epm": epm, "eph": eph}

    def setup_boxes(self):
        height, width = self.window.getmaxyx()
        box_height = 8
        box_width = width // 3 - 4

        gold_y = 3
        gold_x = 2
        self.gold_box = Box(
            self.window,
            y=gold_y,
            x=gold_x,
            height=box_height,
            width=box_width,
        )

        exp_y = gold_y
        exp_x = gold_x + box_width + 4 
        self.exp_box = Box(
            self.window,
            y=exp_y,
            x=exp_x,
            height=box_height,
            width=box_width,
        )


        rep_y = gold_y
        rep_x = exp_x + box_width + 4
        self.rep_box = Box(
            self.window,
            y=rep_y,
            x=rep_x,
            height=box_height,
            width=box_width
        )

        drop_y = gold_y + 9
        drop_x = 2
        self.drop_box = Box(
            self.window,
            y=drop_y,
            x=drop_x,
            height=35,
            width=((gold_x + box_width + 4) * 2) - 8

        )

    def draw(self):
        self.window.erase()
        height, width = self.window.getmaxyx()
        title = "Drops UI"
        self.window.addstr(1, (width - len(title)) // 2, title, curses.A_BOLD)

        rates = self.get_rates()

        self.gold_box.update_content(
            {
                "Gold/s": f"{rates['gps']:.2f}",
                "Gold/m": f"{rates['gpm']:.2f}",
                "Gold/h": f"{rates['gph']:.2f}",
            }
        )

        self.exp_box.update_content(
            {
                "Exp/s": f"{rates['eps']:.2f}",
                "Exp/m": f"{rates['epm']:.2f}",
                "Exp/h": f"{rates['eph']:.2f}",
            }
        )

        drop_content = {}
        for i, (item_name, stats) in enumerate(self.item_stats.items()):
            if i < 32:
                drop_content[item_name] = (
                    f"Drop Rate: {stats['estimated_drop_rate']:.2f}%, "
                    f"Next Drop: ~{stats['kills_until_90']} kills"
                )
        self.drop_box.update_content(drop_content)

        self.gold_box.draw()
        self.exp_box.draw()
        self.drop_box.draw()
        self.rep_box.draw()

        self.window.refresh()
    
    def handle_input(self):
        key = self.window.getch()
        if key == ord("q"):
            return "quit"
        elif key == ord("\n"):
            return ord("\n")

        return None



