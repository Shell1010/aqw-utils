from .packet_capture import PacketCapture, PacketType, GameEvent
import logging
from typing import List, Optional
import curses
from .ui import Box


class ClassSkillsPage:

    def __init__(self, window: "curses.window", packet_capture: PacketCapture):
        self.window = window
        self.packet_capture = packet_capture
        self.skill_boxes: List[Box] = []
        self.passive_boxes: List[Box] = []
        self.selected_index = 0  # Index of the currently selected box
        self.setup_boxes()
        height, width = self.window.getmaxyx()
        self.full_content = Box(window, 20, 2, 26, width // 3 - 4)
        self.packet_capture.register_callback(PacketType.SKILL_DATA, self.update_skills)
        self.packet_capture.register_callback(PacketType.ITEM_UPDATE, self.update_pots)
        self.packet_capture.register_callback(PacketType.AURA_PASSIVE, self.update_passives)
        logging.info("ClassSkillsPage initialized")

    def setup_boxes(self):
        height, width = self.window.getmaxyx()
        box_height = 8
        box_width = width // 3 - 4

        # Create 6 boxes in a 2x3 grid
        for i in range(2):  # rows
            for j in range(3):  # columns
                y = 3 + i * (box_height + 1)
                x = 2 + j * (box_width + 2)
                self.skill_boxes.append(Box(self.window, y, x, box_height, box_width))

    
        middle_skill_box = self.skill_boxes[4]  # Middle box in the 2nd row
        passive_x = middle_skill_box.x  # Align horizontally with the middle skill box
        passive_start_y = middle_skill_box.y + box_height # Place right below it

        for i in range(3):  # Create 3 passive boxes in a column
            y = passive_start_y + i * (box_height + 1)
            self.passive_boxes.append(Box(self.window, y, passive_x, box_height, box_width))

            self.skill_boxes[0].selected = True

    def update_passives(self, event: GameEvent):

        logging.debug(f"Received event: {event}")
        logging.debug(f"Full event data: {event.data}")

        try:
            logging.debug("Doing Passive Update")
            logging.debug(f"Passive data here: {event.data}")
            auras = event.data.get("auras", [])
            for i, aura in enumerate(auras):
                # Process the stat modifications
                stat_details = []
                for effect in aura.get("e", []):
                    stat = effect.get("sta", "N/A")
                    value = effect.get("val", "N/A")
                    modifier = effect.get("typ", "+")
                    stat_details.append(f"{stat}{modifier}{value}")

                # Join the stat details into a single string, separated by commas
                stats_text = ", ".join(stat_details) if stat_details else "N/A"

                # Update the box content
                self.passive_boxes[i].update_content(
                    {
                        "Passive Name": aura.get("nam", "N/A"),
                        "Stats": stats_text
                    }
                )
            logging.debug(f"Passive boxes: {len(self.passive_boxes)}")

        except Exception as e:
            logging.error("failed")

    def update_pots(self, event: GameEvent):

        logging.debug(f"Received event: {event}")
        logging.debug(f"Full event data: {event.data}")


        try:
            logging.debug("Doing Item Update")
            data = event.data.get("o")
            logging.debug(f"{data}")
            if data:
                content = {
                    "Function": str(data.get("dsrc", "N/A")),
                    "Targets": str(data.get("tgtMin", "N/A")),
                    "Damage": str(data.get("damage", "N/A"))
                }
                self.skill_boxes[-1].update_content(content, data)
            else:
                logging.debug("fail")
            
        except Exception as e:
            logging.error("failed")


    def update_skills(self, event: GameEvent):
        logging.debug(f"Received event: {event}")
        logging.debug(f"Full event data: {event.data}")

        # Debug info to show in UI
        debug_content = {}

        try:
            actions = event.data.get("actions", {})
            logging.debug(f"Actions data: {actions}")

            active_skills = actions.get("active", [])
            logging.debug(f"Active skills: {active_skills}")

            debug_content["Event Type"] = str(event.type)
            debug_content["Skills Count"] = str(
                len(active_skills) if active_skills else "0"
            )
            debug_content["Raw Data"] = (
                str(event.data)[:50] + "..."
            )  # Truncated for display

            if active_skills:
                for i, skill in enumerate(active_skills):
                    # content = {}
                    # for key, value in skill.items():
                    #     content[key] = value
                    if i < len(self.skill_boxes):
                        if i >= 5:
                            continue
                        logging.debug(f"Processing skill {i}: {skill}")
                        content = {
                            "Skill Name": str(skill.get("nam", "Unknown")),
                            "Damage": str(skill.get("damage", "N/A")),
                            "Function": str(skill.get("dsrc", "N/A")),
                            "Cooldown": str(skill.get("cd", "N/A")),
                            "Mana": str(skill.get("mp", "N/A")),
                        }
                        self.skill_boxes[i].update_content(content, skill)

                        logging.debug(f"Updated box {i} with content: {content}")
            else:
                logging.warning("No active skills found in event data")
        except Exception as e:
            logging.error(f"Error in update_skills: {str(e)}", exc_info=True)
            debug_content["Error"] = str(e)

        # Update debug box

    def draw(self):
        self.window.erase()
        height, width = self.window.getmaxyx()

        # Draw title
        title = "Current Class Skills"
        self.window.addstr(1, (width - len(title)) // 2, title, curses.A_BOLD)

        # Draw all boxes
        for box in self.skill_boxes:
            box.draw()

        for box in self.passive_boxes:
            box.draw()
        self.full_content.draw()
    
        # self.debug_box.draw()

        self.window.refresh()

    def handle_input(self) -> Optional[str|int]:
        key = self.window.getch()
        if key == ord("q"):
            return "quit"

        elif key in (curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT):
            self.move_cursor(key)
            self.send_full_content()

        if key == ord("\n"):
            return ord("\n")

        return None

    def move_cursor(self, key):
        old_index = self.selected_index
        if key == curses.KEY_UP:
            self.selected_index = (self.selected_index - 3) % len(self.skill_boxes)  # Move up a row
        elif key == curses.KEY_DOWN:
            self.selected_index = (self.selected_index + 3) % len(self.skill_boxes)  # Move down a row
        elif key == curses.KEY_LEFT:
            self.selected_index = (self.selected_index - 1) % len(self.skill_boxes)  # Move left
        elif key == curses.KEY_RIGHT:
            self.selected_index = (self.selected_index + 1) % len(self.skill_boxes)  # Move right

        # Update selection
        self.skill_boxes[old_index].selected = False
        self.skill_boxes[self.selected_index].selected = True

    def send_full_content(self):
        selected_box = self.skill_boxes[self.selected_index]
        if selected_box.full_content is not None:
            content = {k: v for k,v in selected_box.full_content.items() if k not in ["desc", "icon"]}

            self.full_content.update_content(content)

        logging.info(f"Selected Box Full Content: {selected_box.full_content}")
