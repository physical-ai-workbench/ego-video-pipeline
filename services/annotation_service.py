from datetime import datetime
import json

import pandas as pd

from pathlib import Path

from config import (
    VIDEOS_CSV,
    EPISODES_CSV,
    ACTIONS_CSV,
    JSON_PATH,
    TASK_TYPE,
    RAW_DIR,
    PROCESSED_DIR,
    CLIP_DIR,
)

from services.video_service import (
    delete_episode_clip,
    find_processed_videos,
    probe_video,
    extract_video_summary,
)



VIDEO_COLUMNS = [
    "video_id",
    "original_filename",
    "task_type",
    "duration",
    "width",
    "height",
    "fps",
    "codec",
    "created_at",
]


EPISODE_COLUMNS = [
    "video_id",
    "episode_id",
    "start_time",
    "end_time",
    "duration",
    "object",
    "description",
    "created_at",
    "updated_at",
]


ACTION_COLUMNS = [
    "video_id",
    "episode_id",
    "action_id",
    "start_time",
    "end_time",
    "duration",
    "action",
    "object",
    "hand",
    "description",
    "created_at",
    "updated_at",
]


# ============================================================
# GENERIC CSV
# ============================================================

def _load_csv(
    path,
    columns,
):
    if not path.exists():
        return pd.DataFrame(
            columns=columns
        )

    df = pd.read_csv(path)

    for column in columns:

        if column not in df.columns:
            df[column] = None

    return df[columns]


def load_videos():
    df = _load_csv(
        VIDEOS_CSV,
        VIDEO_COLUMNS,
    )

    if df.empty:
        return df

    df["task_type"] = (
        df["task_type"]
        .fillna(TASK_TYPE)
        .replace("", TASK_TYPE)
    )

    return df

def sync_video_registry():
    """
    data/processed에 실제 존재하는 영상과
    annotations/videos.csv를 동기화합니다.

    예전 버전에서 생성한 영상이 videos.csv에 없어도
    앱 재실행 시 자동으로 복원됩니다.
    """

    videos = load_videos()

    changed = False

    processed_videos = (
        find_processed_videos()
    )

    known_ids = set(
        videos["video_id"].astype(str)
    )

    for video_path in processed_videos:

        video_id = video_path.stem

        # 이미 Registry에 존재
        if video_id in known_ids:

            mask = (
                videos["video_id"]
                .astype(str)
                == video_id
            )

            # 예전 데이터 task_type 보정
            current_task = (
                videos.loc[
                    mask,
                    "task_type",
                ]
                .iloc[0]
            )

            if (
                pd.isna(current_task)
                or current_task == ""
            ):
                videos.loc[
                    mask,
                    "task_type",
                ] = TASK_TYPE

                changed = True

            continue

        # ====================================================
        # Registry에 없는 기존 영상 발견
        # ====================================================

        try:
            metadata = probe_video(
                video_path
            )

            summary = (
                extract_video_summary(
                    metadata
                )
            )

        except Exception:
            # 영상이 손상됐거나 probe 실패 시
            # 해당 영상만 Skip
            continue

        # 원본 파일 이름 찾기
        original_filename = (
            video_path.name
        )

        raw_matches = list(
            RAW_DIR.glob(
                f"{video_id}.*"
            )
        )

        if raw_matches:
            original_filename = (
                raw_matches[0].name
            )

        record = {
            "video_id":
                video_id,

            "original_filename":
                original_filename,

            "task_type":
                TASK_TYPE,

            "duration":
                summary["duration"],

            "width":
                summary["width"],

            "height":
                summary["height"],

            "fps":
                summary["fps"],

            "codec":
                summary["codec"],

            "created_at":
                datetime.now()
                .isoformat(),
        }

        videos = pd.concat(
            [
                videos,
                pd.DataFrame(
                    [record]
                ),
            ],
            ignore_index=True,
        )

        known_ids.add(
            video_id
        )

        changed = True

    if changed:
        save_videos(
            videos
        )

def load_episodes():
    return _load_csv(
        EPISODES_CSV,
        EPISODE_COLUMNS,
    )


def load_actions():
    return _load_csv(
        ACTIONS_CSV,
        ACTION_COLUMNS,
    )


def save_videos(df):
    df.to_csv(
        VIDEOS_CSV,
        index=False,
        encoding="utf-8-sig",
    )


def save_episodes(df):
    df.to_csv(
        EPISODES_CSV,
        index=False,
        encoding="utf-8-sig",
    )


def save_actions(df):
    df.to_csv(
        ACTIONS_CSV,
        index=False,
        encoding="utf-8-sig",
    )


