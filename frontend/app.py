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
    url = f"{BACKEND_URL}{endpoint}"
    kwargs['verify'] = False  # Disable SSL verification
    response = requests.request(method, url, **kwargs)
    return response


# 上傳功能
uploaded_files = st.file_uploader("選擇影像檔案", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])
if uploaded_files:
    if len(uploaded_files) > 100:
        st.error("一次最多只能上傳100張圖片")
    else:
        files = [("files", file) for file in uploaded_files]
        response = make_request('POST', '/upload', files=files)
        if response.status_code == 200:
            st.success(f"成功上傳 {len(uploaded_files)} 張圖片")
        else:
            st.error("上傳失敗")

# 顯示已上傳的圖片列表
st.subheader("已上傳的圖片")
with st.spinner('載入圖片列表...'):
    response = make_request('GET', '/images')
    
    if response and response.status_code == 200:
        images = response.json().get('images', [])
        
        if not images:
            st.info("目前沒有已上傳的圖片")
        else:
            cols = st.columns(3)
            
            for idx, image in enumerate(images):
                col = cols[idx % 3]
                with col:
                    try:

                        img_response = make_request('GET', f"/image/{image['id']}")
                        if img_response and img_response.status_code == 200:

                            img = Image.open(io.BytesIO(img_response.content))
                            st.image(img, caption=image['filename'])
                            

                            buf = io.BytesIO()
                            img.save(buf, format="PNG")
                            st.download_button(
                                label="下載圖片",
                                data=buf.getvalue(),
                                file_name=image['filename'],
                                mime="image/png",
                                key=f"download_{image['id']}"
                            )
                    except Exception as e:
                        logger.error(f"Error processing image {image['id']}: {str(e)}")
                        st.error(f"無法載入圖片: {image['filename']}")
                        
st.sidebar.markdown("---")
st.sidebar.info(f"後端連接: {BACKEND_URL}")