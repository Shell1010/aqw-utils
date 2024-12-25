from typing import Any, Callable, Dict, List
from dataclasses import dataclass
from scapy.all import sniff, TCP, IP, Raw
from queue import Queue
from threading import Thread, Lock
import json
import time
from enum import Enum
import logging


class PacketType(Enum):
    AURA_PASSIVE = "aura+p"
    SKILL_DATA = "sAct"
    STAT_UPDATE = "stu"
    ITEM_UPDATE = "seia"
    COMBAT = "ct"
    UNKNOWN = "unknown"
    ADD_ITEM = "addItem"
    DROP_ITEM = "dropItem"
    # No actual killed monster packet with name, etc
    # I'll use this despite some edge cases existing
    # Some monsters don't drop either
    MONSTER_DEATH = "addGoldExp"

@dataclass
class GameEvent:
    type: PacketType
    data: Dict[str, Any]
    timestamp: float

class PacketCapture:
    def __init__(self):

        self.servers = {
            "Artix": "172.65.160.131",
            "Swordhaven (EU)": "172.65.207.70",
            "Yokai (SEA)": "72.65.236.72",
            "Safiria": "172.65.249.3",
            "Alteon": "172.65.235.85",
            "Sir Ver": "172.65.220.106",
            "Yorumi": "172.65.249.41",
        }

        self.packet_queue = Queue()
        self.running = True
        self.selected_server = ""
        self.buffer = ""
        self.data_lock = Lock()
        
        self.raw_json_data: List[str] = []
        self.stat_history: List[Dict[str, Any]] = []
        self.skill_data: Dict[str, Any] = {}
        self.aura_data: Dict[str, Any] = {}
        self.item_data: Dict[str, Any] = {}
        self.item_drops: List[Dict[str, Any]] = []
        self.added_item_drops: List[Dict[str, Any]] = []
        self.monster_death: List[Dict[str, Any]] = []
        self.last_obj = ""
        self.check_last = False
        self.callbacks: Dict[PacketType, List[Callable[[GameEvent], None]]] = {
            packet_type: [] for packet_type in PacketType
        }

    def register_callback(self, event_type: PacketType, callback: Callable[[GameEvent], None]):
        logging.debug(f"Added callback: {callback}")
        self.callbacks[event_type].append(callback)

    def _notify_callbacks(self, event: GameEvent):
        for callback in self.callbacks[event.type]:
            callback(event)

    def start(self, selected_server: str):
        self.selected_server = selected_server
        logging.debug("Starting capture thread")
        self.capture_thread = Thread(target=self._start_capture)
        logging.debug("Starting process packets thread")
        self.process_thread = Thread(target=self._process_packets)
        self.capture_thread.daemon = True
        self.process_thread.daemon = True
        self.capture_thread.start()
        logging.debug("Started capture thread")
        self.process_thread.start()
        logging.debug("Started process packet thread")

    def _start_capture(self):
        logging.debug(f"Beginning sniffing: {self.selected_server}")
        sniff(filter="tcp", prn=self._packet_callback, store=0)

    def extract_json_objects(self, data: str) -> tuple[list[str], str]:
        objects = []
        depth = 0
        start = 0
        in_string = False
        escaped = False

        for i, char in enumerate(data):
            if char == '"' and not escaped:
                in_string = not in_string

            if in_string:
                if char == '\\' and not escaped:
                    escaped = True
                else:
                    escaped = False
                continue

            if char == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    objects.append(data[start:i+1])
                    start = i + 1

        return objects, data[start:]

    def _packet_callback(self, packet):
        if not self.running:
            return

        if packet.haslayer(TCP) and packet.haslayer(IP):
            ip_src = packet[IP].src
            ip_dst = packet[IP].dst

            if (self.selected_server in self.servers and 
                (ip_src == self.servers[self.selected_server] or 
                 ip_dst == self.servers[self.selected_server])):
                
                if packet.haslayer(Raw):
                    logging.debug("Put packet in queue")
                    self.packet_queue.put(packet)

    def parse_data(self, data: dict[str, Any]) -> GameEvent:
        logging.debug(f"Parsing data: {data}")
        obj = data.get("b", {}).get("o", {})
        cmd = obj.get("cmd", "unknown")

        logging.debug(f"Command Type: {cmd}")
        logging.debug("Settings Packet Type")
        event_type = PacketType(cmd) if cmd in [e.value for e in PacketType] else PacketType.UNKNOWN
        logging.debug(f"Packet Type: {event_type}") 

        match event_type:
            case PacketType.AURA_PASSIVE:
                auras = obj.get('auras', [])
                for aura in auras:
                    self.aura_data[aura['nam']] = {
                        'effects': aura.get('e', []),
                        'timestamp': time.time()
                    }

            case PacketType.SKILL_DATA:
                logging.debug("Matching Skill Type")
                logging.debug("Processing SKILL_DATA")
                actives = obj.get('actions', {}).get('active', {})
                logging.debug(f"Active skills found: {actives}")
                self.skill_data = {
                    'skills': actives,
                    'timestamp': time.time()
                }

            case PacketType.STAT_UPDATE:
                stats = obj.get('sta', {})
                self.stat_history.append({
                    'stats': stats,
                    'timestamp': time.time()
                })

            case PacketType.ITEM_UPDATE:
                items = obj.get('o', {})
                self.item_data = {
                    'items': items,
                    'timestamp': time.time()
                }

            case PacketType.MONSTER_DEATH:
                self.monster_death.append({
                    'obj': obj,
                    'timestamp': time.time()
                })


            case PacketType.DROP_ITEM:
                self.item_drops.append({
                    'obj': obj,
                    'timestamp': time.time()
                })


            case PacketType.ADD_ITEM:
                self.added_item_drops.append({
                    'obj': obj,
                    'timestamp': time.time()
                })


            case PacketType.UNKNOWN:
                logging.debug("In Unknown")
                pass
        
        self.raw_json_data.append(json.dumps(data, indent=4))

        event = GameEvent(
            type=event_type,
            data=obj,
            timestamp=time.time()
        )

        logging.debug(f"Created event: {event}")
        return event

    def _process_packets(self):
        while self.running:
            if not self.packet_queue.empty():
                logging.debug("Got packet from queue")
                packet = self.packet_queue.get()
                payload = packet[Raw].load
                clean_payload = payload.replace(b'\x00', b'').decode('utf-8', errors='ignore')
                logging.debug(f"Length of payload: {len(clean_payload)}")
                if len(clean_payload) <= len(self.last_obj):
                    if clean_payload == self.last_obj[-len(clean_payload):] and self.check_last:
                        continue
                logging.debug("Locking in process packet")
                with self.data_lock:
                    self.buffer += clean_payload
                    logging.debug(f"Buffer Size: {len(self.buffer)}")
                    if len(self.buffer) > 1024:
                        logging.debug(f"OUTPUTTED BUFFER: {self.get_buffer()}")

                    logging.debug("Gathering json objects from queue packet")
                    json_objects, self.buffer = self.extract_json_objects(self.buffer)
                
                    for obj in json_objects:
                        try:
                            self.last_obj = obj
                            self.check_last = True
                            parsed_json = json.loads(obj)
                            logging.debug(f"Parsing json data: {parsed_json}")

                            event = self.parse_data(parsed_json)
                            logging.debug(f"Finished parsing data")
                            self._notify_callbacks(event)
                            logging.debug("Notified callbacks")
                        except json.JSONDecodeError:
                            continue
                logging.debug("Unlocked")
        logging.debug(f"No longer Running: {self.running}")

    def get_buffer(self) -> str:
        return self.buffer

    def get_latest_stats(self) -> Dict[str, Any]:
        with self.data_lock:
            return self.stat_history[-1] if self.stat_history else {}

    def get_skill_data(self) -> Dict[str, Any]:
        with self.data_lock:
            return self.skill_data

    def get_aura_data(self) -> Dict[str, Any]:
        with self.data_lock:
            return self.aura_data

    def get_potion_data(self) -> Dict[str, Any]:
        with self.data_lock:
            return self.item_data

    def get_recent_logs(self, count: int = 100) -> List[str]:
        with self.data_lock:
            return self.raw_json_data[-count:]
