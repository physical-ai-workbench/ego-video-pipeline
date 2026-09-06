import pandas as pd
import streamlit as st

from utils.state_utils import (
    get_query_param,
    set_query_param,
)

from config import (
    PROCESSED_DIR,
    CLIP_DIR,
    FRAME_STEP,
    OBJECT_OPTIONS,
    ACTION_OPTIONS,
    HAND_OPTIONS,
    TASK_DISPLAY_NAME,
)

from utils.time_utils import (
    format_time,
)

from services.annotation_service import (
    load_videos,
    get_video_episodes,
    get_episode,
    get_episode_actions,
    create_episode,
    update_episode,
    delete_episode,
    create_action,
    update_action,
    delete_action,
)

from services.video_service import (
    extract_episode_clip,
)

from components.guide import (
    render_annotation_guide,
)

from components.timeline import (
    render_action_timeline,
)


# ============================================================
# 선택값 위치 찾기
# ============================================================

def _object_index(
    value,
):
    """
    현재 Object 값이
    선택 목록에서 몇 번째인지 찾습니다.
    """

    if value in OBJECT_OPTIONS:
        return OBJECT_OPTIONS.index(
            value
        )

    return 0


def _action_index(
    value,
):
    """
    현재 Action 값이
    선택 목록에서 몇 번째인지 찾습니다.
    """

    if value in ACTION_OPTIONS:
        return ACTION_OPTIONS.index(
            value
        )

    return 0


def _hand_index(
    value,
):
    """
    현재 Hand 값이
    선택 목록에서 몇 번째인지 찾습니다.
    """

    if value in HAND_OPTIONS:
        return HAND_OPTIONS.index(
            value
        )

    return 0


# ============================================================
# Annotation 화면
# ============================================================

