from __future__ import annotations
import time
import re
from typing import TYPE_CHECKING
from fastapi import FastAPI, HTTPException, status
import uvicorn
from BaseClasses import MultiWorld, Location
from worlds import AutoWorld
if TYPE_CHECKING:
    from .TrackerClient import TrackerGameContext
    from . import CurrentTrackerState

STATUS_UPDATE_INTERVAL_SECONDS = 300.0

class API:
    instance = None
    
    def __init__(self, port: int, multiworld: MultiWorld):
        API.instance = self
        self.port: int = port
        self.api: FastAPI = None
        self.multiworld: MultiWorld = multiworld
        self.client: dict[str, TrackerGameContext] = {}
        self.state: dict[str, CurrentTrackerState] = {}
        self.status: dict[str, dict[str, Any]] = {}
        self.status_time: float = 0.0
        
    async def launch(self):
        print(f"Launching Universal Tracker API on port {self.port}.")
        
        self.api = FastAPI()
        self.api.add_api_route("/status", self.get_status, methods=[ "GET" ])
        self.api.add_api_route("/slots", self.get_slots, methods=[ "GET" ])
        self.api.add_api_route("/slots/{slot}", self.get_slots_slot, methods=[ "GET" ])
        self.api.add_api_route("/slots/{slot}/locations", self.get_slots_slot_locations, methods=[ "GET" ])
        self.api.add_api_route("/slots/{slot}/locations/checked", self.get_slots_slot_locations_checked, methods=[ "GET" ])
        self.api.add_api_route("/slots/{slot}/locations/missing", self.get_slots_slot_locations_missing, methods=[ "GET" ])
        self.api.add_api_route("/slots/{slot}/locations/reachable", self.get_slots_slot_locations_reachable, methods=[ "GET" ])
        #self.api.add_api_route("/debug", self.get_debug, methods=[ "GET" ])
        
        config = uvicorn.Config(self.api, host="0.0.0.0", port=self.port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()
    
    @property
    def any_client(self) -> TrackerGameContext:
        return self.client[self.multiworld.player_name[1]]
    
    def find_world(self, slot) -> "AutoWorld.World":
        return self.multiworld.worlds[self.multiworld.get_player_id(slot)]
    
    async def update_status(self) -> bool:
        now = time.time()
        age = now - self.status_time
        if age > STATUS_UPDATE_INTERVAL_SECONDS:
            await self.any_client.send_msgs([ { "cmd": "Say", "text": "!status" } ])
            self.status_time = now
            return True, age
        return False, age
    
    def on_status(self, text: str):
        self.status = {}
        lines = text.split("\n")
        for line in lines[1:]:
            match = re.search(r"(.*) has \d.*", line)
            slot = match.group(1)
            self.status[slot] = { "goal_complete": "and has finished" in line }

    async def get_status(self):
        stale, age = await self.update_status()
        return {
            "status_age_seconds": age,
            "status_will_update": stale,
            "status": self.status
        }
    
    def get_slots(self):
        return self.multiworld.player_name
    
    async def get_slots_slot(self, slot: str):
        await self.update_status()
        if slot in self.state:
            reachable_locations_count = len(self.get_slots_slot_locations_reachable(slot))
            return {
                "locations": len(self.get_slots_slot_locations(slot)),
                "checked_locations": len(self.get_slots_slot_locations_checked(slot)),
                "missing_locations": len(self.get_slots_slot_locations_missing(slot)),
                "reachable_locations": reachable_locations_count,
                "bk_mode": reachable_locations_count == 0,
                "go_mode": self.multiworld.has_beaten_game(self.state[slot].state, self.multiworld.get_player_id(slot)),
                "goal_complete": self.status[slot]["goal_complete"] if slot in self.status else None
            }
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND);
    
    def get_slots_slot_locations(self, slot: str):
        return [ *self.get_slots_slot_locations_checked(slot), *self.get_slots_slot_locations_missing(slot) ]
    
    def get_slots_slot_locations_checked(self, slot: str):
        if slot in self.client:
            return [ self.find_world(slot).location_id_to_name[location] for location in self.client[slot].checked_locations ]
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND);
    
    def get_slots_slot_locations_missing(self, slot: str):
        if slot in self.client:
            return [ self.find_world(slot).location_id_to_name[location] for location in self.client[slot].missing_locations ]
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND);
    
    def get_slots_slot_locations_reachable(self, slot: str):
        if slot in self.state:
            return self.state[slot].in_logic_locations
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND);
        
    def get_debug(self):
        return {}
