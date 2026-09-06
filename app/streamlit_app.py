from pathlib import Path
from datetime import datetime
import json
import shutil
import subprocess

import pandas as pd
import streamlit as st


# ============================================================
# PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
CLIP_DIR = BASE_DIR / "data" / "clips"
ANNOTATION_DIR = BASE_DIR / "annotations"

EPISODES_CSV = ANNOTATION_DIR / "episodes.csv"
ACTIONS_CSV = ANNOTATION_DIR / "actions.csv"
JSON_PATH = ANNOTATION_DIR / "annotations.json"

for directory in [
    RAW_DIR,
    PROCESSED_DIR,
    CLIP_DIR,
    ANNOTATION_DIR,
]:
    directory.mkdir(parents=True, exist_ok=True)


# ============================================================
# LABELS
# ============================================================

TASK_OPTIONS = [
    "pick_and_place",
    "install_component",
    "remove_component",
    "move_object",
    "open_container",
    "close_container",
    "inspect_object",
    "assemble",
    "disassemble",
    "other",
]

ACTION_OPTIONS = [
    "reach",
    "pick",
    "grasp",
    "move",
    "place",
    "insert",
    "remove",
    "tighten",
    "loosen",
    "open",
    "close",
    "push",
    "pull",
    "press",
    "release",
    "inspect",
    "other",
]

OBJECT_OPTIONS = [
    "bolt",
    "nut",
    "washer",
    "screw",
    "tool",
    "component",
    "box",
    "cup",
    "bottle",
    "container",
    "panel",
    "connector",
    "other",
]

HAND_OPTIONS = [
    "right",
    "left",
    "both",
    "none",
]


# ============================================================
# TABLE SCHEMA
# ============================================================

EPISODE_COLUMNS = [
    "video_id",
    "episode_id",
    "start_time",
    "end_time",
    "duration",
    "task",
    "object",
    "description",
    "annotator",
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
# DATA FUNCTIONS
# ============================================================

def empty_episode_df():
    return pd.DataFrame(columns=EPISODE_COLUMNS)


def empty_action_df():
    return pd.DataFrame(columns=ACTION_COLUMNS)


def load_episodes():
    if not EPISODES_CSV.exists():
        return empty_episode_df()

    return pd.read_csv(EPISODES_CSV)


def load_actions():
    if not ACTIONS_CSV.exists():
        return empty_action_df()

    return pd.read_csv(ACTIONS_CSV)


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
# VIDEO FUNCTIONS
# ============================================================

def find_processed_videos():
    return sorted(PROCESSED_DIR.glob("*.mp4"))


def generate_video_id():
    """
    기존 ego_001, ego_002 ... 를 확인해서
    다음 번호 생성.
    """

    numbers = []

    for path in list(RAW_DIR.iterdir()) + list(PROCESSED_DIR.iterdir()):
        if not path.is_file():
            continue

        stem = path.stem

        if not stem.startswith("ego_"):
            continue

        try:
            number = int(stem.split("_")[1])
            numbers.append(number)
        except (IndexError, ValueError):
            pass

    next_number = max(numbers, default=0) + 1

    return f"ego_{next_number:03d}"


def probe_video(video_path):
    """
    ffprobe를 이용해 영상 정보 조회.
    """

    command = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(video_path),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    return json.loads(result.stdout)


def extract_video_summary(metadata):
    """
    ffprobe 결과 중 UI에서 보기 좋은 정보만 추출.
    """

    video_stream = None

    for stream in metadata.get("streams", []):
        if stream.get("codec_type") == "video":
            video_stream = stream
            break

    if video_stream is None:
        return {}

    fps = video_stream.get("avg_frame_rate", "0/1")

    try:
        numerator, denominator = fps.split("/")
        fps_value = float(numerator) / float(denominator)
    except Exception:
        fps_value = 0

    duration = metadata.get(
        "format",
        {},
    ).get(
        "duration",
        0,
    )

    return {
        "width": video_stream.get("width"),
        "height": video_stream.get("height"),
        "codec": video_stream.get("codec_name"),
        "fps": round(fps_value, 2),
        "duration": round(float(duration), 2),
    }


def preprocess_video(raw_path, processed_path):
    """
    Annotation 작업용 표준 영상 생성.

    - 720p
    - 30fps
    - H.264
    - AAC
    """

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(raw_path),
        "-vf",
        "scale=-2:720,fps=30",
        "-c:v",
        "libx264",
        "-crf",
        "23",
        "-preset",
        "medium",
        "-c:a",
        "aac",
        "-movflags",
        "+faststart",
        str(processed_path),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)


