import argparse
from datetime import datetime
from enum import Enum
import json
import os
from queue import Queue, Empty
import subprocess
import threading
import time
import traceback
import sys
from typing import IO
import time

from game.plane import Plane

try:
    import engine
except:
    pass

from network.client import Client
from network.received_message import ReceivedMessage, ReceivedMessagePhase
from strategy.strategy import Strategy

raw_debug_env = os.environ.get("DEBUG")
DEBUG = raw_debug_env == "1" or raw_debug_env == "true"


# A argument parser that will also print help upon error
class HelpArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write("error: %s\n" % message)
        self.print_help()
        sys.exit(2)


class RunOpponent(Enum):
    SELF = "self"
    COMPUTER_TEAM_0 = "computerTeam0"
    COMPUTER_TEAM_1 = "computerTeam1"

RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = "\033[93m"
BLUE = '\033[94m'
RESET = '\033[0m'

COMMANDS_FOR_OPPONENT: dict[RunOpponent, list[tuple[str, str]]] = {
    RunOpponent.SELF: [
        ("Engine", "npm start 3001 3002", YELLOW),
        ("Team 0", "python main.py serve 3001", GREEN),
        ("Team 1", "python main.py serve 3002", BLUE),
    ],
    RunOpponent.COMPUTER_TEAM_0: [
        ("Engine", "npm start 0 9001", YELLOW),
        ("Team 1", "python main.py serve 9001", BLUE),
    ],
    RunOpponent.COMPUTER_TEAM_1: [
        ("Engine", "npm start 9001 0", YELLOW),
        ("Team 0", "python main.py serve 9001", GREEN),
    ],
}

def determine_python():
    try:
        subprocess.run("python3 --version", shell=True, check=True, capture_output=True, text=True)
        return "python3"
    except subprocess.CalledProcessError:
        pass
    except FileNotFoundError:
        pass

    # If python3 fails, try python
    try:
        subprocess.run("python --version", shell=True, check=True, capture_output=True, text=True)
        return "python"
    except subprocess.CalledProcessError:
        pass
    except FileNotFoundError:
        pass

    return None


def run(opponent: RunOpponent):
    if engine:
        engine.update_if_not_latest()

    python = determine_python()

    if not python:
        print("Failed to find python in shell")
        exit(1)

    print(
        f"Running against opponent {opponent.value}... (might take a minute, please wait)"
    )

    info = COMMANDS_FOR_OPPONENT[opponent]
    prefixes = list(map(lambda x: x[0], info))
    commands = list(map(lambda x: x[1], info))
    colors = list(map(lambda x: x[2], info))

    now = datetime.now()
    formatted_now = now.strftime("%Y_%m_%d__%H_%M_%S")
    gamelog_name = f"log_{formatted_now}"
    output_logs_dir = f"logs/{gamelog_name}/"
    gamelog_path = os.path.join(output_logs_dir, f"gamelog.json")

    new_env = os.environ.copy()
    # Set gamelog output location, needs to be relative to engine directory
    new_env["OUTPUT"] = os.path.join("../../", gamelog_path)
    # Do not buffer output
    new_env["PYTHONUNBUFFERED"] = "1"

    # Launch each command in a separate terminal
    processes: list[subprocess.Popen] = []
    for i, command in enumerate(commands):
        command = command.replace("python", python)
        process = subprocess.Popen(
            command,
            shell=True,
            cwd=f"engine/content" if i == 0 else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
            text=True,
            env=new_env,
        )
        processes.append(process)

        # Start the engine first, then wait to start everything else (mac requires engine to start first)
        if i == 0:
            time.sleep(1)

    queue = Queue()

    def run_and_output(io: IO, i: int, is_err: True):
        for line in iter(io.readline, ""):
            line: str
            queue.put((is_err, time.time_ns(), i, line.strip()))

    threads: list[threading.Thread] = []
    for i in range(len(processes) - 1, -1, -1):
        process = processes[i]

        thread_stdout = threading.Thread(
            target=run_and_output, args=(process.stdout, i, False)
        )
        thread_stderr = threading.Thread(
            target=run_and_output, args=(process.stderr, i, True)
        )
        thread_stdout.start()
        thread_stderr.start()
        threads.append(thread_stdout)
        threads.append(thread_stderr)

    outputs = []

    while all(t.is_alive() for t in threads):
        try:
            item = queue.get(timeout=0.1)
            outputs.append(item)
            is_err, timestamp, i, line = item
            prefix = prefixes[i]
            color = colors[i] if not is_err else RED
            print(f"{color}[{prefix}] {line}{RESET}", flush=True, file=sys.stderr if is_err else sys.stdout)
        except Empty:
            pass

    for thread in threads:
        thread.join()

    outputs.sort(key=lambda x: x[1])

    files = []

    if not os.path.exists(output_logs_dir):
        os.makedirs(output_logs_dir, exist_ok=True)

    for i in range(len(processes)):
        filename = f"{output_logs_dir}{prefixes[i].replace(' ', '_').lower()}.txt"
        files.append(filename)
        output = list(map(lambda x: x[3], filter(lambda x: x[2] == i, outputs)))

        with open(filename, "w") as file:
            file.write("\n".join(output))

    print(
        "\nNote that output above may not be in the exact order it was output, due to terminal limitations.\n"
        + f"For separated ordered output, see: {', '.join(files)}"
    )
    print(f"For the gamelog, see: {gamelog_path}")


