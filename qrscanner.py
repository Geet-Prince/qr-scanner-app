import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import cv2
import numpy as np
import ctypes
from pyzbar.pyzbar import decode
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import av

# ----------------- GOOGLE SHEETS SETUP -----------------
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

try:
    creds_json = st.secrets["google_credentials"]
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
    st.error("Google credentials secret 'google_credentials' not found. Set up the secret in Streamlit Cloud.")
    st.stop()
except Exception as e:
    st.error(f"Error loading credentials: {e}")
    st.stop()

# ----------------- Load libzbar -----------------
try:
    libzbar_path = "/usr/lib/x86_64-linux-gnu/libzbar.so.0"
    libzbar = ctypes.CDLL(libzbar_path)
except OSError as e:
    st.error(f"Error loading libzbar: {e}")
    st.stop()

# ----------------- Streamlit UI -----------------
st.title("📸 QR Code Scanner & Verification")

scan_option = st.radio("Select Scan Mode:", ["📂 Upload QR Image", "📷 Live Camera"])

# ----------------- Function to Read QR Code from Image -----------------
def read_qr_from_image(image):
    np_image = np.array(bytearray(image.read()), dtype=np.uint8)
    img = cv2.imdecode(np_image, cv2.IMREAD_COLOR)
    qr_codes = decode(img)

    if qr_codes:
        return qr_codes[0].data.decode("utf-8")
    return None

# ----------------- Function to Verify QR Code in Google Sheet -----------------
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

# ----------------- Streamlit WebRTC Transformer Class -----------------
class VideoTransformer(VideoTransformerBase):
    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        qr_codes = decode(img)

        for qr in qr_codes:
            qr_data = qr.data.decode("utf-8")
            rect = qr.rect
            cv2.rectangle(img, (rect.left, rect.top), (rect.left + rect.width, rect.top + rect.height), (0, 255, 0), 3)

            # Verify QR code
            verification_result = verify_user(qr_data)
            st.session_state["qr_result"] = qr_data
            st.session_state["verification_result"] = verification_result

        return av.VideoFrame.from_ndarray(img, format="bgr24")

# ----------------- Handle Scan Modes -----------------
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

elif scan_option == "📷 Live Camera":
    webrtc_ctx = webrtc_streamer(
        key="qr-scanner",
        video_transformer_factory=VideoTransformer,
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
    )

    if "qr_result" in st.session_state:
        st.success(f"🔍 QR Code Scanned: {st.session_state['qr_result']}")
        st.write(st.session_state["verification_result"])
