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
        res = requests.get("https://provinces.open-api.vn/api/p/", timeout=5)
        if res.status_code == 200:
            return res.json()
    except:
        pass
    return []

@st.cache_data
def get_districts(province_code):
    try:
        res = requests.get(f"https://provinces.open-api.vn/api/p/{province_code}?depth=2", timeout=5)
        if res.status_code == 200:
            return res.json().get('districts', [])
    except:
        pass
    return []

@st.cache_data
def get_wards(district_code):
    try:
        res = requests.get(f"https://provinces.open-api.vn/api/d/{district_code}?depth=2", timeout=5)
        if res.status_code == 200:
            return res.json().get('wards', [])
    except:
        pass
    return []

# --- 1. Lấy danh sách Tỉnh / Thành phố ---
provinces = get_provinces()

if provinces:
    province_map = {p['name']: p['code'] for p in provinces}
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_province = st.selectbox("Thành phố / Tỉnh:", list(province_map.keys()))
        province_code = province_map[selected_province]
    
    # --- 2. Lấy danh sách Quận / Huyện ---
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
            
    # --- 3. Lấy danh sách Phường / Xã ---
    wards = get_wards(district_code) if district_code else []
    ward_names = [w['name'] for w in wards] if wards else []
    
    with col3:
        if ward_names:
            selected_ward = st.selectbox("Phường / Xã:", ward_names)
        else:
            selected_ward = ""
            st.selectbox("Phường / Xã:", ["Không có dữ liệu"])

    if st.button("Tra cứu chi tiết"):
        # Thử tìm kiếm theo cấp độ từ Phường -> Quận -> Thành phố nếu địa chỉ quá chi tiết
        search_queries = [
            f"{selected_ward}, {selected_district}, {selected_province}, Vietnam",
            f"{selected_district}, {selected_province}, Vietnam",
            f"{selected_province}, Vietnam"
        ]
        
        lat, lon, display_name = None, None, None
        headers = {"User-Agent": "AirQualityAssistantApp/2.0 (student_academic_project)"}
        
        for query in search_queries:
            geo_url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json"
            try:
                res_geo = requests.get(geo_url, headers=headers, timeout=5)
                if res_geo.status_code == 200 and res_geo.headers.get('content-type', '').startswith('application/json'):
                    data_geo = res_geo.json()
                    if data_geo:
                        lat = data_geo[0]['lat']
                        lon = data_geo[0]['lon']
                        display_name = data_geo[0]['display_name']
                        break
            except Exception:
                continue
        
        if lat and lon:
            try:
                url_weather = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=vi"
                url_aqi = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
                
                res_w_resp = requests.get(url_weather, timeout=5)
                res_aqi_resp = requests.get(url_aqi, timeout=5)
                
                if res_w_resp.status_code == 200 and res_aqi_resp.status_code == 200:
                    res_w = res_w_resp.json()
                    res_aqi = res_aqi_resp.json()
                    
                    st.success(f"📍 Đã định vị tọa độ: {lat}, {lon}")
                    st.caption(f"Địa chỉ nhận diện: {display_name}")
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Nhiệt độ", f"{res_w['main']['temp']} °C")
                    c2.metric("Độ ẩm", f"{res_w['main']['humidity']} %")
                    
                    aqi = res_aqi['list'][0]['main']['aqi']
                    pm25 = res_aqi['list'][0]['components']['pm2_5']
                    c3.metric("Mức AQI", f"{aqi}/5")
                    
                    st.warning(f"Nồng độ bụi mịn PM2.5: {pm25} µg/m³")
                else:
                    st.error("Không thể kết nối API thời tiết. Vui lòng kiểm tra lại chìa khóa API.")
            except Exception as e:
                st.error(f"Lỗi xử lý dữ liệu: {e}")
        else:
            st.error("Không định vị được bản đồ cho địa điểm này. Vui lòng thử lại sau giây lát.")
else:
    st.error("Không thể tải danh sách Tỉnh/Thành phố. Vui lòng nhấn F5 để tải lại.")
