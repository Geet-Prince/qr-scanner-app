import streamlit as st
import cv2
import numpy as np
import av
from pyzbar.pyzbar import decode
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ✅ Load Google Sheet Credentials
CREDENTIALS_FILE = "your_google_credentials.json"  # Update with your JSON key file path
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

try:
    credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPE)
    client = gspread.authorize(credentials)
    sheet = client.open("Your_Google_Sheet_Name").worksheet("Sheet1")  # Update with your sheet name
    data = sheet.get_all_records()
except Exception as e:
    st.error("❌ Google Sheets Authentication Failed. Check Credentials.")
    data = []

# ✅ UI Design
st.markdown("<h1 style='text-align: center;'>📸 QR Code Scanner & Verification</h1>", unsafe_allow_html=True)
st.markdown("### **Select Scan Mode:**")
scan_mode = st.radio(" ", ["📂 Upload QR Image", "📹 Use Camera (Live Scan)"])

# ✅ Camera Selection (for Mobile Support)
if scan_mode == "📹 Use Camera (Live Scan)":
    st.markdown("### **Choose Camera:**")
    camera_option = st.radio(" ", ["📹 Back Camera", "🤳 Front Camera"], index=0)

# ✅ QR Code Scanner Class
class QRScanner(VideoTransformerBase):
    def __init__(self):
        self.qr_data = None

    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")

        print("🔵 Camera Frame Received")  # Debugging

        qr_codes = decode(img)
        if qr_codes:
            for qr in qr_codes:
                self.qr_data = qr.data.decode("utf-8")
                print(f"✅ QR Code Found: {self.qr_data}")

                pts = np.array(qr.polygon, np.int32).reshape((-1, 1, 2))
                cv2.polylines(img, [pts], True, (0, 255, 0), 3)
                cv2.putText(img, self.qr_data, (qr.rect.left, qr.rect.top - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        return av.VideoFrame.from_ndarray(img, format="bgr24")

# ✅ Process Live Camera Input
if scan_mode == "📹 Use Camera (Live Scan)":
    ctx = webrtc_streamer(
        key="qr-scanner",
        video_transformer_factory=QRScanner,
        async_transform=True,
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
        media_stream_constraints={
            "video": {
                "width": {"ideal": 640},
                "height": {"ideal": 480},
                "frameRate": {"ideal": 24},
                "facingMode": {"ideal": "environment" if camera_option == "📹 Back Camera" else "user"}
            },
            "audio": False
        }
    )

    if ctx.video_transformer:
        qr_result = ctx.video_transformer.qr_data
        if qr_result:
            st.success(f"✅ QR Code Scanned: {qr_result}")

            # ✅ Check QR Code in Google Sheet
            ids = [str(row["ID"]) for row in data]
            if qr_result in ids:
                st.success("✅ Verified in Google Sheet!")
            else:
                st.warning("⚠️ No matching user found!")

# ✅ Upload QR Image Option
elif scan_mode == "📂 Upload QR Image":
    uploaded_file = st.file_uploader("Upload QR Code Image", type=["png", "jpg", "jpeg"])
    if uploaded_file:
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        qr_codes = decode(img)

        if qr_codes:
            for qr in qr_codes:
                qr_data = qr.data.decode("utf-8")
                st.success(f"✅ QR Code Scanned: {qr_data}")

                # ✅ Check QR Code in Google Sheet
                ids = [str(row["ID"]) for row in data]
                if qr_data in ids:
                    st.success("✅ Verified in Google Sheet!")
                else:
                    st.warning("⚠️ No matching user found!")
        else:
            st.error("❌ No QR code detected.")