# ============================================================
# VIDEO
# ============================================================

def register_video(
    video_id,
    original_filename,
    summary,
):
    videos = load_videos()

    exists = (
        videos["video_id"]
        .eq(video_id)
        .any()
    )

    if exists:
        return

    record = {
        "video_id":
            video_id,

        "original_filename":
            original_filename,

        "task_type":
            TASK_TYPE,

        "duration":
            summary["duration"],

        "width":
            summary["width"],

        "height":
            summary["height"],

        "fps":
            summary["fps"],

        "codec":
            summary["codec"],

        "created_at":
            datetime.now()
            .isoformat(),
    }

    videos = pd.concat(
        [
            videos,
            pd.DataFrame(
                [record]
            ),
        ],
        ignore_index=True,
    )

    save_videos(videos)


def get_video(video_id):
    videos = load_videos()

    rows = videos[
        videos["video_id"]
        == video_id
    ]

    if rows.empty:
        return None

    return rows.iloc[0]


def delete_video(
    video_id,
):
    """
    Video 삭제 시 관련된 모든 데이터를 함께 삭제합니다.

    - videos.csv
    - episodes.csv
    - actions.csv
    - raw video
    - processed video
    - episode clips
    - annotations.json rebuild
    """

    videos = load_videos()
    episodes = load_episodes()
    actions = load_actions()

    # ========================================================
    # CSV DATA
    # ========================================================

    videos = videos[
        videos["video_id"]
        != video_id
    ].copy()

    episodes = episodes[
        episodes["video_id"]
        != video_id
    ].copy()

    actions = actions[
        actions["video_id"]
        != video_id
    ].copy()

    save_videos(
        videos
    )

    save_episodes(
        episodes
    )

    save_actions(
        actions
    )

    # ========================================================
    # RAW VIDEO
    # ========================================================

    for path in RAW_DIR.glob(
        f"{video_id}.*"
    ):
        if path.is_file():
            path.unlink()

    # ========================================================
    # PROCESSED VIDEO
    # ========================================================

    for path in PROCESSED_DIR.glob(
        f"{video_id}.*"
    ):
        if path.is_file():
            path.unlink()

    # ========================================================
    # EPISODE CLIPS
    # ========================================================

    for path in CLIP_DIR.glob(
        f"{video_id}_*"
    ):
        if path.is_file():
            path.unlink()

    # ========================================================
    # JSON
    # ========================================================

    rebuild_json()

# ============================================================
# IDs
# ============================================================

def next_episode_id(
    video_id,
):
    episodes = load_episodes()

    rows = episodes[
        episodes["video_id"]
        == video_id
    ]

    numbers = []

    for value in rows[
        "episode_id"
    ]:

        try:
            numbers.append(
                int(
                    str(value)
                    .split("_")[-1]
                )
            )

        except ValueError:
            pass

    number = (
        max(numbers, default=0)
        + 1
    )

    return f"ep_{number:03d}"


def next_action_id(
    video_id,
    episode_id,
):
    actions = load_actions()

    rows = actions[
        (
            actions["video_id"]
            == video_id
        )
        &
        (
            actions["episode_id"]
            == episode_id
        )
    ]

    numbers = []

    for value in rows[
        "action_id"
    ]:

        try:
            numbers.append(
                int(
                    str(value)
                    .split("_")[-1]
                )
            )

        except ValueError:
            pass

    number = (
        max(numbers, default=0)
        + 1
    )

    return f"act_{number:03d}"


# ============================================================
# EPISODE
# ============================================================

def create_episode(
    video_id,
    start_time,
    end_time,
    object_name,
    description,
):
    episodes = load_episodes()

    episode_id = (
        next_episode_id(
            video_id
        )
    )

    now = (
        datetime.now()
        .isoformat()
    )

    record = {
        "video_id":
            video_id,

        "episode_id":
            episode_id,

        "start_time":
            round(
                float(start_time),
                3,
            ),

        "end_time":
            round(
                float(end_time),
                3,
            ),

        "duration":
            round(
                float(end_time)
                - float(start_time),
                3,
            ),

        "object":
            object_name,

        "description":
            description,

        "created_at":
            now,

        "updated_at":
            now,
    }

    episodes = pd.concat(
        [
            episodes,
            pd.DataFrame(
                [record]
            ),
        ],
        ignore_index=True,
    )

    save_episodes(
        episodes
    )

    rebuild_json()

    return episode_id


