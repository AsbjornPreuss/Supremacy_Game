# SPDX-License-Identifier: BSD-3-Clause

import numpy as np

from supremacy import helpers


def tank_ai(tank, info, game_map):
    """
    Function to control tanks.
    """
    if not tank.stopped:
        if tank.stuck:
            tank.set_heading(np.random.random() * 360.0)
        elif "target" in info:
            tank.goto(*info["target"])


def ship_ai(ship, info, game_map):
    """
    Function to control ships.
    """
    keep_sailing = False
    if not ship.stopped:
        #print("Ship not stopped")
        if ship.stuck:
            print("Ship stuck")
            for base in info["bases"]:
                print("Checking Base", base.x,base.y)
                if ship.get_distance(base.x,base.y)<60:
                    print("Too close to home")
                    keep_sailing = True
                    break
        
                    
            
            
            #reverse and change angle
            if keep_sailing or info["t"]>0.5*400:
                ship.set_heading(((ship.heading+180)%360 + np.random.normal(loc=0,scale=15))%360)
            else:
                ship.convert_to_base()
      


def jet_ai(jet, info, game_map):
    """
    Function to control jets.
    """
    bases = info["enemy_bases"]
    for ind in range(len(bases)):
        if ind == 0:
            dist = jet.get_distance(bases[ind].x,bases[ind].y)
            target = 0
        else:
            if jet.get_distance(bases[ind].x,bases[ind].y) < dist:
                dist = jet.get_distance(bases[ind].x,bases[ind].y)
                target = ind

    if "target" in info:
        jet.goto(bases[target].x, bases[target].y)


class PlayerAi:
    """
    This is the AI bot that will be instantiated for the competition.
    """

    def __init__(self, name):
        self.team = name
        self.build_queue_start = helpers.BuildQueue(
            ["mine", "tank", "ship"],  cycle=True
        )
        self.build_queue_settler = helpers.BuildQueue(
            ["tank", "mine", "ship"],  cycle=True
        )
        self.build_queue_warrior = helpers.BuildQueue(
            ["jet", "mine"],  cycle=True
        )
        self.build_queue_sailor = helpers.BuildQueue(
            ["ship"],  cycle=True
        )
        self.bases_status = {}
        self.enemies = []
        


    def run(self, t: float, dt: float, info: dict, game_map: np.ndarray):
        """
        This is the main function that will be called by the game engine.
        """

        # Get information about my team
        myinfo = info[self.team]
        myinfo["t"] = t

        # Iterate through all my bases and process build queue
        for base in myinfo["bases"]:
            if (len(myinfo["bases"]) < 2) and (np.random.random()<.25):
                obj = self.build_queue_sailor(base)
                continue

            # Create status for new objects in dict
            self.bases_status[base.uid] =  self.bases_status.get(base.uid, "start")

            # Calling the build_queue will return the object that was built by the base.
            # It will return None if the base did not have enough resources to build.
            if self.bases_status[base.uid] == "start":
                obj = self.build_queue_start(base)
                if obj is not None:
                    if obj.kind == "ship":
                        print("Time to explore")
                        self.bases_status[base.uid] = "settler"

            elif self.bases_status[base.uid] == "settler":
                obj = self.build_queue_settler(base)
                if np.random.random() < (t)/400:
                    print("Time for war")
                    self.bases_status[base.uid] = "warrior"

            elif self.bases_status[base.uid] == "warrior":
                if np.random.random() < 0.1:
                    obj = self.build_queue_sailor(base)
                else:
                    obj = self.build_queue_warrior(base)
                    


        # Try to find an enemy target
        # If there are multiple teams in the info, find the first team that is not mine
        if len(info) > 1:
            self.enemies = []
            mindist = 1e9
            for name in info:
                if name != self.team:
                    # Target only bases
                    if "bases" in info[name]:
                        # Simply target the first base
                        self.enemies += info[name]["bases"]
                
        myinfo["enemy_bases"] = self.enemies
        # Control all my vehicles
        helpers.control_vehicles(
            info=myinfo, game_map=game_map, tank=tank_ai, ship=ship_ai, jet=jet_ai
        )
