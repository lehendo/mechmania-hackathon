from fnmatch import fnmatch
from http.client import HTTPSConnection
import io
import json
from os import path
import os
import subprocess
import time
from urllib import request
import zipfile
import shutil

ENGINE_REPO = "MechMania-30/engine"
USER_AGENT = "MechMania-30"
GITHUB_TOKEN_ENV_NAME = "MECHMANIA_GITHUB_TOKEN"
ASSET_NAME_PREFIX = "engine-v"
GITHUB_RELEASE_CHECK_DELAY = 60
MIN_NPM_MAJOR_VERSION = 10
NODE_JS_DOWNLOAD_URL = "https://nodejs.org/en/download"
NPM_UPDATE_COMMAND = "npm install -g npm@latest"
ENGINE_DIR = "engine"
ENGINE_CONTENT_PATH = path.join(ENGINE_DIR, "content")
DATAFILE_NAME = "data.txt"
DATAFILE_PATH = path.join(ENGINE_DIR, DATAFILE_NAME)

def __get_current_data():
    if path.exists(DATAFILE_PATH):
        with open(DATAFILE_PATH) as file:
            data = file.read().strip()

            if data:
                data = data.split(";")

            return data

def __get_headers(is_download: bool = False):
    result = {
        "User-Agent": USER_AGENT,
    }
    if GITHUB_TOKEN_ENV_NAME in os.environ:
        result["Authorization"] = os.getenv(GITHUB_TOKEN_ENV_NAME)

    if is_download:
        result["Accept"] = "application/octet-stream"

    return result

def __get_latest_release_data():
    try:
        url = f"https://api.github.com/repos/{ENGINE_REPO}/releases/latest"
        req = request.Request(url, headers=__get_headers())

        with request.urlopen(req) as response:
            if response.status == 200:
                data = response.read().decode("utf-8")
                release_data = json.loads(data)

                return release_data
            else:
                print(f"`{url}` returned status code {response.status}")
                exit(1)
    except Exception as e:
        print(f"Error: Failed to connect GitHub API, {e}")
        exit(1)


def __download(url):
    if path.exists(ENGINE_CONTENT_PATH):
        shutil.rmtree(path.join(ENGINE_CONTENT_PATH))

    os.makedirs(ENGINE_CONTENT_PATH, exist_ok=True)

    print(f"Downloading engine from `{url}`...")

    try:
        req = request.Request(url, headers=__get_headers(True))
        with request.urlopen(req) as response:
            with io.BytesIO(response.read()) as zip_buffer:
                with zipfile.ZipFile(zip_buffer, "r") as zip_file:
                    zip_file.extractall(ENGINE_CONTENT_PATH)
    except Exception as e:
        print(f"Error downloading: {e}")
        exit(1)

    print("Saved to `engine/engine`")

def __install():
    print("Checking for npm installation...")
    check_npm = subprocess.run(
        "npm --version",
        shell=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if check_npm.returncode != 0:
        print(check_npm.stderr)
        print("Failed to check npm. Make sure you install node!\n" +
              f"You can update node here: {NODE_JS_DOWNLOAD_URL}\n" +
              f"And you can update npm by running: {NPM_UPDATE_COMMAND}")
        exit(1)

    version = check_npm.stdout.strip()
    print(f"Current installed NPM version: v{version}")
    major = int(version.split(".")[0])

    if major < MIN_NPM_MAJOR_VERSION:
        print("Your node/npm version is out of date! Please install the latest version!\n" +
              f"You can do so here: {NODE_JS_DOWNLOAD_URL}\n" +
              f"And you can update npm by running: {NPM_UPDATE_COMMAND}")
        exit(1)

    print("Is sufficiently up to date!")

    print("Installing node_modules (npm install)...")

    install = subprocess.run(
        "npm install",
        cwd=f"{ENGINE_CONTENT_PATH}",
        shell=True,
        text=True,
    )

    if install.returncode != 0:
        print("Failed to install")
        exit(1)

    print("Installed successfully!")


def __mark_checked(checked, version):
    if not path.exists(ENGINE_DIR):
        os.makedirs(ENGINE_DIR, exist_ok=True)

    with open(DATAFILE_PATH, "w") as file:
        file.write(f"{checked};{version}")


def update_if_not_latest():
    print("Checking for latest engine...")
    data = __get_current_data()

    last_checked = float(data[0]) if data else 0
    current_version = data[1] if data else None

    checked = time.time()
    if checked - last_checked < GITHUB_RELEASE_CHECK_DELAY:
        print("Already checked recently")
        return

    release = __get_latest_release_data()
    latest_version = release["tag_name"]

    if latest_version == current_version:
        __mark_checked(checked, latest_version)
        print("Latest engine already downloaded")
        return

    print(f"New engine is available ({current_version}->{latest_version})")

    asset = list(filter(lambda asset: asset["name"].startswith(ASSET_NAME_PREFIX), release["assets"]))[0]
    asset_url = asset["url"]

    if not path.exists(ENGINE_DIR):
        os.makedirs(ENGINE_DIR, exist_ok=True)

    __download(asset_url)
    __install()
    __mark_checked(checked, latest_version)


if __name__ == "__main__":
    update_if_not_latest()
