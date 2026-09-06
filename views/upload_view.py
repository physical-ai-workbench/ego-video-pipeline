from pathlib import Path

import streamlit as st

from config import (
    RAW_DIR,
    PROCESSED_DIR,
    TASK_DISPLAY_NAME,
)

from services.video_service import (
    generate_video_id,
    probe_video,
    extract_video_summary,
    preprocess_video,
)

from services.annotation_service import (
    register_video,
)


def render_upload_view():
    st.subheader(
        "Video Upload"
    )

    st.caption(
        "원본 영상을 업로드하면 "
        "자동 이름 부여 → 분석 → 전처리 → "
        "Dataset 등록까지 수행합니다."
    )

    st.info(
        f"현재 Dataset Task: "
        f"**{TASK_DISPLAY_NAME}**"
    )

    uploaded_file = (
        st.file_uploader(
            "Egocentric Video",
            type=[
                "mp4",
                "mov",
                "m4v",
                "avi",
                "webm",
            ],
        )
    )

    if uploaded_file is None:
        return

    st.write(
        f"원본 파일: "
        f"`{uploaded_file.name}`"
    )

    if not st.button(
        "등록 및 전처리",
        type="primary",
    ):
        return

    video_id = (
        generate_video_id()
    )

    suffix = (
        Path(
            uploaded_file.name
        )
        .suffix
        .lower()
    )

    raw_path = (
        RAW_DIR
        / f"{video_id}{suffix}"
    )

    processed_path = (
        PROCESSED_DIR
        / f"{video_id}.mp4"
    )

    try:

        with st.status(
            "영상 등록 중...",
            expanded=True,
        ) as status:

            st.write(
                "① 원본 영상 저장"
            )

            with open(
                raw_path,
                "wb",
            ) as f:

                f.write(
                    uploaded_file
                    .getbuffer()
                )

            st.write(
                f"✓ Video ID: "
                f"`{video_id}`"
            )

            st.write(
                "② FFprobe 원본 분석"
            )

            original_metadata = (
                probe_video(
                    raw_path
                )
            )

            original_summary = (
                extract_video_summary(
                    original_metadata
                )
            )

            st.write(
                "✓ 분석 완료"
            )

            st.write(
                "③ FFmpeg 전처리"
            )

            st.caption(
                "720p / 30 FPS / "
                "H.264 / AAC"
            )

            preprocess_video(
                raw_path,
                processed_path,
            )

            st.write(
                "✓ 전처리 완료"
            )

            st.write(
                "④ Processed Video 검증"
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

            register_video(
                video_id=video_id,
                original_filename=(
                    uploaded_file.name
                ),
                summary=(
                    processed_summary
                ),
            )

            st.write(
                "✓ Dataset 등록 완료"
            )

            status.update(
                label=(
                    f"{video_id} 등록 완료"
                ),
                state="complete",
                expanded=False,
            )

        st.success(
            f"{video_id} 준비 완료"
        )

        col1, col2 = (
            st.columns(2)
        )

        with col1:

            st.markdown(
                "**Original**"
            )

            st.json(
                original_summary
            )

        with col2:

            st.markdown(
                "**Processed**"
            )

            st.json(
                processed_summary
            )

        st.video(
            str(processed_path)
        )

    except Exception as e:

        st.error(
            f"영상 처리 실패: {e}"
        )