import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import cv2
import numpy as np
from pyzbar.pyzbar import decode

SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

try:
    creds_json = st.secrets["google_credentials"]
    creds = Credentials.from_service_account_info(creds_json, scopes=SCOPE)
    client = gspread.authorize(creds)

    SHEET_ID = "1I8z27cmHXUB48B6J52_p56elELf2tQVv_K-ra6jf1iQ"
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
    st.error("Google credentials not found in Streamlit secrets.")
    st.stop()
except Exception as e:
    st.error(f"Error loading credentials: {e}")
    st.stop()

st.title("📸 Meloraga Verification")

scan_option = st.radio("Select Scan Mode:", ["📂 Upload QR Image", "📷 Use Camera (Live Scan)"])

def read_qr_from_image(image):
    np_image = np.array(bytearray(image.read()), dtype=np.uint8)
    img = cv2.imdecode(np_image, cv2.IMREAD_COLOR)
    qr_codes = decode(img)

    if qr_codes:
        return qr_codes[0].data.decode("utf-8")
    return None

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
                        return "❌ Error: ID not found in sheet (after initial verification)."

            else:
                return "❌ No user found in the database."

    return "❌ Invalid QR Code Format."

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

elif scan_option == "📷 Use Camera (Live Scan)":
    st.write("**Click the button below to capture a QR Code from your camera.**")

    # Capture image from webcam
    img_file_buffer = st.camera_input("Take a picture")

    if img_file_buffer:
        qr_result = read_qr_from_image(img_file_buffer)

        if qr_result:
            st.success(f"🔍 QR Code Scanned: {qr_result}")
            verification_result = verify_user(qr_result)
            st.write(verification_result)
        else:
            st.error("❌ No QR Code detected in the image.")
