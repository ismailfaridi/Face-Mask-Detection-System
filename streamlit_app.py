import streamlit as st
import sys
import io
import numpy as np
from PIL import Image

# Make the detector module importable
sys.path.append('app/services')
from detector import DetectionSystem


st.set_page_config(page_title="Face Mask Detector", page_icon="😷", layout="wide")

@st.cache_resource
def load_system():
    return DetectionSystem()

system = load_system()

st.title("😷 Face Mask Detection System")
st.caption("Powered by MediaPipe + MobileNetV2")


# Image Upload
uploaded_file = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image_bytes = uploaded_file.read()

    with st.spinner("Running detection..."):
        annotated_bytes, status, conf, db_path, total_faces, masks_count = \
            system.uploadImage(image_bytes)

    if total_faces == 0:
        st.warning("No faces detected in the image.")
    else:
        # Two-column layout: annotated image on left, summary on right
        col_img, col_summary = st.columns([2, 1], gap="large")

        with col_img:
            result_img = Image.open(io.BytesIO(annotated_bytes))
            # Cap the displayed width so huge images don't fill the canvas
            st.image(result_img, caption="Detection Result", width=600)

        with col_summary:
            st.subheader("Detection Summary")

            c1, c2, c3 = st.columns(3)
            c1.metric("Faces", total_faces)
            c2.metric("Mask", masks_count)
            c3.metric("No Mask", total_faces - masks_count)

            st.metric("Confidence", f"{conf:.2f}%")

            st.divider()

            if status == "No Mask":
                st.error("⚠️ At least one person is not wearing a mask.")
            else:
                st.success("✅ All detected faces are wearing masks.")