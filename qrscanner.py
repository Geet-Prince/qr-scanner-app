import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import cv2
import numpy as np
from pyzbar.pyzbar import decode
import os
import ctypes


# ----------------- GOOGLE SHEETS SETUP (USING SECRETS) -----------------
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

try:
    creds_json = st.secrets["google_credentials"]  # Use the secret name
    CREDS = Credentials.from_service_account_info(creds_json, scopes=SCOPE)
    client = gspread.authorize(CREDS)

    SHEET_ID = "1I8z27cmHXUB48B6J52_p56elELf2tQVv_K-ra6jf1iQ"  # Replace with actual Google Sheet ID
    SHEET_NAME = "Attendees"
    try:
        sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    except gspread.exceptions.SpreadsheetNotFound:
        st.error("Spreadsheet not found. Check your SHEET_ID.")
        st.stop()  # Stop execution
    except gspread.exceptions.WorksheetNotFound:
        st.error("Worksheet not found. Check your SHEET_NAME.")
        st.stop()

except KeyError:
    st.error("Google credentials secret 'google_credentials' not found. Please set up the secret in Streamlit Cloud.")
    st.stop()
except Exception as e:
    st.error(f"Error loading credentials: {e}")
    st.stop()

# ----------------- Load libzbar (CRUCIAL FIX) -----------------
try:
    libzbar_path = "/usr/local/lib/libzbar.so.0"  # Path inside the Docker container
    libzbar = ctypes.CDLL(libzbar_path)
except OSError as e:
    st.error(f"Error loading libzbar: {e}")
    st.stop()  # Stop execution if libzbar cannot be loaded

# ----------------- IMPORT DECODE AFTER LOADING LIBZBAR -----------------
from pyzbar.pyzbar import decode

# ----------------- STREAMLIT UI -----------------
st.title("📸 QR Code Scanner & Verification")

scan_option = st.radio("Select Scan Mode:", ["📂 Upload QR Image", "🎥 Use Webcam"])

# ----------------- FUNCTION TO READ QR CODE -----------------
def read_qr_from_image(image):
    np_image = np.array(bytearray(image.read()), dtype=np.uint8)
    img = cv2.imdecode(np_image, cv2.IMREAD_COLOR)
    qr_codes = decode(img)

    if qr_codes:
        return qr_codes[0].data.decode("utf-8")
    return None

def read_qr_from_webcam():
    cap = cv2.VideoCapture(0)

    st.write("**Press 'Q' to Exit the Scanner**")

    while True:
        ret, frame = cap.read()
        if not ret:
            st.error("❌ Error accessing webcam")
            break

        qr_codes = decode(frame)
        for qr in qr_codes:
            qr_data = qr.data.decode("utf-8")
            cap.release()
            cv2.destroyAllWindows()
            return qr_data

        cv2.imshow("QR Code Scanner - Press 'Q' to Exit", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
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
                    if cell:  # Check if the cell was found
                        sheet.update_cell(cell.row, 4, "✅")
                        return f"✅ User Verified: {user_name} (Mobile: {user_mobile})"
                    else:
                        return "❌ Error: ID not found in sheet (after initial verification)." # Handle potential error.

            else:
                return "❌ No user found in the database."

    return "❌ Invalid QR Code Format."

# ----------------- HANDLE SCAN MODES -----------------
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

elif scan_option == "🎥 Use Webcam":
    if st.button("Start Webcam Scanner"):
        qr_result = read_qr_from_webcam()
        if qr_result:
            st.success(f"🔍 QR Code Scanned: {qr_result}")
            verification_result = verify_user(qr_result)
            st.write(verification_result)
        else:
            st.error("❌ No QR Code detected.")
