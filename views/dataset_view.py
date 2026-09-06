import math
import json

import pandas as pd
import streamlit as st

from config import (
    JSON_PATH,
    TASK_DISPLAY_NAME,
)

from services.annotation_service import (
    load_videos,
    load_episodes,
    load_actions,
    rebuild_json,
)

from utils.time_utils import (
    format_time,
)

from utils.state_utils import (
    get_query_param,
    set_query_param,
)


# ============================================================
# 페이지 나누기
# ============================================================

def render_paginated_dataframe(
    df,
    key,
):
    """
    데이터가 많을 때 여러 페이지로 나누어 보여줍니다.
    """

    if df.empty:
        st.info(
            "표시할 데이터가 없습니다."
        )
        return

    control1, control2 = st.columns(
        [1, 3]
    )

    with control1:

        page_size = st.selectbox(
            "한 페이지에 표시할 행 수",
            [
                25,
                50,
                100,
            ],
            index=1,
            key=f"{key}_size",
        )

    total_rows = len(df)

    total_pages = max(
        1,
        math.ceil(
            total_rows
            / page_size
        ),
    )

    with control2:

        page = st.number_input(
            "페이지",
            min_value=1,
            max_value=total_pages,
            value=1,
            step=1,
            key=f"{key}_page",
        )

    start = (
        (page - 1)
        * page_size
    )

    end = (
        start
        + page_size
    )

    page_df = df.iloc[
        start:end
    ]

    st.caption(
        f"전체 {total_rows:,}개 · "
        f"{page}/{total_pages} 페이지"
    )

    st.dataframe(
        page_df,
        use_container_width=True,
        hide_index=True,
        height=500,
    )


# ============================================================
# Dataset 화면
# ============================================================

def render_dataset_view():

    st.subheader(
        "Ground Truth Dataset"
    )

    st.caption(
        f"현재 작업: "
        f"{TASK_DISPLAY_NAME}"
    )

    # ========================================================
    # 데이터 불러오기
    # ========================================================

    videos = load_videos()
    episodes = load_episodes()
    actions = load_actions()

    # ========================================================
    # 영상 필터
    # ========================================================

    video_ids = (
        videos["video_id"]
        .dropna()
        .astype(str)
        .tolist()
    )

    filter_options = [
        "전체",
        *video_ids,
    ]

    saved_filter = get_query_param(
        "dataset_video",
        "전체",
    )

    if (
        saved_filter
        not in filter_options
    ):
        saved_filter = "전체"

    selected_filter = st.selectbox(
        "영상 선택",
        filter_options,
        index=(
            filter_options.index(
                saved_filter
            )
        ),
    )

    if (
        selected_filter
        != saved_filter
    ):
        set_query_param(
            "dataset_video",
            selected_filter,
        )

    # ========================================================
    # 선택한 영상에 맞게 데이터 필터링
    # ========================================================

    if selected_filter == "전체":

        filtered_videos = (
            videos.copy()
        )

        filtered_episodes = (
            episodes.copy()
        )

        filtered_actions = (
            actions.copy()
        )

    else:

        filtered_videos = videos[
            videos["video_id"]
            == selected_filter
        ].copy()

        filtered_episodes = episodes[
            episodes["video_id"]
            == selected_filter
        ].copy()

        filtered_actions = actions[
            actions["video_id"]
            == selected_filter
        ].copy()

    # ========================================================
    # 데이터 개수
    # ========================================================

    metric1, metric2, metric3 = (
        st.columns(3)
    )

    metric1.metric(
        "영상 수",
        len(filtered_videos),
    )

    metric2.metric(
        "에피소드 수",
        len(filtered_episodes),
    )

    metric3.metric(
        "액션 수",
        len(filtered_actions),
    )

    st.divider()

    # ========================================================
    # 상세 데이터
    # ========================================================

    st.markdown(
        "### 상세 데이터"
    )

    video_tab, episode_tab, action_tab = (
        st.tabs(
            [
                "영상",
                "에피소드",
                "액션",
            ]
        )
    )

    # ========================================================
    # 영상
    # ========================================================

    with video_tab:

        video_display = (
            filtered_videos.copy()
        )

        render_paginated_dataframe(
            video_display,
            key="videos",
        )

    # ========================================================
    # 에피소드
    # ========================================================

    with episode_tab:

        episode_display = (
            filtered_episodes.copy()
        )

        if not episode_display.empty:

            episode_display[
                "시작 시간"
            ] = (
                episode_display[
                    "start_time"
                ]
                .apply(
                    format_time
                )
            )

            episode_display[
                "종료 시간"
            ] = (
                episode_display[
                    "end_time"
                ]
                .apply(
                    format_time
                )
            )

            # 화면에서는 필요한 정보 위주로 표시
            episode_columns = [
                "video_id",
                "episode_id",
                "시작 시간",
                "종료 시간",
                "duration",
                "object",
                "description",
                "created_at",
                "updated_at",
            ]

            existing_columns = [
                column
                for column
                in episode_columns
                if column
                in episode_display.columns
            ]

            episode_display = (
                episode_display[
                    existing_columns
                ]
            )

        render_paginated_dataframe(
            episode_display,
            key="episodes",
        )

    # ========================================================
    # 액션
    # ========================================================

    with action_tab:

        action_display = (
            filtered_actions.copy()
        )

        if not action_display.empty:

            action_display[
                "시작 시간"
            ] = (
                action_display[
                    "start_time"
                ]
                .apply(
                    format_time
                )
            )

            action_display[
                "종료 시간"
            ] = (
                action_display[
                    "end_time"
                ]
                .apply(
                    format_time
                )
            )

            action_columns = [
                "video_id",
                "episode_id",
                "action_id",
                "action",
                "시작 시간",
                "종료 시간",
                "duration",
                "object",
                "hand",
                "description",
                "created_at",
                "updated_at",
            ]

            existing_columns = [
                column
                for column
                in action_columns
                if column
                in action_display.columns
            ]

            action_display = (
                action_display[
                    existing_columns
                ]
            )

        render_paginated_dataframe(
            action_display,
            key="actions",
        )

    # ========================================================
    # JSON 미리보기
    # ========================================================

    st.divider()

    rebuild_json()

    with st.expander(
        "JSON 데이터 미리보기",
        expanded=False,
    ):

        if not JSON_PATH.exists():

            st.info(
                "JSON 데이터가 없습니다."
            )

            return

        with open(
            JSON_PATH,
            "r",
            encoding="utf-8",
        ) as f:

            json_data = (
                json.load(f)
            )

        if selected_filter == "전체":

            st.json(
                json_data
            )

        else:

            filtered_json = [
                item
                for item
                in json_data
                if item.get(
                    "video_id"
                )
                == selected_filter
            ]

            st.json(
                filtered_json
            )