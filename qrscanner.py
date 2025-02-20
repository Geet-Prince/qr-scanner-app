import os
import subprocess
import streamlit as st

# Debug: Check if libzbar is installed
try:
    result = subprocess.run(["ldconfig", "-p"], capture_output=True, text=True)
    if "libzbar.so" in result.stdout:
        st.write("✅ libzbar is installed!")
        st.write(result.stdout)  # Print all available libraries
    else:
        st.error("❌ libzbar.so.0 NOT FOUND!")
except Exception as e:
    st.error(f"⚠ Error running ldconfig: {e}")

# Debug: Check library directories
lib_dirs = ["/usr/lib", "/usr/local/lib", "/lib", "/usr/lib/x86_64-linux-gnu", "/lib/x86_64-linux-gnu"]
found_paths = []
for lib_dir in lib_dirs:
    if os.path.exists(os.path.join(lib_dir, "libzbar.so.0")):
        found_paths.append(os.path.join(lib_dir, "libzbar.so.0"))

if found_paths:
    st.write(f"✅ Found libzbar in: {found_paths}")
else:
    st.error("❌ libzbar.so.0 NOT FOUND in expected locations!")
