import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, RTCConfiguration
import cv2
import numpy as np
from pyzbar.pyzbar import decode
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Google Sheets Setup
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDENTIALS_FILE = "path-to-your-google-credentials.json"  # Replace with your credentials file path
SPREADSHEET_NAME = "your-spreadsheet-name"  # Replace with your Google Sheet name

credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPE)
client = gspread.authorize(credentials)
sheet = client.open(SPREADSHEET_NAME).sheet1  # Use the first sheet

# Streamlit UI
st.title("📸 QR Code Scanner & Verification")

# Camera selection option
camera_option = st.radio("Select Camera", ["Back Camera", "Front Camera"])
camera_facing_mode = "environment" if camera_option == "Back Camera" else "user"

rtc_configuration = RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]})

class QRScanner(VideoTransformerBase):
    def __init__(self):
        self.last_detected = ""

    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        decoded_objects = decode(img)

        for obj in decoded_objects:
            qr_data = obj.data.decode("utf-8")
            self.last_detected = qr_data

            # Draw bounding box around QR code
            points = obj.polygon
            if len(points) == 4:
                pts = np.array([(p.x, p.y) for p in points], dtype=np.int32)
                cv2.polylines(img, [pts], isClosed=True, color=(0, 255, 0), thickness=3)

        return img

# WebRTC Scanner with Camera Switching
ctx = webrtc_streamer(
    key="qr-scanner",
    mode="live",
    rtc_configuration=rtc_configuration,
    video_transformer_factory=QRScanner,
    media_stream_constraints={"video": {"facingMode": camera_facing_mode}, "audio": False},
)

if ctx.video_transformer and ctx.video_transformer.last_detected:
    scanned_qr = ctx.video_transformer.last_detected
    st.success(f"✅ QR Code Scanned: {scanned_qr}")

    # Check in Google Sheet
    records = sheet.get_all_records()
    ids = [str(record["ID"]) for record in records]

    if scanned_qr in ids:
        st.success("🎉 QR Code Verified! User Found in Database.")
    else:
        st.error("⚠️ QR Code Not Found in Database.")

