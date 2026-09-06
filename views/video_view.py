import streamlit as st

from config import (
    PROCESSED_DIR,
)

from services.annotation_service import (
    load_videos,
    load_episodes,
    load_actions,
    delete_video,
)

from utils.time_utils import (
    format_time,
)


def render_video_view():

    st.subheader(
        "Video Management"
    )

    st.caption(
        "업로드된 영상을 확인하고 관리합니다."
    )

    videos = load_videos()
    episodes = load_episodes()
    actions = load_actions()

    # ========================================================
    # EMPTY
    # ========================================================

    if videos.empty:

        st.info(
            "등록된 영상이 없습니다."
        )

        return

    # ========================================================
    # SUMMARY
    # ========================================================

    metric1, metric2, metric3 = (
        st.columns(3)
    )

    metric1.metric(
        "Videos",
        len(videos),
    )

    metric2.metric(
        "Episodes",
        len(episodes),
    )

    metric3.metric(
        "Actions",
        len(actions),
    )

    st.divider()

    # ========================================================
    # VIDEO LIST
    # ========================================================

    st.markdown(
        "### Uploaded Videos"
    )

    video_table = (
        videos.copy()
    )

    # Episode Count
    if not episodes.empty:

        episode_counts = (
            episodes.groupby(
                "video_id"
            )
            .size()
            .to_dict()
        )

    else:
        episode_counts = {}

    # Action Count
    if not actions.empty:

        action_counts = (
            actions.groupby(
                "video_id"
            )
            .size()
            .to_dict()
        )

    else:
        action_counts = {}

    video_table[
        "episodes"
    ] = (
        video_table[
            "video_id"
        ]
        .map(
            episode_counts
        )
        .fillna(0)
        .astype(int)
    )

    video_table[
        "actions"
    ] = (
        video_table[
            "video_id"
        ]
        .map(
            action_counts
        )
        .fillna(0)
        .astype(int)
    )

    display_columns = [
        "video_id",
        "original_filename",
        "duration",
        "width",
        "height",
        "fps",
        "codec",
        "episodes",
        "actions",
    ]

    st.dataframe(
        video_table[
            display_columns
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    # ========================================================
    # VIDEO DETAIL
    # ========================================================

    st.markdown(
        "### Video Detail"
    )

    video_ids = (
        videos[
            "video_id"
        ]
        .astype(str)
        .tolist()
    )

    selected_video = (
        st.selectbox(
            "Video",
            video_ids,
        )
    )

    video_row = videos[
        videos["video_id"]
        == selected_video
    ].iloc[0]

    selected_episodes = episodes[
        episodes["video_id"]
        == selected_video
    ]

    selected_actions = actions[
        actions["video_id"]
        == selected_video
    ]

    col1, col2, col3 = (
        st.columns(3)
    )

    col1.metric(
        "Duration",
        format_time(
            float(
                video_row["duration"]
            )
        ),
    )

    col2.metric(
        "Episodes",
        len(
            selected_episodes
        ),
    )

    col3.metric(
        "Actions",
        len(
            selected_actions
        ),
    )

    # ========================================================
    # VIDEO PREVIEW
    # ========================================================

    video_matches = list(
        PROCESSED_DIR.glob(
            f"{selected_video}.*"
        )
    )

    if video_matches:

        st.video(
            str(
                video_matches[0]
            )
        )

    else:

        st.warning(
            "Processed Video 파일을 찾을 수 없습니다."
        )

    st.divider()

    # ========================================================
    # DELETE
    # ========================================================

    st.markdown(
        "### Delete Video"
    )

    st.warning(
        "영상을 삭제하면 관련 Episode, Action, "
        "Clip 데이터도 모두 삭제됩니다."
    )

    confirm_delete = (
        st.checkbox(
            f"{selected_video} 삭제에 동의합니다.",
            key=(
                f"delete_confirm_"
                f"{selected_video}"
            ),
        )
    )

    if st.button(
        "Delete Video",
        type="primary",
        disabled=(
            not confirm_delete
        ),
    ):

        delete_video(
            selected_video
        )

        st.success(
            f"{selected_video} 삭제 완료"
        )

        st.rerun()