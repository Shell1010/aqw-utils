import curses
from dataclasses import dataclass
from typing import Dict, Optional
from ..packet_capture import GameEvent, PacketCapture, PacketType
from ..ui import Box, DropBox
import time
import logging
import math
import toml

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
        conf = toml.load("./config.toml")
        self.rates_expiry = conf['drops'].get("rates_expiry", 60)
        self.drops_expiry = conf['drops'].get("drops_expiry", 3600)
        self.total_gold = 0
        self.total_exp = 0
        self.total_rep = 0
        self.monster_kills = 0
        self.last_kill_time = 0
        self.item_stats = {}  # {item_name: {"drop_count": int, "quantity_dropped": int, "estimated_drop_rate": float, "kills_until_90": float}}
        self.first_kill = True
        self.start_time = 0
        self.elapsed_time = 0


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
                        "drops_per_second": 0.0,
                        "drops_per_minute": 0.0,
                        "drops_per_hour": 0.0
                    }

                self.item_stats[item_name]["drop_count"] += 1
                self.item_stats[item_name]["quantity_dropped"] += quantity
                self.item_stats[item_name]["last_drop_time"] = current_time

                
            for item_name in list(self.item_stats.keys()):
                if current_time - self.item_stats[item_name]["last_drop_time"] > self.drops_expiry:
                    del self.item_stats[item_name]

        except Exception as e:
            logging.error(f"Error in processing drop event: {e}")


    def death_update(self, event: GameEvent):
        # try:
        data = event.data
        current_time = time.time()

        self.total_gold += data.get("intGold", 0)
        self.total_exp += data.get("intExp", 0)
        self.total_rep += data.get("iRep", 0)
        logging.debug(f"Death update data: {data}")
        if data['typ'] == "m":
            if self.first_kill:
                self.start_time = current_time
                self.first_kill = False
            self.monster_kills += 1
            self.last_kill_time = current_time



        

        for item_name, stats in self.item_stats.items():
            drop_count = stats["drop_count"]
            if self.monster_kills > 0:
                stats["estimated_drop_rate"] = (drop_count / self.monster_kills) * 100
                p = drop_count / self.monster_kills
                if p == 1:
                    p = 0.9999
                if p > 0:
                    logging.debug(f"P value: {p}")
                    stats["kills_until_90"] = math.ceil(math.log(1 - 0.9) / math.log(1 - p))
                else:
                    stats["kills_until_90"] = float("inf")

        logging.debug(f"Monster death data: {data}")
        logging.debug(f"Total gold: {self.total_gold}, Total experience: {self.total_exp}")
        # except Exception as e:
        #     logging.error(f"Error in processing monster death event: {e}")

    def get_rates(self) -> Dict[str, float]:
        current_time = time.time()

        

        if self.last_kill_time and current_time - self.last_kill_time > self.rates_expiry:
            for item_name in list(self.item_stats.keys()):
                self.item_stats[item_name]['drop_count'] = 0 
            self.monster_kills = 0
            self.total_exp = 0
            self.total_gold = 0
            self.total_rep = 0
            self.first_kill = True
            return {"gps": 0, "gpm": 0, "gph": 0, "eps": 0, "epm": 0, "eph": 0, "rps": 0, "rpm": 0, "rph": 0, "kps": 0, "kpm": 0, "kph": 0}

        self.elapsed_time = current_time - self.start_time
        if self.elapsed_time == 0:  
            return {"gps": 0, "gpm": 0, "gph": 0, "eps": 0, "epm": 0, "eph": 0, "rps": 0, "rpm": 0, "rph": 0, "kps": 0, "kpm": 0, "kph": 0}

        gps = self.total_gold / self.elapsed_time
        gpm = gps * 60
        gph = gps * 3600

        eps = self.total_exp / self.elapsed_time
        epm = eps * 60
        eph = eps * 3600

        rps = self.total_rep / self.elapsed_time
        rpm = rps * 60
        rph = rps * 3600

        kps = self.monster_kills / self.elapsed_time
        kpm = kps * 60
        kph = kps * 3600

        for item_name in list(self.item_stats.keys()):
            if not self.first_kill:
                elapsed = current_time - self.start_time
                if elapsed > 0:
                    drops_per_second = self.item_stats[item_name]["quantity_dropped"] / elapsed
                    self.item_stats[item_name]["drops_per_second"] = drops_per_second
                    self.item_stats[item_name]["drops_per_minute"] = drops_per_second * 60
                    self.item_stats[item_name]["drops_per_hour"] = drops_per_second * 3600


        return {"gps": gps, "gpm": gpm, "gph": gph, "eps": eps, "epm": epm, "eph": eph, "rps": rps, "rpm": rpm, "rph": rph, "kps": kps, "kpm": kpm, "kph": kph}

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
            title="Gold"
        )

        exp_y = gold_y
        exp_x = gold_x + box_width + 4 
        self.exp_box = Box(
            self.window,
            y=exp_y,
            x=exp_x,
            height=box_height,
            width=box_width,
            title="EXP"
        )


        rep_y = gold_y
        rep_x = exp_x + box_width + 4
        self.rep_box = Box(
            self.window,
            y=rep_y,
            x=rep_x,
            height=box_height,
            width=box_width,
            title="Rep"
        )

        drop_y = gold_y + 9
        drop_x = 2
        drop_width = ((gold_x + box_width + 4) * 2) - 8
        self.drop_box = DropBox(
            self.window,
            y=drop_y,
            x=drop_x,
            height=34,
            width=drop_width,
            title="Item Drops"
        )
        kill_y = drop_y
        kill_x = drop_x + ((gold_x + box_width) * 2) + 4
        self.kill_box = Box(
            self.window,
            y=kill_y,
            x=kill_x,
            height=box_height,
            width=box_width,
            title="Kills"
        )

        stats_y = kill_y + 9
        stats_x = kill_x
        self.stats_box = Box(
            self.window,
            y=stats_y,
            x=stats_x,
            height=box_height,
            width=box_width,
            title="Farm Stats"
        )

    def draw(self):
        self.window.erase()
        height, width = self.window.getmaxyx()
        title = "Resource Monitor"
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

        self.rep_box.update_content(
            {
                "Rep/s": f"{rates['rps']:.2f}",
                "Rep/m": f"{rates['rpm']:.2f}",
                "Rep/h": f"{rates['rph']:.2f}",
            }
        )

        self.kill_box.update_content(
            {
                "Kill/s": f"{rates['kps']:.2f}",
                "Kill/m": f"{rates['kpm']:.2f}",
                "Kill/h": f"{rates['kph']:.2f}"
            }
        )

        hours, remainder = divmod(int(self.elapsed_time), 3600)
        minutes, seconds = divmod(remainder, 60)
        self.stats_box.update_content(
            {
                "Time": f"{hours}:{minutes}:{seconds}",
                "Kills": f"{self.monster_kills}",
                "Gold": f"{self.total_gold}",
                "Exp": f"{self.total_exp}",
                "Rep": f"{self.total_rep}",
            }
        )
        sorted_items = sorted(
            self.item_stats.items(),
            key=lambda x: x[1]['last_drop_time'],
            reverse=True
        )

        drop_content = {}
        for i, (item_name, stats) in enumerate(sorted_items[:5]):
            drop_content[item_name] = {
                "Drop Rate": f"{stats['estimated_drop_rate']:.2f}%",
                "Next Drop": f"~ {stats['kills_until_90']} kills",
                "Drop/s": f"{stats['drops_per_second']:.2f}",
                "Drop/m": f"{stats['drops_per_minute']:.2f}",
                "Drop/h": f"{stats['drops_per_hour']:.2f}"
            }

        self.drop_box.update_content(drop_content)
    

        self.gold_box.draw()
        self.exp_box.draw()
        self.drop_box.draw()
        self.rep_box.draw()
        self.kill_box.draw()
        self.stats_box.draw()

        self.window.refresh()
    
    def handle_input(self):
        key = self.window.getch()
        if key == ord("q"):
            return "quit"
        elif key == ord("\n"):
            return ord("\n")
        elif key == ord("p"):
            return ord("p")
        return None