def extract_episode_clip(
    video_path,
    video_id,
    episode_id,
    start_time,
    end_time,
):
    """
    지정한 Episode 구간을 정확하게 재인코딩하여 저장.
    """

    duration = float(end_time) - float(start_time)

    if duration <= 0:
        raise ValueError("End Time은 Start Time보다 커야 합니다.")

    output_dir = CLIP_DIR / video_id
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = (
        output_dir
        / f"{video_id}_{episode_id}.mp4"
    )

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-ss",
        f"{float(start_time):.3f}",
        "-t",
        f"{duration:.3f}",
        "-map",
        "0:v:0",
        "-map",
        "0:a?",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "20",
        "-c:a",
        "aac",
        "-movflags",
        "+faststart",
        str(output_path),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    return output_path


# ============================================================
# ID FUNCTIONS
# ============================================================

def next_episode_id(episodes_df, video_id):
    rows = episodes_df[
        episodes_df["video_id"] == video_id
    ]

    numbers = []

    for episode_id in rows["episode_id"]:
        try:
            numbers.append(
                int(str(episode_id).split("_")[-1])
            )
        except ValueError:
            pass

    return f"ep_{max(numbers, default=0) + 1:03d}"


def next_action_id(
    actions_df,
    video_id,
    episode_id,
):
    rows = actions_df[
        (actions_df["video_id"] == video_id)
        & (actions_df["episode_id"] == episode_id)
    ]

    numbers = []

    for action_id in rows["action_id"]:
        try:
            numbers.append(
                int(str(action_id).split("_")[-1])
            )
        except ValueError:
            pass

    return f"act_{max(numbers, default=0) + 1:03d}"


# ============================================================
# JSON
# ============================================================

def rebuild_json():
    episodes = load_episodes()
    actions = load_actions()

    result = []

    for _, episode in episodes.iterrows():

        action_rows = actions[
            (actions["video_id"] == episode["video_id"])
            & (
                actions["episode_id"]
                == episode["episode_id"]
            )
        ].sort_values("start_time")

        action_list = []

        for _, action in action_rows.iterrows():

            action_list.append(
                {
                    "action_id": action["action_id"],
                    "start_time": float(
                        action["start_time"]
                    ),
                    "end_time": float(
                        action["end_time"]
                    ),
                    "duration": float(
                        action["duration"]
                    ),
                    "action": action["action"],
                    "object": action["object"],
                    "hand": action["hand"],
                    "description": (
                        ""
                        if pd.isna(action["description"])
                        else action["description"]
                    ),
                }
            )

        result.append(
            {
                "video_id": episode["video_id"],
                "episode_id": episode["episode_id"],
                "start_time": float(
                    episode["start_time"]
                ),
                "end_time": float(
                    episode["end_time"]
                ),
                "duration": float(
                    episode["duration"]
                ),
                "task": episode["task"],
                "object": episode["object"],
                "description": (
                    ""
                    if pd.isna(episode["description"])
                    else episode["description"]
                ),
                "actions": action_list,
            }
        )

    with open(
        JSON_PATH,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            result,
            f,
            ensure_ascii=False,
            indent=2,
        )


