from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"

RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
CLIP_DIR = DATA_DIR / "clips"

ANNOTATION_DIR = BASE_DIR / "annotations"

VIDEOS_CSV = ANNOTATION_DIR / "videos.csv"
EPISODES_CSV = ANNOTATION_DIR / "episodes.csv"
ACTIONS_CSV = ANNOTATION_DIR / "actions.csv"
JSON_PATH = ANNOTATION_DIR / "annotations.json"


for directory in [
    RAW_DIR,
    PROCESSED_DIR,
    CLIP_DIR,
    ANNOTATION_DIR,
]:
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )


# ============================================================
# CURRENT PROJECT SCOPE
# ============================================================

TASK_TYPE = "pick_and_place"

TASK_DISPLAY_NAME = "Pick & Place"


# Processed video = 30 FPS
FPS = 30.0
FRAME_STEP = 1.0 / FPS


# ============================================================
# LABELS
# ============================================================

ACTION_OPTIONS = [
    "pick",
    "move",
    "place",
]

HAND_OPTIONS = [
    "right",
    "left",
    "both",
    "none",
]


# Object는 아직 다양한 샘플 영상을 고려해 유지
OBJECT_OPTIONS = [
    "component",
    "cup",
    "bottle",
    "box",
    "tool",
    "bolt",
    "nut",
    "container",
    "other",
]