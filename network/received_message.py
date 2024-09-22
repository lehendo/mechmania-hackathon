from dataclasses import dataclass
from enum import Enum


class ReceivedMessagePhase(Enum):
    HELLO_WORLD = "HELLO_WORLD"
    PLANE_SELECT = "PLANE_SELECT"
    STEER_INPUT = "STEER_INPUT"
    FINISH = "FINISH"


@dataclass
class ReceivedMessage:
    phase: ReceivedMessagePhase
    data: object

    def deserialize(blob: object) -> "ReceivedMessage":
        try:
            message = ReceivedMessage(ReceivedMessagePhase[blob["phase"]], blob["data"])
        except:
            print("Failed to validate ReceivedMessage json")
            raise

        return message
