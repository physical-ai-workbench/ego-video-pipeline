import streamlit as st


def render_annotation_guide():
    """Pick & Place Annotation Guide."""

    with st.expander(
        "📘 Annotation Guide 보기",
        expanded=False,
    ):

        st.markdown(
            """
### Pick & Place

하나의 물체를 집어서 다른 위치에 놓는 전체 작업을
하나의 **Episode**로 정의합니다.

**기본 구조**

`Pick → Move → Place`
            """
        )

        st.divider()

        pick_col, move_col, place_col = (
            st.columns(3)
        )

        # ====================================================
        # PICK
        # ====================================================

        with pick_col:

            st.markdown(
                "### 🟦 Pick"
            )

            st.write(
                "물체를 집어 기존 지지면에서 "
                "분리하는 동작입니다."
            )

            st.caption(
                "Start"
            )

            st.write(
                "손이 물체를 집기 위한 "
                "명확한 동작을 시작"
            )

            st.caption(
                "End"
            )

            st.write(
                "물체가 기존 지지면에서 "
                "분리된 시점"
            )

        # ====================================================
        # MOVE
        # ====================================================

        with move_col:

            st.markdown(
                "### 🟨 Move"
            )

            st.write(
                "물체를 잡은 상태로 "
                "목표 위치까지 이동합니다."
            )

            st.caption(
                "Start"
            )

            st.write(
                "Pick이 완료된 시점"
            )

            st.caption(
                "End"
            )

            st.write(
                "Place 동작이 시작되는 시점"
            )

        # ====================================================
        # PLACE
        # ====================================================

        with place_col:

            st.markdown(
                "### 🟩 Place"
            )

            st.write(
                "물체를 목표 위치에 놓고 "
                "손을 분리하는 동작입니다."
            )

            st.caption(
                "Start"
            )

            st.write(
                "목표 위치에 물체를 "
                "내려놓기 시작"
            )

            st.caption(
                "End"
            )

            st.write(
                "손이 물체에서 완전히 "
                "분리된 시점"
            )

        st.divider()

        st.markdown(
            "### Annotation Rules"
        )

        st.markdown(
            """
- Action은 반드시 Episode 내부에 있어야 합니다.
- Action 구간끼리는 겹치지 않습니다.
- 기본 순서는 `Pick → Move → Place`입니다.
- 동일 동작은 항상 동일 Label을 사용합니다.
- 알 수 없는 Object는 `other`를 사용합니다.
- 경계가 애매하더라도 전체 Dataset에서 동일한 기준을 유지합니다.
            """
        )

        st.info(
            "시간 표기: MM:SS.mmm "
            "예) 00:01.000 = 1초"
        )