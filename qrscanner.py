import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import cv2
import numpy as np
import ctypes
import os
from pyzbar.pyzbar import decode

# ----------------- GOOGLE SHEETS SETUP -----------------
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

try:
    creds_json = st.secrets["google_credentials"]  # Fetch credentials from Streamlit secrets
    CREDS = Credentials.from_service_account_info(creds_json, scopes=SCOPE)
    client = gspread.authorize(CREDS)

    SHEET_ID = "1I8z27cmHXUB48B6J52_p56elELf2tQVv_K-ra6jf1iQ"  # Replace with actual Google Sheet ID
    SHEET_NAME = "Attendees"

    try:
        sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    except gspread.exceptions.SpreadsheetNotFound:
        st.error("Spreadsheet not found. Check your SHEET_ID.")
        st.stop()
    except gspread.exceptions.WorksheetNotFound:
        st.error("Worksheet not found. Check your SHEET_NAME.")
        st.stop()

except KeyError:
    st.error("Google credentials not found. Set up 'google_credentials' in Streamlit Cloud secrets.")
    st.stop()
except Exception as e:
    st.error(f"Error loading credentials: {e}")
    st.stop()

# ----------------- FIND & LOAD LIBZBAR -----------------
LIBZBAR_LOCATIONS = [
    "/usr/lib/x86_64-linux-gnu/libzbar.so.0",
    "/usr/local/lib/libzbar.so.0",
    "/lib/x86_64-linux-gnu/libzbar.so.0"
]

libzbar = None
for path in LIBZBAR_LOCATIONS:
    if os.path.exists(path):
        try:
            libzbar = ctypes.CDLL(path)
            st.success(f"✅ Successfully loaded libzbar from: {path}")
            break
        except OSError:
            continue

if not libzbar:
    st.error("❌ libzbar.so.0 not found in common locations. Check installation.")
    st.stop()

# ----------------- STREAMLIT UI -----------------
st.title("📸 QR Code Scanner & Verification")

scan_option = st.radio("Select Scan Mode:", ["📂 Upload QR Image", "📷 Live Camera"])

# ----------------- FUNCTION TO READ QR CODE -----------------
def read_qr_from_image(image):
    try:
        np_image = np.array(bytearray(image.read()), dtype=np.uint8)
        img = cv2.imdecode(np_image, cv2.IMREAD_COLOR)
        qr_codes = decode(img)

        if qr_codes:
            return qr_codes[0].data.decode("utf-8")
        return None
    except Exception as e:
        st.error(f"Error reading QR code: {e}")
        return None

# ----------------- VERIFY USER IN GOOGLE SHEET -----------------
def verify_user(qr_data):
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    qr_lines = qr_data.split("\n")
    for line in qr_lines:
        if line.startswith("ID: "):
            qr_id = line.replace("ID: ", "").strip()
            user_row = df[df["ID"] == qr_id]

            if not user_row.empty:
                user_name = user_row.iloc[0]["Name"]
                user_mobile = user_row.iloc[0]["Mobile"]
                verified_status = user_row.iloc[0]["Verified"]

                if verified_status == "✅":
                    return f"⚠ Duplicate Entry: {user_name} has already been verified!"
                else:
                    cell = sheet.find(qr_id)
                    if cell:
                        sheet.update_cell(cell.row, 4, "✅")
                        return f"✅ User Verified: {user_name} (Mobile: {user_mobile})"
                    else:
                        return "❌ Error: ID not found in sheet after initial verification."

            else:
                return "❌ No user found in the database."

    return "❌ Invalid QR Code Format."

# ----------------- HANDLE UPLOADED IMAGE -----------------
if scan_option == "📂 Upload QR Image":
    uploaded_file = st.file_uploader("Upload a QR Code Image", type=["png", "jpg", "jpeg"])
    if uploaded_file:
        st.image(uploaded_file, caption="Uploaded QR Code", use_column_width=True)
        qr_result = read_qr_from_image(uploaded_file)

        if qr_result:
            st.success(f"🔍 QR Code Scanned: {qr_result}")
            verification_result = verify_user(qr_result)
            st.write(verification_result)
        else:
            st.error("❌ No QR Code detected in the image.")

# ----------------- LIVE CAMERA QR SCANNING -----------------
elif scan_option == "📷 Live Camera":
    st.warning("⚠ Make sure your camera is accessible.")

    cap = cv2.VideoCapture(0)  # Open webcam
    frame_placeholder = st.empty()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            st.error("❌ Unable to access camera.")
            break

        qr_codes = decode(frame)
        for qr_code in qr_codes:
            qr_data = qr_code.data.decode("utf-8")
            st.success(f"🔍 QR Code Scanned: {qr_data}")
            verification_result = verify_user(qr_data)
            st.write(verification_result)

            # Draw rectangle around QR code
            (x, y, w, h) = qr_code.rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Stop capturing once QR is found
            cap.release()
            cv2.destroyAllWindows()
            break

        # Convert frame to RGB and display in Streamlit
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_placeholder.image(frame, channels="RGB")

    cap.release()
    cv2.destroyAllWindows()