# ============================================================
# DELETE
# ============================================================

def delete_episode(
    video_id,
    episode_id,
):
    episodes = load_episodes()
    actions = load_actions()

    episodes = episodes[
        ~(
            (episodes["video_id"] == video_id)
            & (
                episodes["episode_id"]
                == episode_id
            )
        )
    ]

    actions = actions[
        ~(
            (actions["video_id"] == video_id)
            & (
                actions["episode_id"]
                == episode_id
            )
        )
    ]

    save_episodes(episodes)
    save_actions(actions)

    clip_path = (
        CLIP_DIR
        / video_id
        / f"{video_id}_{episode_id}.mp4"
    )

    if clip_path.exists():
        clip_path.unlink()

    rebuild_json()


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="Ego Annotation Tool",
    page_icon="🎥",
    layout="wide",
)

st.title("🎥 Egocentric Video Annotation Tool")

st.caption(
    "Raw Video → Preprocessing → Episode → Action → Ground Truth"
)


# ============================================================
# GUIDE
# ============================================================

with st.expander("📘 Annotation Guide", expanded=False):

    st.markdown(
        """
### Episode

하나의 명확한 **작업 목적 단위**입니다.

예를 들어:

**컵을 집어서 지정된 위치에 내려놓는다**

이 전체가 하나의 Episode입니다.

`Task = pick_and_place`

---

### Action

Episode 안의 세부 동작입니다.

예:

`Pick → Move → Place`

따라서 하나의 Episode 안에 여러 Action이 들어갈 수 있습니다.

---

### Episode Start

작업 목적을 수행하기 위한 명확한 행동이 시작되는 시점.

### Episode End

작업 목적이 완료되고 해당 작업에서 벗어나는 시점.

---

### 예시

Episode:

`10.2 ~ 18.4 / pick_and_place / cup`

Actions:

- `10.2 ~ 12.1 / pick / cup`
- `12.1 ~ 16.0 / move / cup`
- `16.0 ~ 18.4 / place / cup`

---

### 원칙

- 같은 행동에는 같은 Label을 사용합니다.
- Action은 Episode 범위 안에 있어야 합니다.
- 판단이 애매하면 `other`를 사용합니다.
- Start / End 기준을 일관되게 적용합니다.
        """
    )


# ============================================================
# TAB
# ============================================================

upload_tab, annotation_tab, dataset_tab = st.tabs(
    [
        "① Video Upload & Preprocess",
        "② Annotation",
        "③ Dataset",
    ]
)


# ============================================================
# TAB 1 - UPLOAD
# ============================================================

