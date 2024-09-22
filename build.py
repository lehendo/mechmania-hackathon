import zipapp
import os
import fnmatch

print("Building to build/bot.pyz...")

if not os.path.exists("build"):
    os.makedirs("build", exist_ok=True)

ignore_list = [
    ".git",
    ".git/*",
    "build",
    "build/*",
    "README.md",
    "build.py",
    "engine.py",
    "gamelogs",
    "gamelogs/*",
    "debuglog",
    "debuglog/*",
    "debuglogs",
    "debuglogs/*",
    "logs",
    "logs/*",
    "engine/",
    "engine/*"
]


def filter(path):
    for pattern in ignore_list:
        if fnmatch.fnmatch(path, pattern):
            return False
    return True


zipapp.create_archive(".", main="main:main", target="build/bot.pyz", filter=filter)
print("Done!")