def update_episode(
    video_id,
    episode_id,
    start_time,
    end_time,
    object_name,
    description,
):
    """
    기존 Action이 새 Episode 범위 밖으로 나가면
    Episode 수정 자체를 막는다.
    """

    actions = get_episode_actions(
        video_id,
        episode_id,
    )

    if not actions.empty:

        outside = actions[
            (
                actions["start_time"]
                < float(start_time)
            )
            |
            (
                actions["end_time"]
                > float(end_time)
            )
        ]

        if not outside.empty:
            raise ValueError(
                "새 Episode 범위를 벗어나는 "
                "Action이 있습니다. "
                "Action을 먼저 수정해 주세요."
            )

    episodes = load_episodes()

    mask = (
        (
            episodes["video_id"]
            == video_id
        )
        &
        (
            episodes["episode_id"]
            == episode_id
        )
    )

    episodes.loc[
        mask,
        "start_time",
    ] = round(
        float(start_time),
        3,
    )

    episodes.loc[
        mask,
        "end_time",
    ] = round(
        float(end_time),
        3,
    )

    episodes.loc[
        mask,
        "duration",
    ] = round(
        float(end_time)
        - float(start_time),
        3,
    )

    episodes.loc[
        mask,
        "object",
    ] = object_name

    episodes.loc[
        mask,
        "description",
    ] = description

    episodes.loc[
        mask,
        "updated_at",
    ] = (
        datetime.now()
        .isoformat()
    )

    save_episodes(
        episodes
    )

    rebuild_json()


def delete_episode(
    video_id,
    episode_id,
):
    episodes = load_episodes()
    actions = load_actions()

    episodes = episodes[
        ~(
            (
                episodes["video_id"]
                == video_id
            )
            &
            (
                episodes["episode_id"]
                == episode_id
            )
        )
    ]

    actions = actions[
        ~(
            (
                actions["video_id"]
                == video_id
            )
            &
            (
                actions["episode_id"]
                == episode_id
            )
        )
    ]

    save_episodes(
        episodes
    )

    save_actions(
        actions
    )

    delete_episode_clip(
        video_id,
        episode_id,
    )

    rebuild_json()


def get_video_episodes(
    video_id,
):
    episodes = load_episodes()

    rows = episodes[
        episodes["video_id"]
        == video_id
    ].copy()

    if not rows.empty:
        rows = rows.sort_values(
            "start_time"
        )

    return rows


def get_episode(
    video_id,
    episode_id,
):
    episodes = load_episodes()

    rows = episodes[
        (
            episodes["video_id"]
            == video_id
        )
        &
        (
            episodes["episode_id"]
            == episode_id
        )
    ]

    if rows.empty:
        return None

    return rows.iloc[0]


# ============================================================
# ACTION
# ============================================================

def get_episode_actions(
    video_id,
    episode_id,
):
    actions = load_actions()

    rows = actions[
        (
            actions["video_id"]
            == video_id
        )
        &
        (
            actions["episode_id"]
            == episode_id
        )
    ].copy()

    if not rows.empty:
        rows = rows.sort_values(
            "start_time"
        )

    return rows


def _validate_action_overlap(
    video_id,
    episode_id,
    start_time,
    end_time,
    exclude_action_id=None,
):
    actions = get_episode_actions(
        video_id,
        episode_id,
    )

    if exclude_action_id:
        actions = actions[
            actions["action_id"]
            != exclude_action_id
        ]

    for _, action in actions.iterrows():

        existing_start = float(
            action["start_time"]
        )

        existing_end = float(
            action["end_time"]
        )

        overlaps = (
            float(start_time)
            < existing_end
            and
            float(end_time)
            > existing_start
        )

        if overlaps:
            raise ValueError(
                f"{action['action_id']} "
                f"구간과 겹칩니다."
            )


def create_action(
    video_id,
    episode_id,
    start_time,
    end_time,
    action_label,
    object_name,
    hand,
    description,
):
    episode = get_episode(
        video_id,
        episode_id,
    )

    if episode is None:
        raise ValueError(
            "Episode을 찾을 수 없습니다."
        )

    if (
        float(start_time)
        < float(
            episode["start_time"]
        )
        or
        float(end_time)
        > float(
            episode["end_time"]
        )
    ):
        raise ValueError(
            "Action은 Episode 범위 "
            "내부에 있어야 합니다."
        )

    _validate_action_overlap(
        video_id,
        episode_id,
        start_time,
        end_time,
    )

    actions = load_actions()

    action_id = next_action_id(
        video_id,
        episode_id,
    )

    now = (
        datetime.now()
        .isoformat()
    )

    record = {
        "video_id":
            video_id,

        "episode_id":
            episode_id,

        "action_id":
            action_id,

        "start_time":
            round(
                float(start_time),
                3,
            ),

        "end_time":
            round(
                float(end_time),
                3,
            ),

        "duration":
            round(
                float(end_time)
                - float(start_time),
                3,
            ),

        "action":
            action_label,

        "object":
            object_name,

        "hand":
            hand,

        "description":
            description,

        "created_at":
            now,

        "updated_at":
            now,
    }

    actions = pd.concat(
        [
            actions,
            pd.DataFrame(
                [record]
            ),
        ],
        ignore_index=True,
    )

    save_actions(
        actions
    )

    rebuild_json()

    return action_id