with upload_tab:

    st.header("Video Upload")

    st.write(
        "원본 영상을 업로드하면 이름을 자동으로 부여하고 "
        "Annotation용 포맷으로 전처리합니다."
    )

    uploaded_file = st.file_uploader(
        "Egocentric Video",
        type=[
            "mp4",
            "mov",
            "m4v",
            "avi",
            "webm",
        ],
    )

    if uploaded_file is not None:

        st.write(
            f"원본 파일명: `{uploaded_file.name}`"
        )

        if st.button(
            "영상 등록 및 전처리",
            type="primary",
        ):

            video_id = generate_video_id()

            original_suffix = (
                Path(uploaded_file.name)
                .suffix
                .lower()
            )

            raw_path = (
                RAW_DIR
                / f"{video_id}{original_suffix}"
            )

            processed_path = (
                PROCESSED_DIR
                / f"{video_id}.mp4"
            )

            try:

                with st.status(
                    "영상 처리 중...",
                    expanded=True,
                ) as status:

                    st.write(
                        "1/4 원본 영상 저장"
                    )

                    with open(
                        raw_path,
                        "wb",
                    ) as f:
                        shutil.copyfileobj(
                            uploaded_file,
                            f,
                        )

                    st.write(
                        f"✓ `{video_id}` 이름 부여"
                    )

                    st.write(
                        "2/4 FFprobe 메타데이터 분석"
                    )

                    raw_metadata = probe_video(
                        raw_path
                    )

                    raw_summary = (
                        extract_video_summary(
                            raw_metadata
                        )
                    )

                    st.write(
                        "✓ 원본 영상 분석 완료"
                    )

                    st.write(
                        "3/4 FFmpeg 전처리"
                    )

                    st.code(
                        "720p / 30 FPS / H.264 / AAC"
                    )

                    preprocess_video(
                        raw_path,
                        processed_path,
                    )

                    st.write(
                        "✓ 전처리 완료"
                    )

                    st.write(
                        "4/4 Processed Video 검증"
                    )

                    processed_metadata = (
                        probe_video(
                            processed_path
                        )
                    )

                    processed_summary = (
                        extract_video_summary(
                            processed_metadata
                        )
                    )

                    st.write(
                        "✓ Annotation Video 등록 완료"
                    )

                    status.update(
                        label=(
                            f"{video_id} 등록 완료"
                        ),
                        state="complete",
                        expanded=True,
                    )

                st.success(
                    f"새 Video ID: {video_id}"
                )

                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("Original")

                    st.json(
                        raw_summary
                    )

                with col2:
                    st.subheader("Processed")

                    st.json(
                        processed_summary
                    )

                st.subheader(
                    "Processed Video Preview"
                )

                st.video(
                    str(processed_path)
                )

                st.info(
                    "이제 ② Annotation 탭으로 이동하면 "
                    "이 영상을 선택할 수 있습니다."
                )

            except Exception as e:

                st.error(
                    f"영상 처리 실패: {e}"
                )


# ============================================================
# TAB 2 - ANNOTATION
# ============================================================

