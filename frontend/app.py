import os
import io
import logging
import streamlit as st
import requests
from PIL import Image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BACKEND_URL = os.getenv("BACKEND_URL", "http://10.211.55.1:8000")

st.title("影像上傳與存儲系統")

def make_request(method, endpoint, **kwargs):
    """Helper function to make API requests."""
    url = f"{BACKEND_URL}/{endpoint.lstrip('/')}"
    kwargs["verify"] = False  # Disable SSL verification for local development
    
    try:
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        logger.error(f"API request error: {e}, Response: {getattr(e, 'response', None)}")
        return None


def upload_images(files):
    """Uploads images to the backend."""
    file_data = [("files", (file.name, file, file.type)) for file in files]
    response = make_request("POST", "/upload", files=file_data)
    
    if response:
        st.success(f"成功上傳 {len(files)} 張圖片")
    else:
        st.error("上傳失敗，請檢查後端日誌")

def fetch_image_list():
    """Fetches the list of uploaded images."""
    response = make_request("GET", "/images")
    return response.json().get("images", []) if response else []

def fetch_and_display_image(image_id, filename, col):
    """Fetches an image by ID and displays it in a column."""
    img_response = make_request("GET", f"/image/{image_id}")
    if not img_response:
        st.error(f"無法載入圖片: {filename}")
        return

    try:
        img = Image.open(io.BytesIO(img_response.content))
        col.image(img, caption=filename)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        col.download_button(
            label="下載圖片",
            data=buf.getvalue(),
            file_name=filename,
            mime="image/png",
            key=f"download_{image_id}",
        )
    except Exception as e:
        logger.error(f"Error processing image {image_id}: {str(e)}")
        st.error(f"無法處理圖片: {filename}")

# --- Image Upload Section ---
uploaded_files = st.file_uploader("選擇影像檔案", accept_multiple_files=True, type=["png", "jpg", "jpeg"])
if uploaded_files:
    if len(uploaded_files) > 100:
        st.error("一次最多只能上傳 100 張圖片")
    else:
        upload_images(uploaded_files)

# --- Display Uploaded Images ---
st.subheader("已上傳的圖片")
with st.spinner("載入圖片列表..."):
    images = fetch_image_list()

if not images:
    st.info("目前沒有已上傳的圖片")
else:
    cols = st.columns(3)  # Display images in a 3-column layout
    for idx, image in enumerate(images):
        fetch_and_display_image(image["id"], image["filename"], cols[idx % 3])

# --- Sidebar ---
st.sidebar.markdown("---")
st.sidebar.info(f"後端連接: {BACKEND_URL}")