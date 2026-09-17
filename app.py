import streamlit as st
import requests

API_KEY = "f36c96983d5b0f6d25655f5415769f1a"

st.set_page_config(page_title="Air Quality Assistant", page_icon="🌱")
st.title("🌱 Trợ Lý Cảnh Báo Chất Lượng Không Khí")
st.write("Tra cứu thời tiết & chỉ số ô nhiễm không khí (AQI) chi tiết theo Cấp Phường / Xã / Quận.")

# --- Dùng Cache để tối ưu tốc độ gọi API Tỉnh Thành ---
@st.cache_data
def get_provinces():
    try:
        res = requests.get("https://provinces.open-api.vn/api/p/")
        return res.json() if res.status_code == 200 else []
    except:
        return []

@st.cache_data
def get_districts(province_code):
    try:
        res = requests.get(f"https://provinces.open-api.vn/api/p/{province_code}?depth=2")
        return res.json().get('districts', []) if res.status_code == 200 else []
    except:
        return []

@st.cache_data
def get_wards(district_code):
    try:
        res = requests.get(f"https://provinces.open-api.vn/api/d/{district_code}?depth=2")
        return res.json().get('wards', []) if res.status_code == 200 else []
    except:
        return []

# --- 1. Lấy danh sách Tỉnh / Thành phố ---
provinces = get_provinces()

if provinces:
    province_map = {p['name']: p['code'] for p in provinces}
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_province = st.selectbox("Thành phố / Tỉnh:", list(province_map.keys()))
        province_code = province_map[selected_province]
    
    # --- 2. Lấy danh sách Quận / Huyện dựa trên Tỉnh đã chọn ---
    districts = get_districts(province_code)
    district_map = {d['name']: d['code'] for d in districts} if districts else {}
    
    with col2:
        if district_map:
            selected_district = st.selectbox("Quận / Huyện:", list(district_map.keys()))
            district_code = district_map[selected_district]
        else:
            selected_district = ""
            district_code = None
            st.selectbox("Quận / Huyện:", ["Không có dữ liệu"])
            
    # --- 3. Lấy danh sách Phường / Xã dựa trên Quận đã chọn ---
    wards = get_wards(district_code) if district_code else []
    ward_names = [w['name'] for w in wards] if wards else []
    
    with col3:
        if ward_names:
            selected_ward = st.selectbox("Phường / Xã:", ward_names)
        else:
            selected_ward = ""
            st.selectbox("Phường / Xã:", ["Không có dữ liệu"])

    if st.button("Tra cứu chi tiết"):
        # Ghép chuỗi địa chỉ đầy đủ
        address_parts = [p for p in [selected_ward, selected_district, selected_province, "Vietnam"] if p]
        full_address = ", ".join(address_parts)
        
        # Bước 1: Chuyển đổi Địa chỉ -> Tọa độ (Geocoding qua OpenStreetMap)
        geo_url = f"https://nominatim.openstreetmap.org/search?q={full_address}&format=json"
        headers = {"User-Agent": "AirQualityApp/1.0"}
        
        try:
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
                c1, c2, c3 = st.columns(3)
                c1.metric("Nhiệt độ", f"{res_w['main']['temp']} °C")
                c2.metric("Độ ẩm", f"{res_w['main']['humidity']} %")
                
                aqi = res_aqi['list'][0]['main']['aqi']
                pm25 = res_aqi['list'][0]['components']['pm2_5']
                c3.metric("Mức AQI", f"{aqi}/5")
                
                st.warning(f"Nồng độ bụi mịn PM2.5: {pm25} µg/m³")
            else:
                st.error("Không tìm thấy tọa độ địa lý. Vui lòng chọn địa điểm khác.")
        except Exception as e:
            st.error(f"Có lỗi xảy ra khi kết nối dữ liệu: {e}")
else:
    st.error("Không thể tải danh sách Tỉnh/Thành phố. Vui lòng làm mới lại trang.")
