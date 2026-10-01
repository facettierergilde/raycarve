import os
import tomllib

with open(os.path.join(os.path.dirname(__file__), "blender_manifest.toml"), "rb") as f:
    ADDON_VERSION = tomllib.load(f)["version"]
