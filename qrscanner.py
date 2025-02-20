import ctypes
import streamlit as st

# Correct path for libzbar
libzbar_path = "/usr/lib/x86_64-linux-gnu/libzbar.so.0"

try:
    libzbar = ctypes.CDLL(libzbar_path)
    st.success(f"✅ Successfully loaded libzbar from: {libzbar_path}")
except OSError as e:
    st.error(f"❌ Error loading libzbar: {e}")
    st.stop()