def render_annotation_view():

    videos = load_videos()

    # ========================================================
    # 등록된 영상 확인
    # ========================================================

    if videos.empty:

        st.warning(
            "등록된 영상이 없습니다. "
            "먼저 Upload 페이지에서 영상을 등록해 주세요."
        )

        return

    # ========================================================
    # 제목
    # ========================================================

    st.subheader(
        f"{TASK_DISPLAY_NAME} 어노테이션"
    )

    render_annotation_guide()

    # ========================================================
    # 영상 선택
    # ========================================================

    task_videos = videos[
        videos["task_type"]
        == "pick_and_place"
    ].copy()

    video_options = (
        task_videos[
            "video_id"
        ].tolist()
    )

    if not video_options:

        st.warning(
            "현재 작업에 사용할 수 있는 영상이 없습니다."
        )

        return

    saved_video = get_query_param(
        "video"
    )

    if saved_video not in video_options:
        saved_video = (
            video_options[0]
        )

    selected_video_id = (
        st.selectbox(
            "영상 선택",
            video_options,
            index=(
                video_options.index(
                    saved_video
                )
            ),
        )
    )

    if (
        selected_video_id
        != saved_video
    ):
        set_query_param(
            "video",
            selected_video_id,
        )

    video_row = (
        task_videos[
            task_videos[
                "video_id"
            ]
            == selected_video_id
        ]
        .iloc[0]
    )

    video_path = (
        PROCESSED_DIR
        / f"{selected_video_id}.mp4"
    )

    video_duration = float(
        video_row["duration"]
    )

    # ========================================================
    # 영상 + 새 에피소드 입력 영역
    # ========================================================

    video_col, episode_col = (
        st.columns(
            [2.2, 1]
        )
    )

    # 영상 표시
    with video_col:

        st.video(
            str(video_path)
        )

        st.caption(
            f"{selected_video_id} · "
            f"영상 길이 "
            f"{format_time(video_duration)}"
        )

    # 새 에피소드 정보 입력
    with episode_col:

        st.markdown(
            "### 새 에피소드 만들기"
        )

        episode_object = (
            st.selectbox(
                "대상 물체",
                OBJECT_OPTIONS,
                key=(
                    f"new_object_"
                    f"{selected_video_id}"
                ),
            )
        )

        episode_description = (
            st.text_input(
                "설명",
                placeholder=(
                    "예: 컵을 집어서 "
                    "상자 안에 놓기"
                ),
                key=(
                    f"new_desc_"
                    f"{selected_video_id}"
                ),
            )
        )

        st.caption(
            "아래 구간 선택 바에서 "
            "에피소드의 시작과 종료 구간을 지정하세요."
        )

    # ========================================================
    # 새 에피소드 구간 선택
    # ========================================================

    default_end = min(
        5.0,
        video_duration,
    )

    episode_range = st.slider(
        "에피소드 구간",
        min_value=0.0,
        max_value=video_duration,
        value=(
            0.0,
            default_end,
        ),
        step=FRAME_STEP,
        format="%.3f",
        key=(
            f"episode_range_"
            f"{selected_video_id}"
        ),
    )

    ep_start, ep_end = (
        episode_range
    )

    time1, time2, time3 = (
        st.columns(3)
    )

    time1.metric(
        "시작 시간",
        format_time(ep_start),
    )

    time2.metric(
        "종료 시간",
        format_time(ep_end),
    )

    time3.metric(
        "구간 길이",
        format_time(
            ep_end - ep_start
        ),
    )

    if st.button(
        "＋ 에피소드 생성",
        type="primary",
        use_container_width=True,
    ):

        if ep_end <= ep_start:

            st.error(
                "종료 시간은 시작 시간보다 "
                "뒤에 있어야 합니다."
            )

        else:

            episode_id = (
                create_episode(
                    video_id=(
                        selected_video_id
                    ),
                    start_time=ep_start,
                    end_time=ep_end,
                    object_name=(
                        episode_object
                    ),
                    description=(
                        episode_description
                    ),
                )
            )

            extract_episode_clip(
                video_path=video_path,
                video_id=(
                    selected_video_id
                ),
                episode_id=(
                    episode_id
                ),
                start_time=ep_start,
                end_time=ep_end,
            )

            st.success(
                f"{episode_id} 생성 완료"
            )

            st.rerun()

    # ========================================================
    # 기존 에피소드
    # ========================================================

    st.divider()

    episodes = get_video_episodes(
        selected_video_id
    )

    if episodes.empty:

        st.info(
            "아직 생성된 에피소드가 없습니다."
        )

        return

    st.markdown(
        "### 생성된 에피소드"
    )

    episode_labels = {}

    for _, episode in (
        episodes.iterrows()
    ):

        label = (
            f"{episode['episode_id']} · "
            f"{format_time(episode['start_time'])}"
            f" → "
            f"{format_time(episode['end_time'])}"
        )

        episode_labels[label] = (
            episode["episode_id"]
        )

    saved_episode = (
        get_query_param(
            "episode"
        )
    )

    episode_ids = list(
        episode_labels.values()
    )

    if (
        saved_episode
        not in episode_ids
    ):
        saved_episode = (
            episode_ids[0]
        )

    saved_label = next(
        label
        for label, episode_id
        in episode_labels.items()
        if episode_id
        == saved_episode
    )

    labels = list(
        episode_labels.keys()
    )

    selected_label = (
        st.selectbox(
            "에피소드 선택",
            labels,
            index=(
                labels.index(
                    saved_label
                )
            ),
        )
    )

    selected_episode_id = (
        episode_labels[
            selected_label
        ]
    )

    if (
        selected_episode_id
        != saved_episode
    ):
        set_query_param(
            "episode",
            selected_episode_id,
        )

    episode = get_episode(
        selected_video_id,
        selected_episode_id,
    )

    # ========================================================
    # 선택한 에피소드 정보
    # ========================================================

    episode_left, episode_right = (
        st.columns(
            [3, 1]
        )
    )

    # Episode Clip
    with episode_left:

        clip_path = (
            CLIP_DIR
            / selected_video_id
            / (
                f"{selected_video_id}_"
                f"{selected_episode_id}.mp4"
            )
        )

        if clip_path.exists():

            st.video(
                str(clip_path)
            )

        else:

            st.info(
                "에피소드 영상 클립이 없습니다."
            )

    # Episode 정보
    with episode_right:

        st.metric(
            "시작 시간",
            format_time(
                episode[
                    "start_time"
                ]
            ),
        )

        st.metric(
            "종료 시간",
            format_time(
                episode[
                    "end_time"
                ]
            ),
        )

        st.write(
            f"**대상 물체:** "
            f"{episode['object']}"
        )

    # ========================================================
    # 에피소드 수정 / 삭제
    # ========================================================

    with st.expander(
        "에피소드 수정 / 삭제",
        expanded=False,
    ):

        edit_range = st.slider(
            "에피소드 구간 수정",
            min_value=0.0,
            max_value=video_duration,
            value=(
                float(
                    episode[
                        "start_time"
                    ]
                ),
                float(
                    episode[
                        "end_time"
                    ]
                ),
            ),
            step=FRAME_STEP,
            format="%.3f",
            key=(
                f"edit_episode_range_"
                f"{selected_episode_id}"
            ),
        )

        edit_start, edit_end = (
            edit_range
        )

        st.caption(
            f"{format_time(edit_start)}"
            f" → "
            f"{format_time(edit_end)}"
        )

        edit_object = (
            st.selectbox(
                "대상 물체",
                OBJECT_OPTIONS,
                index=_object_index(
                    episode["object"]
                ),
                key=(
                    f"edit_episode_object_"
                    f"{selected_episode_id}"
                ),
            )
        )

        description = (
            ""
            if pd.isna(
                episode[
                    "description"
                ]
            )
            else str(
                episode[
                    "description"
                ]
            )
        )

        edit_description = (
            st.text_input(
                "설명",
                value=description,
                key=(
                    f"edit_episode_desc_"
                    f"{selected_episode_id}"
                ),
            )
        )

        col1, col2 = (
            st.columns(2)
        )

        # Episode 수정
        if col1.button(
            "수정 내용 저장",
            key=(
                f"update_episode_"
                f"{selected_episode_id}"
            ),
            use_container_width=True,
        ):

            try:

                update_episode(
                    video_id=(
                        selected_video_id
                    ),
                    episode_id=(
                        selected_episode_id
                    ),
                    start_time=(
                        edit_start
                    ),
                    end_time=(
                        edit_end
                    ),
                    object_name=(
                        edit_object
                    ),
                    description=(
                        edit_description
                    ),
                )

                # 수정된 시간 기준으로 Clip 다시 생성
                extract_episode_clip(
                    video_path,
                    selected_video_id,
                    selected_episode_id,
                    edit_start,
                    edit_end,
                )

                st.success(
                    "에피소드 수정 완료"
                )

                st.rerun()

            except ValueError as e:

                st.error(
                    str(e)
                )

        # Episode 삭제
        if col2.button(
            "에피소드 삭제",
            key=(
                f"delete_episode_"
                f"{selected_episode_id}"
            ),
            use_container_width=True,
        ):

            delete_episode(
                selected_video_id,
                selected_episode_id,
            )

            st.success(
                "에피소드 삭제 완료"
            )

            st.rerun()

    # ========================================================
    # 액션 구간 나누기
    # ========================================================

    st.divider()

    st.markdown(
        "### 액션 구간 나누기"
    )

    st.caption(
        "에피소드 안에서 행동이 일어난 구간을 선택하고 "
        "Pick / Move / Place 중 하나를 지정합니다."
    )

    actions = get_episode_actions(
        selected_video_id,
        selected_episode_id,
    )

    render_action_timeline(
        episode,
        actions,
    )

    episode_start = float(
        episode["start_time"]
    )

    episode_end = float(
        episode["end_time"]
    )

    action_range = st.slider(
        "액션 구간",
        min_value=episode_start,
        max_value=episode_end,
        value=(
            episode_start,
            episode_end,
        ),
        step=FRAME_STEP,
        format="%.3f",
        key=(
            f"new_action_range_"
            f"{selected_episode_id}"
        ),
    )

    action_start, action_end = (
        action_range
    )

    range_left, range_right = (
        st.columns(2)
    )

    range_left.write(
        f"**시작 시간**  "
        f"{format_time(action_start)}"
    )

    range_right.write(
        f"**종료 시간**  "
        f"{format_time(action_end)}"
    )

    action_col, hand_col = (
        st.columns(2)
    )

    # Action 선택
    with action_col:

        action_label = st.radio(
            "행동 종류",
            ACTION_OPTIONS,
            horizontal=True,
            key=(
                f"new_action_label_"
                f"{selected_episode_id}"
            ),
        )

    # Hand 선택
    with hand_col:

        hand = st.selectbox(
            "사용한 손",
            HAND_OPTIONS,
            key=(
                f"new_action_hand_"
                f"{selected_episode_id}"
            ),
        )

    st.caption(
        f"대상 물체는 에피소드에서 선택한 "
        f"`{episode['object']}`가 자동으로 사용됩니다."
    )

    if st.button(
        f"＋ {action_label.title()} 액션 추가",
        type="primary",
        key=(
            f"add_action_"
            f"{selected_episode_id}"
        ),
    ):

        try:

            create_action(
                video_id=(
                    selected_video_id
                ),
                episode_id=(
                    selected_episode_id
                ),
                start_time=(
                    action_start
                ),
                end_time=(
                    action_end
                ),
                action_label=(
                    action_label
                ),
                object_name=(
                    episode["object"]
                ),
                hand=hand,
                description="",
            )

            st.success(
                f"{action_label.title()} "
                f"액션 추가 완료"
            )

            st.rerun()

        except ValueError as e:

            st.error(
                str(e)
            )

    # ========================================================
    # 등록된 액션 목록
    # ========================================================

    actions = get_episode_actions(
        selected_video_id,
        selected_episode_id,
    )

    if actions.empty:

        st.info(
            "아직 등록된 액션이 없습니다."
        )

        return

    st.markdown(
        "#### 등록된 액션"
    )

    for _, action in (
        actions.iterrows()
    ):

        with st.container(
            border=True
        ):

            info_col, button_col = (
                st.columns(
                    [5, 1]
                )
            )

            # Action 정보
            with info_col:

                st.write(
                    f"**{action['action'].title()}**"
                    f"  ·  "
                    f"{format_time(action['start_time'])}"
                    f" → "
                    f"{format_time(action['end_time'])}"
                )

                st.caption(
                    f"대상 물체: "
                    f"{action['object']} · "
                    f"사용한 손: "
                    f"{action['hand']}"
                )

            # Action 삭제
            with button_col:

                if st.button(
                    "삭제",
                    key=(
                        f"delete_action_"
                        f"{action['action_id']}"
                    ),
                    use_container_width=True,
                ):

                    delete_action(
                        selected_video_id,
                        selected_episode_id,
                        action[
                            "action_id"
                        ],
                    )

                    st.rerun()

            # =================================================
            # 액션 수정
            # =================================================

            with st.expander(
                "수정",
                expanded=False,
            ):

                edit_action_range = (
                    st.slider(
                        "액션 구간 수정",
                        min_value=(
                            episode_start
                        ),
                        max_value=(
                            episode_end
                        ),
                        value=(
                            float(
                                action[
                                    "start_time"
                                ]
                            ),
                            float(
                                action[
                                    "end_time"
                                ]
                            ),
                        ),
                        step=FRAME_STEP,
                        format="%.3f",
                        key=(
                            f"edit_action_range_"
                            f"{action['action_id']}"
                        ),
                    )
                )

                new_start, new_end = (
                    edit_action_range
                )

                st.caption(
                    f"{format_time(new_start)}"
                    f" → "
                    f"{format_time(new_end)}"
                )

                new_label = (
                    st.selectbox(
                        "행동 종류",
                        ACTION_OPTIONS,
                        index=_action_index(
                            action[
                                "action"
                            ]
                        ),
                        key=(
                            f"edit_action_label_"
                            f"{action['action_id']}"
                        ),
                    )
                )

                new_hand = (
                    st.selectbox(
                        "사용한 손",
                        HAND_OPTIONS,
                        index=_hand_index(
                            action[
                                "hand"
                            ]
                        ),
                        key=(
                            f"edit_action_hand_"
                            f"{action['action_id']}"
                        ),
                    )
                )

                if st.button(
                    "액션 수정 내용 저장",
                    key=(
                        f"save_action_"
                        f"{action['action_id']}"
                    ),
                    use_container_width=True,
                ):

                    try:

                        update_action(
                            video_id=(
                                selected_video_id
                            ),
                            episode_id=(
                                selected_episode_id
                            ),
                            action_id=(
                                action[
                                    "action_id"
                                ]
                            ),
                            start_time=(
                                new_start
                            ),
                            end_time=(
                                new_end
                            ),
                            action_label=(
                                new_label
                            ),
                            object_name=(
                                episode[
                                    "object"
                                ]
                            ),
                            hand=(
                                new_hand
                            ),
                            description="",
                        )

                        st.success(
                            "액션 수정 완료"
                        )

                        st.rerun()

                    except ValueError as e:

                        st.error(
                            str(e)
                        )