with annotation_tab:

    videos = find_processed_videos()

    if not videos:

        st.warning(
            "아직 등록된 Processed Video가 없습니다."
        )

    else:

        video_map = {
            video.name: video
            for video in videos
        }

        selected_video_name = st.selectbox(
            "Video 선택",
            list(video_map.keys()),
        )

        video_path = video_map[
            selected_video_name
        ]

        video_id = video_path.stem

        st.video(
            str(video_path)
        )

        st.caption(
            f"현재 Video ID: {video_id}"
        )

        episodes = load_episodes()
        actions = load_actions()

        st.divider()

        # ====================================================
        # CREATE EPISODE
        # ====================================================

        st.header("Episode 생성")

        with st.form(
            f"create_episode_{video_id}"
        ):

            col1, col2 = st.columns(2)

            with col1:
                start_time = st.number_input(
                    "Episode Start (sec)",
                    min_value=0.0,
                    step=0.1,
                    format="%.3f",
                )

            with col2:
                end_time = st.number_input(
                    "Episode End (sec)",
                    min_value=0.0,
                    step=0.1,
                    format="%.3f",
                )

            col1, col2 = st.columns(2)

            with col1:
                task = st.selectbox(
                    "Task",
                    TASK_OPTIONS,
                )

            with col2:
                main_object = st.selectbox(
                    "Main Object",
                    OBJECT_OPTIONS,
                )

            episode_description = st.text_input(
                "Description",
                placeholder=(
                    "Pick up the cup and "
                    "place it on the table"
                ),
            )

            create_episode = (
                st.form_submit_button(
                    "Episode 생성",
                    type="primary",
                )
            )

        if create_episode:

            if end_time <= start_time:

                st.error(
                    "End Time은 Start Time보다 커야 합니다."
                )

            else:

                episodes = load_episodes()

                episode_id = next_episode_id(
                    episodes,
                    video_id,
                )

                now = datetime.now().isoformat()

                record = {
                    "video_id": video_id,
                    "episode_id": episode_id,
                    "start_time": round(
                        start_time,
                        3,
                    ),
                    "end_time": round(
                        end_time,
                        3,
                    ),
                    "duration": round(
                        end_time - start_time,
                        3,
                    ),
                    "task": task,
                    "object": main_object,
                    "description": (
                        episode_description
                    ),
                    "annotator": "human_01",
                    "created_at": now,
                    "updated_at": now,
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

                save_episodes(episodes)

                try:

                    extract_episode_clip(
                        video_path,
                        video_id,
                        episode_id,
                        start_time,
                        end_time,
                    )

                    rebuild_json()

                    st.success(
                        f"{episode_id} 생성 완료"
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"FFmpeg 오류: {e}"
                    )

        # ====================================================
        # EPISODE MANAGEMENT
        # ====================================================

        episodes = load_episodes()

        current_episodes = episodes[
            episodes["video_id"]
            == video_id
        ].copy()

        if not current_episodes.empty:

            current_episodes = (
                current_episodes
                .sort_values("start_time")
            )

            st.divider()

            st.header("Episode 관리")

            st.dataframe(
                current_episodes[
                    [
                        "episode_id",
                        "start_time",
                        "end_time",
                        "duration",
                        "task",
                        "object",
                        "description",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )

            selected_episode_id = (
                st.selectbox(
                    "Episode 선택",
                    current_episodes[
                        "episode_id"
                    ].tolist(),
                )
            )

            selected_episode = (
                current_episodes[
                    current_episodes[
                        "episode_id"
                    ]
                    == selected_episode_id
                ]
                .iloc[0]
            )

            clip_path = (
                CLIP_DIR
                / video_id
                / (
                    f"{video_id}_"
                    f"{selected_episode_id}.mp4"
                )
            )

            if clip_path.exists():

                st.subheader(
                    "Episode Preview"
                )

                st.video(
                    str(clip_path)
                )

            # ================================================
            # EDIT EPISODE
            # ================================================

            with st.expander(
                "✏️ Episode 수정"
            ):

                with st.form(
                    f"edit_episode_"
                    f"{selected_episode_id}"
                ):

                    col1, col2 = st.columns(2)

                    with col1:

                        edit_start = (
                            st.number_input(
                                "Start",
                                value=float(
                                    selected_episode[
                                        "start_time"
                                    ]
                                ),
                                step=0.1,
                                format="%.3f",
                            )
                        )

                    with col2:

                        edit_end = (
                            st.number_input(
                                "End",
                                value=float(
                                    selected_episode[
                                        "end_time"
                                    ]
                                ),
                                step=0.1,
                                format="%.3f",
                            )
                        )

                    task_index = (
                        TASK_OPTIONS.index(
                            selected_episode[
                                "task"
                            ]
                        )
                        if selected_episode[
                            "task"
                        ]
                        in TASK_OPTIONS
                        else 0
                    )

                    object_index = (
                        OBJECT_OPTIONS.index(
                            selected_episode[
                                "object"
                            ]
                        )
                        if selected_episode[
                            "object"
                        ]
                        in OBJECT_OPTIONS
                        else 0
                    )

                    edit_task = st.selectbox(
                        "Task",
                        TASK_OPTIONS,
                        index=task_index,
                    )

                    edit_object = st.selectbox(
                        "Object",
                        OBJECT_OPTIONS,
                        index=object_index,
                    )

                    original_description = (
                        selected_episode[
                            "description"
                        ]
                    )

                    if pd.isna(
                        original_description
                    ):
                        original_description = ""

                    edit_description = (
                        st.text_input(
                            "Description",
                            value=str(
                                original_description
                            ),
                        )
                    )

                    update_episode = (
                        st.form_submit_button(
                            "수정 저장"
                        )
                    )

                if update_episode:

                    if edit_end <= edit_start:

                        st.error(
                            "End는 Start보다 커야 합니다."
                        )

                    else:

                        episodes = load_episodes()

                        mask = (
                            (
                                episodes[
                                    "video_id"
                                ]
                                == video_id
                            )
                            & (
                                episodes[
                                    "episode_id"
                                ]
                                == selected_episode_id
                            )
                        )

                        episodes.loc[
                            mask,
                            "start_time",
                        ] = round(
                            edit_start,
                            3,
                        )

                        episodes.loc[
                            mask,
                            "end_time",
                        ] = round(
                            edit_end,
                            3,
                        )

                        episodes.loc[
                            mask,
                            "duration",
                        ] = round(
                            edit_end
                            - edit_start,
                            3,
                        )

                        episodes.loc[
                            mask,
                            "task",
                        ] = edit_task

                        episodes.loc[
                            mask,
                            "object",
                        ] = edit_object

                        episodes.loc[
                            mask,
                            "description",
                        ] = edit_description

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

                        extract_episode_clip(
                            video_path,
                            video_id,
                            selected_episode_id,
                            edit_start,
                            edit_end,
                        )

                        rebuild_json()

                        st.success(
                            "Episode 수정 완료"
                        )

                        st.rerun()

            # ================================================
            # DELETE EPISODE
            # ================================================

            with st.expander(
                "🗑️ Episode 삭제"
            ):

                st.warning(
                    "Episode를 삭제하면 "
                    "내부 Action과 Clip도 함께 삭제됩니다."
                )

                confirm_delete = (
                    st.checkbox(
                        "삭제 확인",
                        key=(
                            f"confirm_"
                            f"{selected_episode_id}"
                        ),
                    )
                )

                if st.button(
                    "Episode 삭제",
                    disabled=not confirm_delete,
                    key=(
                        f"delete_"
                        f"{selected_episode_id}"
                    ),
                ):

                    delete_episode(
                        video_id,
                        selected_episode_id,
                    )

                    st.success(
                        "Episode 삭제 완료"
                    )

                    st.rerun()

            # ================================================
            # ACTION
            # ================================================

            st.divider()

            st.header(
                "Action Annotation"
            )

            st.info(
                f"Episode Range: "
                f"{selected_episode['start_time']} "
                f"~ "
                f"{selected_episode['end_time']} sec"
            )

            with st.form(
                f"add_action_"
                f"{selected_episode_id}"
            ):

                col1, col2 = st.columns(2)

                with col1:

                    action_start = (
                        st.number_input(
                            "Action Start",
                            value=float(
                                selected_episode[
                                    "start_time"
                                ]
                            ),
                            step=0.1,
                            format="%.3f",
                        )
                    )

                with col2:

                    action_end = (
                        st.number_input(
                            "Action End",
                            value=float(
                                selected_episode[
                                    "end_time"
                                ]
                            ),
                            step=0.1,
                            format="%.3f",
                        )
                    )

                col1, col2, col3 = (
                    st.columns(3)
                )

                with col1:
                    action_label = (
                        st.selectbox(
                            "Action",
                            ACTION_OPTIONS,
                        )
                    )

                with col2:
                    action_object = (
                        st.selectbox(
                            "Object",
                            OBJECT_OPTIONS,
                        )
                    )

                with col3:
                    action_hand = (
                        st.selectbox(
                            "Hand",
                            HAND_OPTIONS,
                        )
                    )

                action_description = (
                    st.text_input(
                        "Action Description"
                    )
                )

                add_action = (
                    st.form_submit_button(
                        "Action 추가"
                    )
                )

            if add_action:

                episode_start = float(
                    selected_episode[
                        "start_time"
                    ]
                )

                episode_end = float(
                    selected_episode[
                        "end_time"
                    ]
                )

                if (
                    action_end
                    <= action_start
                ):

                    st.error(
                        "End는 Start보다 커야 합니다."
                    )

                elif (
                    action_start
                    < episode_start
                    or action_end
                    > episode_end
                ):

                    st.error(
                        "Action은 Episode 범위 안에 있어야 합니다."
                    )

                else:

                    actions = load_actions()

                    action_id = next_action_id(
                        actions,
                        video_id,
                        selected_episode_id,
                    )

                    now = (
                        datetime.now()
                        .isoformat()
                    )

                    record = {
                        "video_id": video_id,
                        "episode_id": (
                            selected_episode_id
                        ),
                        "action_id": action_id,
                        "start_time": round(
                            action_start,
                            3,
                        ),
                        "end_time": round(
                            action_end,
                            3,
                        ),
                        "duration": round(
                            action_end
                            - action_start,
                            3,
                        ),
                        "action": action_label,
                        "object": action_object,
                        "hand": action_hand,
                        "description": (
                            action_description
                        ),
                        "created_at": now,
                        "updated_at": now,
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

                    save_actions(actions)
                    rebuild_json()

                    st.success(
                        f"{action_id} 생성 완료"
                    )

                    st.rerun()

            # ================================================
            # ACTION LIST
            # ================================================

            actions = load_actions()

            current_actions = actions[
                (
                    actions["video_id"]
                    == video_id
                )
                & (
                    actions["episode_id"]
                    == selected_episode_id
                )
            ].copy()

            if not current_actions.empty:

                current_actions = (
                    current_actions
                    .sort_values(
                        "start_time"
                    )
                )

                sequence = " → ".join(
                    current_actions[
                        "action"
                    ].tolist()
                )

                st.success(
                    f"Action Sequence: {sequence}"
                )

                st.dataframe(
                    current_actions[
                        [
                            "action_id",
                            "start_time",
                            "end_time",
                            "action",
                            "object",
                            "hand",
                            "description",
                        ]
                    ],
                    use_container_width=True,
                    hide_index=True,
                )

                selected_action_id = (
                    st.selectbox(
                        "수정 / 삭제할 Action",
                        current_actions[
                            "action_id"
                        ].tolist(),
                    )
                )

                selected_action = (
                    current_actions[
                        current_actions[
                            "action_id"
                        ]
                        == selected_action_id
                    ]
                    .iloc[0]
                )

                # ============================================
                # EDIT ACTION
                # ============================================

                with st.expander(
                    "✏️ Action 수정"
                ):

                    with st.form(
                        f"edit_action_"
                        f"{selected_action_id}"
                    ):

                        col1, col2 = (
                            st.columns(2)
                        )

                        with col1:

                            new_action_start = (
                                st.number_input(
                                    "Start",
                                    value=float(
                                        selected_action[
                                            "start_time"
                                        ]
                                    ),
                                    step=0.1,
                                    format="%.3f",
                                )
                            )

                        with col2:

                            new_action_end = (
                                st.number_input(
                                    "End",
                                    value=float(
                                        selected_action[
                                            "end_time"
                                        ]
                                    ),
                                    step=0.1,
                                    format="%.3f",
                                )
                            )

                        action_index = (
                            ACTION_OPTIONS.index(
                                selected_action[
                                    "action"
                                ]
                            )
                            if selected_action[
                                "action"
                            ]
                            in ACTION_OPTIONS
                            else 0
                        )

                        object_index = (
                            OBJECT_OPTIONS.index(
                                selected_action[
                                    "object"
                                ]
                            )
                            if selected_action[
                                "object"
                            ]
                            in OBJECT_OPTIONS
                            else 0
                        )

                        hand_index = (
                            HAND_OPTIONS.index(
                                selected_action[
                                    "hand"
                                ]
                            )
                            if selected_action[
                                "hand"
                            ]
                            in HAND_OPTIONS
                            else 0
                        )

                        new_action_label = (
                            st.selectbox(
                                "Action",
                                ACTION_OPTIONS,
                                index=action_index,
                            )
                        )

                        new_action_object = (
                            st.selectbox(
                                "Object",
                                OBJECT_OPTIONS,
                                index=object_index,
                            )
                        )

                        new_action_hand = (
                            st.selectbox(
                                "Hand",
                                HAND_OPTIONS,
                                index=hand_index,
                            )
                        )

                        old_action_description = (
                            selected_action[
                                "description"
                            ]
                        )

                        if pd.isna(
                            old_action_description
                        ):
                            old_action_description = ""

                        new_action_description = (
                            st.text_input(
                                "Description",
                                value=str(
                                    old_action_description
                                ),
                            )
                        )

                        update_action = (
                            st.form_submit_button(
                                "Action 수정 저장"
                            )
                        )

                    if update_action:

                        episode_start = float(
                            selected_episode[
                                "start_time"
                            ]
                        )

                        episode_end = float(
                            selected_episode[
                                "end_time"
                            ]
                        )

                        if (
                            new_action_end
                            <= new_action_start
                        ):

                            st.error(
                                "End는 Start보다 커야 합니다."
                            )

                        elif (
                            new_action_start
                            < episode_start
                            or new_action_end
                            > episode_end
                        ):

                            st.error(
                                "Action은 Episode 범위 안에 있어야 합니다."
                            )

                        else:

                            actions = (
                                load_actions()
                            )

                            mask = (
                                (
                                    actions[
                                        "video_id"
                                    ]
                                    == video_id
                                )
                                & (
                                    actions[
                                        "episode_id"
                                    ]
                                    == selected_episode_id
                                )
                                & (
                                    actions[
                                        "action_id"
                                    ]
                                    == selected_action_id
                                )
                            )

                            actions.loc[
                                mask,
                                "start_time",
                            ] = round(
                                new_action_start,
                                3,
                            )

                            actions.loc[
                                mask,
                                "end_time",
                            ] = round(
                                new_action_end,
                                3,
                            )

                            actions.loc[
                                mask,
                                "duration",
                            ] = round(
                                new_action_end
                                - new_action_start,
                                3,
                            )

                            actions.loc[
                                mask,
                                "action",
                            ] = new_action_label

                            actions.loc[
                                mask,
                                "object",
                            ] = new_action_object

                            actions.loc[
                                mask,
                                "hand",
                            ] = new_action_hand

                            actions.loc[
                                mask,
                                "description",
                            ] = (
                                new_action_description
                            )

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

                            st.success(
                                "Action 수정 완료"
                            )

                            st.rerun()

                # ============================================
                # DELETE ACTION
                # ============================================

                if st.button(
                    "선택한 Action 삭제",
                    key=(
                        f"action_delete_"
                        f"{selected_action_id}"
                    ),
                ):

                    actions = load_actions()

                    actions = actions[
                        ~(
                            (
                                actions[
                                    "video_id"
                                ]
                                == video_id
                            )
                            & (
                                actions[
                                    "episode_id"
                                ]
                                == selected_episode_id
                            )
                            & (
                                actions[
                                    "action_id"
                                ]
                                == selected_action_id
                            )
                        )
                    ]

                    save_actions(actions)
                    rebuild_json()

                    st.success(
                        "Action 삭제 완료"
                    )

                    st.rerun()


# ============================================================
# TAB 3 - DATASET
# ============================================================

with dataset_tab:

    st.header("Ground Truth Dataset")

    videos = find_processed_videos()
    episodes = load_episodes()
    actions = load_actions()

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Videos",
        len(videos),
    )

    col2.metric(
        "Episodes",
        len(episodes),
    )

    col3.metric(
        "Actions",
        len(actions),
    )

    st.subheader("Episodes")

    st.dataframe(
        episodes,
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Actions")

    st.dataframe(
        actions,
        use_container_width=True,
        hide_index=True,
    )

    rebuild_json()

    with st.expander(
        "JSON Preview"
    ):

        if JSON_PATH.exists():

            with open(
                JSON_PATH,
                "r",
                encoding="utf-8",
            ) as f:

                st.json(
                    json.load(f)
                )