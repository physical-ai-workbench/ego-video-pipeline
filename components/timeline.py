import streamlit as st


ACTION_COLORS = {
    "pick": "#4CAF50",
    "move": "#2196F3",
    "place": "#FF9800",
}


def render_action_timeline(
    episode,
    actions,
):
    """
    선택한 Episode 안에서
    각 Action이 어느 구간에 있는지 보여줍니다.
    """

    st.markdown(
        "#### 액션 타임라인"
    )

    episode_start = float(
        episode["start_time"]
    )

    episode_end = float(
        episode["end_time"]
    )

    episode_duration = (
        episode_end
        - episode_start
    )

    if episode_duration <= 0:
        st.warning(
            "에피소드 구간이 올바르지 않습니다."
        )
        return

    # ========================================================
    # Timeline
    # ========================================================

    timeline_html = """
    <div style="
        position: relative;
        width: 100%;
        height: 44px;
        background: #eeeeee;
        border-radius: 6px;
        overflow: hidden;
        margin-top: 8px;
        margin-bottom: 8px;
    ">
    """

    if not actions.empty:

        for _, action in actions.iterrows():

            action_start = float(
                action["start_time"]
            )

            action_end = float(
                action["end_time"]
            )

            left = (
                (
                    action_start
                    - episode_start
                )
                / episode_duration
                * 100
            )

            width = (
                (
                    action_end
                    - action_start
                )
                / episode_duration
                * 100
            )

            action_name = str(
                action["action"]
            )

            color = ACTION_COLORS.get(
                action_name,
                "#9E9E9E",
            )

            timeline_html += f"""
            <div style="
                position: absolute;
                left: {left:.3f}%;
                width: {width:.3f}%;
                height: 100%;
                background: {color};
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 12px;
                font-weight: 600;
                border-right: 1px solid white;
                box-sizing: border-box;
            ">
                {action_name}
            </div>
            """

    timeline_html += """
    </div>
    """

    st.markdown(
        timeline_html,
        unsafe_allow_html=True,
    )

    # ========================================================
    # 시간 표시
    # ========================================================

    left_col, right_col = (
        st.columns(2)
    )

    left_col.caption(
        f"시작: {episode_start:.3f}초"
    )

    right_col.caption(
        f"종료: {episode_end:.3f}초"
    )