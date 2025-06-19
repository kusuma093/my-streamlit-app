import requests
import streamlit as st
from PIL import Image
import os

st.title("🚘 ระบบตรวจจับภาพ + ประเภทรถ")

image_url = "https://enterprise.garage-pro.net/Images/2024/06/71_1_506188_99_22062024165931.jpg"
image_path = "test_image.jpg"
headers = { "User-Agent": "Mozilla/5.0" }

if not os.path.exists(image_path):
    response = requests.get(image_url, headers=headers, stream=True)
    if response.status_code == 200:
        with open(image_path, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        st.success("✅ ดาวน์โหลดภาพสำเร็จ")
    else:
        st.error(f"❌ โหลดภาพไม่สำเร็จ: {response.status_code}")

st.image(image_path, caption="ภาพตัวอย่าง", use_column_width=True)

car_type_api = "https://express.garage-pro.net/MobileService/GetCarTypes"
try:
    car_type_response = requests.post(car_type_api)
    car_types = car_type_response.json()
    car_type_dict = {item["Text"]: item["Value"] for item in car_types}
    selected_text = st.selectbox("เลือกประเภทรถ:", list(car_type_dict.keys()))
    st.write(f"คุณเลือก: {selected_text} (รหัส: {car_type_dict[selected_text]})")
except Exception as e:
    st.error("❌ ไม่สามารถเชื่อมต่อ API ได้")
    st.exception(e)