def serve(port: int):
    print(f"Connecting to server on port {port}...")

    client = Client(port)

    client.connect()

    print(f"Connected to server on port {port}")

    strategy = None

    while True:
        raw_received = client.read()

        if raw_received:
            try:
                received = json.loads(raw_received)
                received_message = ReceivedMessage.deserialize(received)
                phase = received_message.phase
                data = received_message.data

                if strategy is None and phase != ReceivedMessagePhase.HELLO_WORLD:
                    raise RuntimeError("Invalid local state, no hello world sent!")

                if phase == ReceivedMessagePhase.HELLO_WORLD:
                    our_team = data["team"]
                    strategy = Strategy(our_team)

                    client.write(json.dumps({
                        "good": True,
                    }))
                elif phase == ReceivedMessagePhase.PLANE_SELECT:
                    response = strategy.select_planes()

                    serialized_response = dict()

                    for type, count in response.items():
                        serialized_response[type.value] = count

                    response_str = json.dumps(serialized_response)

                    client.write(response_str)
                elif phase == ReceivedMessagePhase.STEER_INPUT:
                    planes = dict()

                    for id, blob in data.items():
                        planes[id] = Plane.deserialize(blob)

                    response = strategy.steer_input(planes)
                    response_str = json.dumps(response)

                    client.write(response_str)
                elif phase == ReceivedMessagePhase.FINISH:
                    print(data)

                    break
                else:
                    raise RuntimeError(f"Unknown phase type {phase}")

                if DEBUG:
                    print(f"Sent response to {phase} phase to server!")

            except Exception as e:
                print(f"Something went wrong running your bot: {e}", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
                client.write("null")


def main():
    parser = HelpArgumentParser(description="MechMania 30 bot runner")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    serve_parser = subparsers.add_parser(
        "serve",
        help="Serves your bot to an engine on the port passed, requires engine to be running there",
    )
    serve_parser.add_argument("port", type=int, help="Port to connect to")

    run_parser = subparsers.add_parser("run", help="Run your bot against an opponent")
    run_parser.add_argument(
        "opponent",
        choices=list(map(lambda opponent: opponent.value, list(RunOpponent))),
        help="Opponent to put your bot against, where self is your own bot or computer is against a simple computer bot. " +
        "Computer can the top or bottom team.",
    )

    args = parser.parse_args()

    # Match to a valid command
    if args.command == "serve":
        return serve(args.port)
    elif args.command == "run":
        for opponent in list(RunOpponent):
            if opponent.value == args.opponent:
                return run(opponent)

    # If no valid command, print help
    parser.print_help()


if __name__ == "__main__":
    main()
