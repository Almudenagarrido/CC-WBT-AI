import utils as u
import streamlit as st

def show():

    niccp_path = "public/niccp_logo.png"
    se4all_path = "public/se4all_logo.png"
    iit_path = "public/iit_logo.png"
    niccp_base64 = u.get_base64_of_bin_file(niccp_path)
    se4all_base64 = u.get_base64_of_bin_file(se4all_path)
    iit_base64 = u.get_base64_of_bin_file(iit_path)

    st.markdown("""
    <style>
    .header {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background-color: #f0f2f6;
        border-bottom: 1px solid #ddd;
        padding: 10px 0;
        text-align: center;
        font-size: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 20px;
        z-index: 1000;
    }
    .header img {
        height: 40px;
        width: auto;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f'''
                <div class="header">
                National Integrated Clean Cooking Plan (NICCP)
                <img src="data:image/png;base64,{niccp_base64}" />
                <img src="data:image/png;base64,{se4all_base64}" />
                <img src="data:image/png;base64,{iit_base64}" />
                </div>''', unsafe_allow_html=True)