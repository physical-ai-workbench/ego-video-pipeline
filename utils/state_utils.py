import streamlit as st


def get_query_param(name: str, default=None):
    value = st.query_params.get(name)

    if value is None or value == "":
        return default

    return value


def set_query_param(name: str, value):
    if value is None:
        if name in st.query_params:
            del st.query_params[name]
        return

    st.query_params[name] = str(value)


def clear_query_param(name: str):
    if name in st.query_params:
        del st.query_params[name]