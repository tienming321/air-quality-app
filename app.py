import streamlit as st
import requests

API_KEY = "f36c96983d5b0f6d25655f5415769f1a"

st.set_page_config(page_title="Air Quality Assistant", page_icon="🌱")
st.title("🌱 Trợ Lý Cảnh Báo Chất Lượng Không Khí")
st.write("Tra cứu thời tiết & chỉ số ô nhiễm không khí (AQI) chi tiết theo Cấp Phường / Xã / Quận.")

# Chia 3 cột nhập thông tin hành chính
col_city, col_dist, col_ward = st.columns(3)

with col_city:
    city = st.selectbox("Thành phố / Tỉnh:", ["Hà Nội", "TP. Hồ Chí Minh", "Đà Nẵng", "Hải Phòng", "Cần Thơ"])

with col_dist:
    district = st.text_input("Quận / Huyện (VD: Cầu Giấy):", "")

with col_ward:
    ward = st.text_input("Phường / Xã (VD: Dịch Vọng):", "")

if st.button("Tra cứu chi tiết"):
    # Tạo chuỗi địa chỉ đầy đủ
    address_parts = [p.strip() for p in [ward, district, city, "Vietnam"] if p.strip()]
    full_address = ", ".join(address_parts)
    
    # Bước 1: Chuyển đổi Địa chỉ -> Tọa độ (Geocoding qua OpenStreetMap)
    geo_url = f"https://nominatim.openstreetmap.org/search?q={full_address}&format=json"
    headers = {"User-Agent": "AirQualityApp/1.0"}
    
    res_geo = requests.get(geo_url, headers=headers).json()
    
    if res_geo:
        lat = res_geo[0]['lat']
        lon = res_geo[0]['lon']
        display_name = res_geo[0]['display_name']
        
        # Bước 2: Gọi OpenWeatherMap lấy Thời tiết & AQI theo tọa độ lat, lon
        url_weather = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=vi"
        url_aqi = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
        
        res_w = requests.get(url_weather).json()
        res_aqi = requests.get(url_aqi).json()
        
        st.success(f"📍 Đã định vị tọa độ: {lat}, {lon}")
        st.caption(f"Địa chỉ nhận diện: {display_name}")
        
        # Bước 3: Hiển thị kết quả
        col1, col2, col3 = st.columns(3)
        col1.metric("Nhiệt độ", f"{res_w['main']['temp']} °C")
        col2.metric("Độ ẩm", f"{res_w['main']['humidity']} %")
        
        aqi = res_aqi['list'][0]['main']['aqi']
        pm25 = res_aqi['list'][0]['components']['pm2_5']
        col3.metric("Mức AQI", f"{aqi}/5")
        
        st.warning(f"Nồng độ bụi mịn PM2.5: {pm25} µg/m³")
    else:
        st.error("Không tìm thấy tọa độ địa lý. Vui lòng kiểm tra lại tên Phường/Quận.")
