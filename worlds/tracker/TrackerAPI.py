from fastapi import FastAPI
import uvicorn
from BaseClasses import MultiWorld, Location
from . import CurrentTrackerState

class API:
    instance = None
    
    def __init__(self, port: int, multiworld: MultiWorld):
        API.instance = self
        self.port: int = port
        self.api: FastAPI = None
        self.multiworld: MultiWorld = multiworld
        self.state: dict[str, CurrentTrackerState] = {}
        
    async def launch(self):
        print(f"Launching Universal Tracker API on port {self.port}.")
        
        self.api = FastAPI()
        self.api.add_api_route("/slots", self.get_slots, methods=[ "GET" ])
        self.api.add_api_route("/slots/{slot}", self.get_slots_slot, methods=[ "GET" ])
        self.api.add_api_route("/slots/{slot}/locations", self.get_slots_slot_locations, methods=[ "GET" ])
        self.api.add_api_route("/slots/{slot}/locations/reachable", self.get_slots_slot_locations_reachable, methods=[ "GET" ])
        
        config = uvicorn.Config(self.api, host="0.0.0.0", port=self.port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()
    
    def get_slots(self):
        return self.multiworld.player_name
    
    def get_slots_slot(self, slot: str):
        return {
            "locations": len(self.get_slots_slot_locations(slot)),
            "reachable_locations": len(self.get_slots_slot_locations_reachable(slot))
        }
    
    def get_slots_slot_locations(self, slot: str):
        return [ location.name for location in self.multiworld.get_locations(self.multiworld.get_player_id(slot)) ]
    
    def get_slots_slot_locations_reachable(self, slot: str):
        return self.state[slot].in_logic_locations
        