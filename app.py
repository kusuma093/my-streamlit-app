import streamlit as st
import requests
from PIL import Image
from ultralytics import YOLO
import os
import uuid
import pandas as pd

st.set_page_config(page_title="ตรวจจับภาพด้วย AI", layout="centered")
st.title("🚘 ตรวจจับความเสียหายรถด้วย AI")

# ✅ ฟังก์ชันแปลง label ให้อ่านง่าย
def explain_label(label):
    parts = label.split("-")
    if len(parts) == 2:
        area, damage = parts
    elif len(parts) == 3:
        area = f"{parts[0]}-{parts[1]}"
        damage = parts[2]
    else:
        return f"❓ ไม่สามารถแปลความหมายได้: {label}"

    area_thai = {
        "front": "ด้านหน้า",
        "back": "ด้านหลัง",
        "left": "ด้านซ้าย",
        "right": "ด้านขวา",
        "front-left": "ด้านหน้าซ้าย",
        "front-right": "ด้านหน้าขวา",
        "back-left": "ด้านหลังซ้าย",
        "back-right": "ด้านหลังขวา",
    }.get(area, area)

    damage_thai = {
        "0": "ไม่เสียหาย",
        "1": "เสียหายเล็กน้อย",
        "2": "เสียหายปานกลาง",
        "3": "เสียหายรุนแรง",
    }.get(damage, f"ระดับ {damage}")

    return f"{area_thai} - {damage_thai}"

# --- เลือกแหล่งภาพ
option = st.radio("เลือกรูปภาพ:", ["📷 อัปโหลดจากเครื่อง", "🌐 ใช้ URL ของภาพ"])
image_path = None

if option == "📷 อัปโหลดจากเครื่อง":
    uploaded_file = st.file_uploader("เลือกรูปภาพ", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        image_path = f"uploaded_{uuid.uuid4().hex}.jpg"
        with open(image_path, "wb") as f:
            f.write(uploaded_file.read())
        st.image(image_path, caption="ภาพจากเครื่อง", use_container_width=True)
        st.session_state["image_path"] = image_path

elif option == "🌐 ใช้ URL ของภาพ":
    image_url = st.text_input("กรอก URL ของภาพ", "")
    if image_url:
        image_path = f"downloaded_{uuid.uuid4().hex}.jpg"
        try:
            headers = { "User-Agent": "Mozilla/5.0" }
            response = requests.get(image_url, headers=headers, stream=True)
            if response.status_code == 200:
                with open(image_path, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                st.image(image_path, caption="ภาพจาก URL", use_container_width=True)
                st.session_state["image_path"] = image_path
            else:
                st.error(f"โหลดภาพไม่สำเร็จ: {response.status_code}")
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")

# --- โหลดโมเดล YOLO
model_path = "runs/detect/train2/weights/best.pt"
if os.path.exists(model_path):
    model = YOLO(model_path)
else:
    st.error("❌ ไม่พบโมเดล YOLO best.pt")

# --- ปุ่มรัน AI
if "image_path" in st.session_state :
    with st.spinner("⏳ กำลังประมวลผล..."):
        image_path = st.session_state["image_path"]
        results = model.predict(source=image_path, save=True, conf=0.25)
        output_image_path = os.path.join(results[0].save_dir, os.path.basename(image_path))
        st.session_state["results"] = results
        st.session_state["output_image_path"] = output_image_path

# --- แสดงภาพผลลัพธ์
if "output_image_path" in st.session_state:
    st.image(st.session_state["output_image_path"], caption="ผลลัพธ์จาก AI", use_container_width=True)

# --- แสดง label และตรวจจับ front
if "results" in st.session_state:
    results = st.session_state["results"]
    detected_labels = []

    for result in results:
        for box in result.boxes:
            cls_id = int(box.cls[0])
            label = result.names[cls_id]
            conf = float(box.conf[0])
            description = explain_label(label)
            st.write(f"🔍 {description} (ความมั่นใจ {conf*100:.1f}%)")
            detected_labels.append(label)
    
       

    # เช็ค front / back
    front_count = sum(1 for lbl in detected_labels if lbl.startswith("front"))
    back_count = sum(1 for lbl in detected_labels if lbl.startswith("back"))
   
    # ตรวจว่ามี damage level 3 ใน front หรือ back หรือไม่
    severe_damage_detected_front = any(lbl in ["front-3"] for lbl in detected_labels)
    severe_damage_detected_back = any(lbl in ["back-3"] for lbl in detected_labels)
    if front_count > 1 or back_count > 1 or severe_damage_detected_front or severe_damage_detected_back:
        #st.success(f"✅ ตรวจพบวัตถุด้านหน้า {front_count} และด้านหลัง {back_count}")

        # --- API: ประเภทรถ
        car_type_api = "https://express.garage-pro.net/MobileService/GetCarTypes"
        try:
            car_type_response = requests.post(car_type_api)
            car_types = car_type_response.json()
            car_type_dict = {item["Text"]: item["Value"] for item in car_types}

            selected_text = st.selectbox("เลือกประเภทรถ:", list(car_type_dict.keys()))
            selected_value = int(car_type_dict[selected_text])

            # --- เงื่อนไขเฉพาะ
            name = ""
            if selected_value == 12 and (back_count > 1 or severe_damage_detected_back):
                custom_template_id = 124
                name = "ชนท้ายเต็ม"
            elif selected_value == 12 and (front_count > 1 or severe_damage_detected_front):
                custom_template_id = 29
                name = "ชนหน้าเต็ม"
            elif selected_value == 19 and (back_count > 1 or severe_damage_detected_back):
                custom_template_id = 177
                name = "ชนท้ายเต็ม"
            elif selected_value == 19 and (front_count > 1 or severe_damage_detected_front):
                custom_template_id = 30
                name = "ชนหน้าเต็ม"
            else:
                st.info("🚫 ยังไม่มีข้อมูลอะไหล่สำหรับประเภทรถนี้")
                custom_template_id = None

            # --- เรียก API อะไหล่ถ้ามี custom_template_id
            if custom_template_id:
                gps_api = "https://express.garage-pro.net/MobileService/GetCustomTemplateGPSCode"
                headers = { "Content-Type": "application/json" }
                payload = { "customTemplateId": custom_template_id }

                gps_response = requests.post(gps_api, headers=headers, json=payload)
                if gps_response.status_code == 200:
                    gps_data = gps_response.json()
                    if isinstance(gps_data, list) and len(gps_data) > 0:
                        df = pd.DataFrame(gps_data)
                        st.subheader("📋 รายการอะไหล่ (จาก GPS Code) {name}")
                        st.dataframe(df[["GPSCode", "GPSName", "GPSSpecial"]])
                    else:
                        st.warning("ไม่พบรายการอะไหล่สำหรับประเภทนี้")
                else:
                    st.error(f"เรียก API GPS ไม่สำเร็จ: {gps_response.status_code}")
        except Exception as e:
            st.error("❌ เกิดข้อผิดพลาดขณะดึงข้อมูลประเภทรถ")
            st.exception(e)
    elif (front_count > 0 or back_count > 0 ) and (len(detected_labels) > 0):
        st.warning(f"⚠️ ตรวจพบวัตถุด้านหน้า {front_count} หรือด้านหลัง {back_count} แต่ไม่เพียงพอสำหรับการแสดงประเภทรถ")
    else:
        st.warning("⚠️ ไม่พบวัตถุใด ๆ ในภาพที่สามารถตรวจจับได้")
