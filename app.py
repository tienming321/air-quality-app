..import streamlit as st
import requests

# Khai báo API Key
API_KEY = "f36c96983d5b0f6d25655f5415769f1a"

st.set_page_config(page_title="Air Quality Assistant", page_icon="🌱")
st.title("🌱 Trợ Lý Cảnh Báo Chất Lượng Không Khí")
st.write("Tra cứu chỉ số thời tiết & ô nhiễm không khí (AQI) theo thời gian thực.")

city = st.text_input("Nhập tên thành phố (VD: Hanoi, Ho Chi Minh, Danang):", "")

if st.button("Tra cứu"):
    if city:
        # Đường dẫn API thời tiết (Đã sửa lại {API_KEY} ở đây)
        url_weather = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric&lang=vi"
        res_w = requests.get(url_weather)
        
        if res_w.status_code == 200:
            data_w = res_w.json()
            lat = data_w['coord']['lat']
            lon = data_w['coord']['lon']
            
            # Đường dẫn API chỉ số ô nhiễm AQI
            url_aqi = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
            data_aqi = requests.get(url_aqi).json()
            aqi = data_aqi['list'][0]['main']['aqi']
            pm25 = data_aqi['list'][0]['components']['pm2_5']
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Nhiệt độ", f"{data_w['main']['temp']} °C")
            col2.metric("Độ ẩm", f"{data_w['main']['humidity']} %")
            col3.metric("Mức AQI", f"{aqi}/5")
            
            st.warning(f"Nồng độ bụi mịn PM2.5: {pm25} µg/m³")
        else:
            st.error("Không tìm thấy thông tin thành phố!")
    else:
        st.info("Vui lòng nhập tên thành phố.")