def update_action(
    video_id,
    episode_id,
    action_id,
    start_time,
    end_time,
    action_label,
    object_name,
    hand,
    description,
):
    episode = get_episode(
        video_id,
        episode_id,
    )

    if (
        float(start_time)
        < float(
            episode["start_time"]
        )
        or
        float(end_time)
        > float(
            episode["end_time"]
        )
    ):
        raise ValueError(
            "Action은 Episode 범위 "
            "내부에 있어야 합니다."
        )

    _validate_action_overlap(
        video_id,
        episode_id,
        start_time,
        end_time,
        exclude_action_id=action_id,
    )

    actions = load_actions()

    mask = (
        (
            actions["video_id"]
            == video_id
        )
        &
        (
            actions["episode_id"]
            == episode_id
        )
        &
        (
            actions["action_id"]
            == action_id
        )
    )

    actions.loc[
        mask,
        "start_time",
    ] = round(
        float(start_time),
        3,
    )

    actions.loc[
        mask,
        "end_time",
    ] = round(
        float(end_time),
        3,
    )

    actions.loc[
        mask,
        "duration",
    ] = round(
        float(end_time)
        - float(start_time),
        3,
    )

    actions.loc[
        mask,
        "action",
    ] = action_label

    actions.loc[
        mask,
        "object",
    ] = object_name

    actions.loc[
        mask,
        "hand",
    ] = hand

    actions.loc[
        mask,
        "description",
    ] = description

    actions.loc[
        mask,
        "updated_at",
    ] = (
        datetime.now()
        .isoformat()
    )

    save_actions(
        actions
    )

    rebuild_json()


def delete_action(
    video_id,
    episode_id,
    action_id,
):
    actions = load_actions()

    actions = actions[
        ~(
            (
                actions["video_id"]
                == video_id
            )
            &
            (
                actions["episode_id"]
                == episode_id
            )
            &
            (
                actions["action_id"]
                == action_id
            )
        )
    ]

    save_actions(
        actions
    )

    rebuild_json()


# ============================================================
# JSON
# ============================================================

def rebuild_json():
    videos = load_videos()
    episodes = load_episodes()
    actions = load_actions()

    dataset = []

    for _, video in videos.iterrows():

        video_episodes = episodes[
            episodes["video_id"]
            == video["video_id"]
        ].sort_values(
            "start_time"
        )

        episode_list = []

        for _, episode in (
            video_episodes.iterrows()
        ):

            episode_actions = actions[
                (
                    actions["video_id"]
                    == video["video_id"]
                )
                &
                (
                    actions["episode_id"]
                    == episode["episode_id"]
                )
            ].sort_values(
                "start_time"
            )

            action_list = []

            for _, action in (
                episode_actions.iterrows()
            ):

                action_list.append(
                    {
                        "action_id":
                            action[
                                "action_id"
                            ],

                        "start_time":
                            float(
                                action[
                                    "start_time"
                                ]
                            ),

                        "end_time":
                            float(
                                action[
                                    "end_time"
                                ]
                            ),

                        "action":
                            action[
                                "action"
                            ],

                        "object":
                            action[
                                "object"
                            ],

                        "hand":
                            action[
                                "hand"
                            ],
                    }
                )

            episode_list.append(
                {
                    "episode_id":
                        episode[
                            "episode_id"
                        ],

                    "start_time":
                        float(
                            episode[
                                "start_time"
                            ]
                        ),

                    "end_time":
                        float(
                            episode[
                                "end_time"
                            ]
                        ),

                    "object":
                        episode[
                            "object"
                        ],

                    "actions":
                        action_list,
                }
            )

        dataset.append(
            {
                "video_id":
                    video[
                        "video_id"
                    ],

                "task_type":
                    video[
                        "task_type"
                    ],

                "episodes":
                    episode_list,
            }
        )

    with open(
        JSON_PATH,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            dataset,
            f,
            ensure_ascii=False,
            indent=2,
        )