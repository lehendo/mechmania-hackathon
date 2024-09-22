import random
from game.base_strategy import BaseStrategy
from game.plane import Plane, PlaneType

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
            PlaneType.STANDARD: 1,
            PlaneType.FLYING_FORTRESS: 1,
            PlaneType.THUNDERBIRD: 1,
            PlaneType.SCRAPYARD_RESCUE: 1,
            PlaneType.PIGEON: 10,
        }
    
    def steer_input(self, planes: dict[str, Plane]) -> dict[str, float]:
        # Define a dictionary to hold our response
        response = dict()

        # For each plane
        for id, plane in planes.items():
            # id is the unique id of the plane, plane is a Plane object

            # We can only control our own planes
            if plane.team != self.team:
                # Ignore any planes that aren't our own - continue
                continue

            # If we're within the first 5 turns, just set the steer to 0
            if self.my_counter < 5:
                response[id] = 0
            else:
                # If we haven't initialized steers yet, generate a random one for this plane
                if id not in self.my_steers:
                    self.my_steers[id] = random.random() * 2 - 1

                # Set the steer for this plane to our previously decided steer
                response[id] = self.my_steers[id]

        # Increment counter to keep track of what turn we're on
        self.my_counter += 1

        # Return the steers
        return response
