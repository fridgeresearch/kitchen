"""
The MIT License (MIT)

Copyright (c) 2016 Jake Lussier (Stanford University)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import sys, numpy as np
from os.path import *

# ------------ DIRECTORIES AND FILES ----------------
# Kitchen
KITCHEN_DIR = dirname(dirname(abspath(__file__)))
PARENT_DIR = dirname(KITCHEN_DIR)
# - Data
DATA = join(PARENT_DIR, "data")
# - allrecipes data
ALLRECIPES_DATA = join(DATA, "allrecipes")
# - allrecipes dict
ALLRECIPES_DICT = join(DATA, "allrecipes.json")
# - ideorecipes dict
IDEORECIPES_DICT = join(DATA, "ideorecipes.json")
# - Bin
BIN_DIR = join(KITCHEN_DIR, "bin")
# - Config
CONFIG_DIR = join(KITCHEN_DIR, "config")
# -- Search ingredients.
SEARCH_INGREDIENTS = join(CONFIG_DIR, "ingredients.txt")
# -- Fridge configuration without markers
FRIDGE_NO_MARKERS_CONFIG = join(CONFIG_DIR, "fridge_no_markers.json")
# -- Fridge configuration with markers
FRIDGE_FULL_CONFIG = join(CONFIG_DIR, "fridge_full.json")
# -- Fridge storage configuration
FRIDGE_STORAGE_CONFIG = join(CONFIG_DIR, "fridge_storage.json")
# -- Markers stem (for tex and pdf files)
MARKERS_STEM = join(CONFIG_DIR, "markers")
# -- Scales configuration
SCALES_CONFIG = join(CONFIG_DIR, "scales.json")
SCALES_CONFIG_DATA = join(CONFIG_DIR, "scales_data")
# -- API configuration
API_CONFIG = join(CONFIG_DIR, "api.json")
# -- BLE configuration
BLE_CONFIG = join(CONFIG_DIR, "ble.json")
# -- Database configuration
DB_CONFIG = join(CONFIG_DIR, "db.json")
# -- Processing configuration
PROCESSING_CONFIG = join(CONFIG_DIR, "processing.json")
# -- Debug configuration
DEBUG_CONFIG = join(CONFIG_DIR, "debug.json")
# -- HTTP respones
HTTP_RESPONSES_CONFIG = join(CONFIG_DIR, "http_responses.json")
# -- Safeway configuration
SAFEWAY_CONFIG = join(CONFIG_DIR, "safeway.json")
# - Calibration
CALIBRATION_DIR = join(KITCHEN_DIR, "calibration")
# -- Scales calibration
SCALES_CALIBRATION_DIR = join(CALIBRATION_DIR, "scales")
SCALES_CALIBRATION_DATA = join(SCALES_CALIBRATION_DIR, "data")
SCALES_MODELS = join(SCALES_CALIBRATION_DIR, "models")
# -- Extrinsics calibration
EXTRINSICS_DIR = join(CALIBRATION_DIR, "extrinsics")
EXTRINSICS_RECORDING = join(EXTRINSICS_DIR, "recording")
EXTRINSICS_MODEL = join(EXTRINSICS_DIR, "model.pkl")
# -- Cameras calibration
CAMERAS_CALIBRATION_DIR = join(CALIBRATION_DIR, "cameras")
CAMERAS_CALIBRATION_DATA = join(CAMERAS_CALIBRATION_DIR, "data")
CAMERAS_MODEL = np.load(join(CAMERAS_CALIBRATION_DIR, "model.npz"))
CAMERA_CMAT = CAMERAS_MODEL["camera_matrix"]
CAMERA_DCOEFFS = CAMERAS_MODEL["distortion"]

# ------------ CONSTANTS ----------------
AUDIO_CHUNK = 10*1024
MAX_STABLE_FORCE = 20.0
