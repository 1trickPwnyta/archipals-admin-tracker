from typing import TYPE_CHECKING
from fastapi import FastAPI
import uvicorn
from BaseClasses import MultiWorld, Location
if TYPE_CHECKING:
    from .TrackerClient import TrackerGameContext
    from . import CurrentTrackerState

class API:
    instance = None
    
    def __init__(self, port: int, multiworld: MultiWorld):
        API.instance = self
        self.port: int = port
        self.api: FastAPI = None
        self.multiworld: MultiWorld = multiworld
        self.client: dict[str, TrackerGameContext] = {}
        self.state: dict[str, CurrentTrackerState] = {}
        
    async def launch(self):
        print(f"Launching Universal Tracker API on port {self.port}.")
        
        self.api = FastAPI()
        self.api.add_api_route("/slots", self.get_slots, methods=[ "GET" ])
        self.api.add_api_route("/slots/{slot}", self.get_slots_slot, methods=[ "GET" ])
        self.api.add_api_route("/slots/{slot}/locations", self.get_slots_slot_locations, methods=[ "GET" ])
        self.api.add_api_route("/slots/{slot}/locations/checked", self.get_slots_slot_locations_checked, methods=[ "GET" ])
        self.api.add_api_route("/slots/{slot}/locations/reachable", self.get_slots_slot_locations_reachable, methods=[ "GET" ])
        
        config = uvicorn.Config(self.api, host="0.0.0.0", port=self.port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()
    
    def get_slots(self):
        return self.multiworld.player_name
    
    def get_slots_slot(self, slot: str):
        return {
            "locations": len(self.get_slots_slot_locations(slot)),
            "checked_locations": len(self.get_slots_slot_locations_checked(slot)),
            "reachable_locations": len(self.get_slots_slot_locations_reachable(slot))
        }
    
    def get_slots_slot_locations(self, slot: str):
        return [ location.name for location in self.multiworld.get_locations(self.multiworld.get_player_id(slot)) ]
    
    def get_slots_slot_locations_checked(self, slot: str):
        return [ self.multiworld.worlds[self.multiworld.get_player_id(slot)].location_id_to_name[location] for location in self.client[slot].checked_locations ]
    
    def get_slots_slot_locations_reachable(self, slot: str):
        return self.state[slot].in_logic_locations
        