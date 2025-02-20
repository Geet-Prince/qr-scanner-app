import os
import ctypes
import streamlit as st

# Try loading libzbar from common locations
common_paths = [
    "/usr/lib/libzbar.so.0",
    "/usr/local/lib/libzbar.so.0",
    "/lib/x86_64-linux-gnu/libzbar.so.0",
    "/lib/libzbar.so.0"
]

found = False
for path in common_paths:
    if os.path.exists(path):
        try:
            libzbar = ctypes.CDLL(path)
            st.success(f"✅ Loaded libzbar from {path}")
            found = True
            break
        except OSError as e:
            st.warning(f"Failed to load libzbar from {path}: {e}")

if not found:
    st.error("❌ libzbar.so.0 not found in common locations. Check installation.")

# Now import the necessary modules
import cv2
import numpy as np
from pyzbar.pyzbar import decode
