import streamlit as st

from views.upload_view import render_upload_view
from views.annotation_view import render_annotation_view
from views.dataset_view import render_dataset_view
from views.video_view import render_video_view

from services.annotation_service import sync_video_registry

from utils.state_utils import (
    get_query_param,
    set_query_param,
)


st.set_page_config(
    page_title="Ego Annotation Tool",
    page_icon="🎥",
    layout="wide",
)


# ============================================================
# EXISTING DATA SYNC
# ============================================================

# 앱을 다시 실행해도 data/processed의 기존 영상들을
# videos.csv와 자동 동기화
sync_video_registry()


# ============================================================
# HEADER
# ============================================================

st.title("🎥 Egocentric Video Annotation Tool")

st.caption(
    "Pick & Place · Manual Ground Truth Builder"
)


# ============================================================
# NAVIGATION
# ============================================================

PAGES = [
    "Upload",
    "Videos",
    "Annotation",
    "Dataset",
]


saved_page = get_query_param(
    "page",
    "Annotation",
)

if saved_page not in PAGES:
    saved_page = "Annotation"


selected_page = st.radio(
    "Navigation",
    PAGES,
    index=PAGES.index(saved_page),
    horizontal=True,
    label_visibility="collapsed",
)


if selected_page != saved_page:
    set_query_param(
        "page",
        selected_page,
    )


st.divider()


# ============================================================
# PAGE
# ============================================================

if selected_page == "Upload":
    render_upload_view()

elif selected_page == "Videos":
    render_video_view()

elif selected_page == "Annotation":
    render_annotation_view()

elif selected_page == "Dataset":
    render_dataset_view()