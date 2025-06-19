import requests
import streamlit as st
from PIL import Image
import os
import pandas as pd

st.title("🚘 ระบบตรวจจับภาพ + ประเภทรถ")

# --- ดาวน์โหลดภาพ
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

st.image(image_path, caption="ภาพตัวอย่าง", use_container_width=True)

# --- ดึงรายการประเภทรถ
car_type_api = "https://express.garage-pro.net/MobileService/GetCarTypes"
try:
    car_type_response = requests.post(car_type_api)
    car_types = car_type_response.json()
    car_type_dict = {item["Text"]: item["Value"] for item in car_types}
    selected_text = st.selectbox("เลือกประเภทรถ:", list(car_type_dict.keys()))
    selected_value = car_type_dict[selected_text]
    st.write(f"คุณเลือก: {selected_text} (รหัส: {selected_value})")

    # --- เรียก API GetCustomTemplateGPSCode หลังเลือกประเภทรถ
    gps_api = "https://express.garage-pro.net/MobileService/GetCustomTemplateGPSCode"
    headers = { "Content-Type": "application/json" }
    payload = {
        "customTemplateId": int(193)  # ใช้รหัสประเภทรถเป็น customTemplateId
    }

    gps_response = requests.post(gps_api, headers=headers, json=payload)
    if gps_response.status_code == 200:
        gps_data = gps_response.json()

        if isinstance(gps_data, list) and len(gps_data) > 0:
            df = pd.DataFrame(gps_data)
            st.subheader("📋 รายการอะไหล่ (จาก GPS Code)")
            st.dataframe(df[["GPSCode", "GPSName", "GPSSpecial", "GPSPositionId"]])
        else:
            st.warning("ไม่พบรายการ GPS Code สำหรับประเภทรถนี้")
    else:
        st.error(f"ไม่สามารถเรียก API GPS ได้: {gps_response.status_code}")

except Exception as e:
    st.error("❌ เกิดข้อผิดพลาดในการเชื่อมต่อ API")
    st.exception(e)
