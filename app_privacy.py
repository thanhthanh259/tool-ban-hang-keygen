import streamlit as st
import extra_streamlit_components as stx
from PIL import Image, ExifTags, ImageOps
from PIL.ExifTags import TAGS, GPSTAGS
from pillow_heif import register_heif_opener
import io
import pandas as pd
import time

# --- CẤU HÌNH ---
VALID_CODES = ["VIP-2026", "ADMIN-888"]
register_heif_opener()
st.set_page_config(page_title="EZ-Protect Pro", page_icon="🛡️")

# --- CSS ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; background-color: #ff4b4b; color: white; height: 3em; font-weight: bold; }
    .vip-badge { padding: 5px 10px; background-color: #f1c40f; color: black; border-radius: 15px; font-weight: bold; }
    .trial-badge { padding: 5px 10px; background-color: #2ecc71; color: white; border-radius: 15px; font-weight: bold; }
    .paywall-box { border: 2px dashed #ff4b4b; background-color: #fff0f0; padding: 20px; border-radius: 10px; text-align: center; }
    .danger-box { padding: 10px; background-color: #ffebee; border-left: 5px solid #f44336; color: #c62828; margin-bottom: 10px; }
    .warning-box { padding: 10px; background-color: #fff3e0; border-left: 5px solid #ff9800; color: #ef6c00; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)


# --- COOKIE MANAGER ---
def get_manager():
    return stx.CookieManager()


cookie_manager = get_manager()


# --- HÀM XỬ LÝ (GIỮ NGUYÊN) ---
def get_lat_lon(gps_info):
    def convert(value):
        try:
            d = float(value[0]);
            m = float(value[1]);
            s = float(value[2])
            return d + (m / 60.0) + (s / 3600.0)
        except:
            return 0.0

    try:
        lat = convert(gps_info.get(2))
        if gps_info.get(1) != 'N': lat = -lat
        lon = convert(gps_info.get(4))
        if gps_info.get(3) != 'E': lon = -lon
        return lat, lon
    except:
        return None, None


def scan_image(image):
    info = {"device": "Không xác định", "date": "Không xác định", "has_gps": False, "lat": None, "lon": None}
    try:
        exif = image.getexif()
        if not exif: return info
        for k, v in exif.items():
            tag = TAGS.get(k, k)
            if tag == 'Model':
                info['device'] = str(v)
            elif tag == 'DateTimeOriginal':
                info['date'] = str(v)
        gps = exif.get_ifd(34853)
        if gps:
            lat, lon = get_lat_lon(gps)
            if lat and lon:
                info['has_gps'] = True;
                info['lat'] = lat;
                info['lon'] = lon
    except:
        pass
    return info


def clean_image_data(img):
    try:
        fixed = ImageOps.exif_transpose(img)
    except:
        fixed = img
    if fixed.mode in ("RGBA", "P"): fixed = fixed.convert("RGB")
    buf = io.BytesIO()
    fixed.save(buf, format='JPEG', quality=100)
    buf.seek(0)
    return buf


# --- GIAO DIỆN CHÍNH ---
def main():
    st.title("🛡️ EZ-Protect")

    # Lấy Cookie
    trial_status = cookie_manager.get(cookie="ez_trial_status")
    vip_status = cookie_manager.get(cookie="ez_vip_status")

    is_vip = (vip_status == "true")
    is_trial_used = (trial_status == "done")

    # Header
    if is_vip:
        st.markdown('<span class="vip-badge">👑 VIP MEMBER</span>', unsafe_allow_html=True)
        if st.button("Đăng xuất", key="logout"):
            cookie_manager.delete("ez_vip_status")
            st.rerun()
    elif not is_trial_used:
        st.markdown('<span class="trial-badge">⚡ DÙNG THỬ MIỄN PHÍ</span>', unsafe_allow_html=True)

    st.divider()

    # Logic chặn
    if not is_vip and is_trial_used:
        show_paywall()
    else:
        show_uploader(is_vip)


def show_uploader(is_vip):
    uploaded_file = st.file_uploader("Upload ảnh (JPG/PNG/HEIC)", type=['jpg', 'png', 'heic'])

    if uploaded_file:
        try:
            image = Image.open(uploaded_file)
            st.image(image, caption="Ảnh gốc", use_container_width=True)

            # Quét ảnh
            data = scan_image(image)

            st.divider()
            st.subheader("🔍 PHÂN TÍCH RỦI RO:")

            # --- PHẦN HIỂN THỊ CHI TIẾT ĐỂ "DỌA" KHÁCH ---

            # 1. Hiển thị thông tin máy & ngày giờ
            c1, c2 = st.columns(2)

            # Kiểm tra nếu đọc được tên máy thì hiện cảnh báo
            if data['device'] != "Không xác định":
                c1.markdown(f"""
                <div class="warning-box">
                    <b>📱 LỘ THIẾT BỊ:</b><br>{data['device']}
                </div>
                """, unsafe_allow_html=True)
            else:
                c1.info("📱 Thiết bị: Ẩn")

            if data['date'] != "Không xác định":
                c2.markdown(f"""
                <div class="warning-box">
                    <b>🕒 LỘ THỜI GIAN:</b><br>{data['date']}
                </div>
                """, unsafe_allow_html=True)
            else:
                c2.info("🕒 Thời gian: Ẩn")

            # 2. Hiển thị GPS (Phần quan trọng nhất)
            if data['has_gps']:
                st.markdown(f"""
                <div class="danger-box">
                    <b>🚨 RỦI RO CAO: LỘ VỊ TRÍ NHÀ RIÊNG!</b><br>
                    Tọa độ: {data['lat']}, {data['lon']}
                </div>
                """, unsafe_allow_html=True)
                # Vẽ bản đồ
                st.map(pd.DataFrame({'lat': [data['lat']], 'lon': [data['lon']]}))
            else:
                st.success("✅ Vị trí: An toàn (Không tìm thấy GPS)")

            st.divider()

            # Nút xử lý
            if st.button("✨ XÓA SẠCH DẤU VẾT & TẢI VỀ"):
                clean_buf = clean_image_data(image)

                st.success("ĐÃ XỬ LÝ XONG! Ảnh của bạn giờ đã an toàn 100%.")

                # Nút tải
                st.download_button("⬇️ Tải ảnh sạch", clean_buf, "safe_image.jpg", "image/jpeg")

                # Ghi cookie chặn nếu không phải VIP
                if not is_vip:
                    cookie_manager.set("ez_trial_status", "done", key="set_trial", expires_at=None)
                    st.toast("Đã hết lượt dùng thử! Chuyển hướng sau 3s...")
                    time.sleep(3)
                    st.rerun()

        except Exception as e:
            st.error(f"Lỗi: {e}")


def show_paywall():
    st.markdown("""
        <div class='paywall-box'>
            <h3>⛔ CẢNH BÁO BẢO MẬT</h3>
            <p>Bạn đã sử dụng hết lượt miễn phí.</p>
            <p>Để tiếp tục bảo vệ thông tin cá nhân, vui lòng kích hoạt bản quyền.</p>
            <hr>
            <p>💰 Phí trọn đời: <b>20.000đ</b></p>
            <p>👉 Zalo Admin: <b>0931.458.778</b></p>
        </div>
    """, unsafe_allow_html=True)

    code = st.text_input("🔑 Nhập Code kích hoạt:", type="password")
    if st.button("MỞ KHÓA NGAY"):
        if code in VALID_CODES:
            cookie_manager.set("ez_vip_status", "true", key="set_vip")
            st.success("Mã đúng! Đang mở khóa...")
            time.sleep(1)
            st.rerun()
        else:
            st.error("Mã không đúng!")


if __name__ == "__main__":
    main()