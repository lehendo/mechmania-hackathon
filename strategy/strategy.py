import random
from game.base_strategy import BaseStrategy
from game.plane import Plane, PlaneType, Vector
import math
import strategy.utils as utils

# The following is the heart of your bot. This controls what your bot does.
# Feel free to change the behavior to your heart's content.
# You can also add other files under the strategy/ folder and import them

class Strategy(BaseStrategy):
    # BaseStrategy provides self.team, so you use self.team to see what team you are on

    # You can define whatever variables you want here
    my_counter = 0
    my_steers = dict()

    
    def select_planes(self) -> dict[PlaneType, int]:
        # Select which planes you want, and what number
        return {
            PlaneType.STANDARD: 0,
            PlaneType.FLYING_FORTRESS: 1,
            PlaneType.THUNDERBIRD: 3,
            PlaneType.SCRAPYARD_RESCUE: 0,
            PlaneType.PIGEON: 10
        }
    
    def steer_input(self, planes: dict[str, Plane]) -> dict[str, float]:
        response = dict()
        enemy_planes = []
        for id, plane in planes.items():
            if (plane.team != self.team):
                enemy_planes.append(plane)
        # Define a dictionary to hold our response
        #nearest plane to current plane

        response = dict()  
        # For each plane
        for id, plane in planes.items():
            # id is the unique id of the plane, plane is a Plane object
            # We can only control our own planes
            if plane.team != self.team:
                # Ignore any planes that aren't our own - continue
                continue
            nearest_plane = plane
            min2 = 100000
            for plane2 in enemy_planes:
                if (math.sqrt((plane2.position.x - plane.position.x)**2 + (plane2.position.y - plane.position.y)**2) < min2):
                    min2 = math.sqrt((plane2.position.x - plane.position.x)**2 + (plane2.position.y - plane.position.y)**2)
                    nearest_plane = plane2
            # If we're within the first 5 turns, just set the steer to 0
            #create tuple for plane direction vector
            '''
            vector_1 = Vector(math.cos(plane.angle), math.sin(plane.angle)) 
            x_diff = nearest_plane.position.x - plane.position.x
            y_diff = nearest_plane.position.y - plane.position.y
            vector_2 = Vector(x_diff, y_diff)  
            #gives us the angle between our plane and its current target
            target_angle = utils.angle_between_vectors(vector_1, vector_2)
            if x_diff < 0:
                self.my_steers[id] = -1 * target_angle/
            '''
            vector = Vector(nearest_plane.position.x, nearest_plane.position.y)
            
            x_diff = nearest_plane.position.x - plane.position.x
            a = utils.plane_find_path_to_point(vector,plane)
            response[id] = a[1] + a[0]
            if(response[id] < -1) :
                response[id] = -1
            if(response[id] > 1):
                response[id] = 1
        # Increment counter to keep track of what turn we're on
        self.my_counter += 1

        # Return the steers
        return response
