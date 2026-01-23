import streamlit as st

def show():
    st.markdown("""
    <style>
    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #f0f2f6;
        border-top: 1px solid #ddd;
        padding: 10px 0;
        text-align: center;
        font-size: 24px;
    }
    </style>
    """, unsafe_allow_html=True)