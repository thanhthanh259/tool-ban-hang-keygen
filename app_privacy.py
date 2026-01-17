import streamlit as st
import extra_streamlit_components as stx
from PIL import Image, ExifTags, ImageOps
from PIL.ExifTags import TAGS, GPSTAGS
from pillow_heif import register_heif_opener
import io
import pandas as pd
import time

# --- CẤU HÌNH ---
VALID_CODES = ["AITHANHAI-2026", "ADMIN-888"]
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

# --- KHỞI TẠO SESSION STATE (QUAN TRỌNG ĐỂ SỬA LỖI) ---
if 'processed_buffer' not in st.session_state:
    st.session_state.processed_buffer = None  # Lưu ảnh đã xử lý để không bị mất
if 'temp_vip' not in st.session_state:
    st.session_state.temp_vip = False  # Mở khóa tạm thời ngay lập tức


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

    # 1. Lấy trạng thái từ Cookie
    trial_status = cookie_manager.get(cookie="ez_trial_status")
    vip_cookie = cookie_manager.get(cookie="ez_vip_status")

    # Logic kiểm tra VIP: Ưu tiên Session tạm thời (để mở ngay lập tức) hoặc Cookie (cho lần sau)
    is_vip = (vip_cookie == "true") or st.session_state.temp_vip
    is_trial_used = (trial_status == "done")

    # Header
    if is_vip:
        st.markdown('<span class="vip-badge">👑 VIP MEMBER</span>', unsafe_allow_html=True)
        if st.button("Đăng xuất", key="logout"):
            cookie_manager.delete("ez_vip_status")
            st.session_state.temp_vip = False
            st.session_state.processed_buffer = None
            st.rerun()
    elif not is_trial_used:
        st.markdown('<span class="trial-badge">⚡ DÙNG THỬ MIỄN PHÍ (1 ẢNH)</span>', unsafe_allow_html=True)

    st.divider()

    # Logic chặn: Chỉ chặn khi ĐÃ HẾT THỬ và CHƯA CÓ KẾT QUẢ XỬ LÝ (để cho khách tải xong đã)
    # Nếu khách đang có ảnh đã xử lý (processed_buffer) thì vẫn cho hiện để tải
    if not is_vip and is_trial_used and st.session_state.processed_buffer is None:
        show_paywall()
    else:
        show_uploader(is_vip)


def show_uploader(is_vip):
    # Key của file_uploader giúp reset khi cần
    uploaded_file = st.file_uploader("Upload ảnh (JPG/PNG/HEIC)", type=['jpg', 'png', 'heic'], key="uploader")

    if uploaded_file:
        # Nếu upload ảnh mới -> Xóa kết quả cũ đi
        # (Cách nhận biết ảnh mới: Streamlit sẽ chạy lại từ đầu)
        # Tuy nhiên để đơn giản, ta chỉ hiển thị kết quả nếu nó khớp

        try:
            image = Image.open(uploaded_file)
            st.image(image, caption="Ảnh gốc", use_container_width=True)

            data = scan_image(image)

            st.divider()
            st.subheader("🔍 PHÂN TÍCH RỦI RO:")

            c1, c2 = st.columns(2)
            if data['device'] != "Không xác định":
                c1.markdown(f"""<div class="warning-box"><b>📱 LỘ THIẾT BỊ:</b><br>{data['device']}</div>""",
                            unsafe_allow_html=True)
            else:
                c1.info("📱 Thiết bị: Ẩn")

            if data['date'] != "Không xác định":
                c2.markdown(f"""<div class="warning-box"><b>🕒 LỘ THỜI GIAN:</b><br>{data['date']}</div>""",
                            unsafe_allow_html=True)
            else:
                c2.info("🕒 Thời gian: Ẩn")

            if data['has_gps']:
                st.markdown(
                    f"""<div class="danger-box"><b>🚨 RỦI RO CAO: LỘ VỊ TRÍ!</b><br>Tọa độ: {data['lat']}, {data['lon']}</div>""",
                    unsafe_allow_html=True)
                st.map(pd.DataFrame({'lat': [data['lat']], 'lon': [data['lon']]}))
            else:
                st.success("✅ Vị trí: An toàn (Không tìm thấy GPS)")

            st.divider()

            # --- KHU VỰC NÚT XỬ LÝ VÀ TẢI VỀ (ĐÃ SỬA LỖI BIẾN MẤT) ---

            # Nếu chưa có kết quả trong bộ nhớ -> Hiện nút Xử lý
            if st.session_state.processed_buffer is None:
                if st.button("✨ XÓA SẠCH DẤU VẾT & TẢI VỀ"):
                    # Xử lý ảnh
                    clean_buf = clean_image_data(image)
                    # Lưu vào Session State (Bộ nhớ tạm) -> Để F5 không bị mất
                    st.session_state.processed_buffer = clean_buf

                    # Nếu không phải VIP -> Ghi nhận đã dùng thử
                    if not is_vip:
                        cookie_manager.set("ez_trial_status", "done", key="set_trial", expires_at=None)

                    # Rerun để hiển thị nút Tải về từ Session State
                    st.rerun()

            # Nếu ĐÃ CÓ kết quả trong bộ nhớ -> Hiện nút Tải về (Nó sẽ nằm lỳ ở đây)
            else:
                st.success("✅ ĐÃ XỬ LÝ XONG! Hãy tải ảnh về.")
                st.download_button(
                    label="⬇️ Tải ảnh sạch",
                    data=st.session_state.processed_buffer,
                    file_name="safe_image.jpg",
                    mime="image/jpeg"
                )

                if not is_vip:
                    st.info("💡 Bạn đã dùng hết lượt thử. Sau khi tải xong và tải lại trang, hệ thống sẽ khóa.")

        except Exception as e:
            st.error(f"Lỗi đọc file: {e}")
    else:
        # Nếu người dùng xóa ảnh khỏi ô upload -> Xóa luôn bộ nhớ đệm
        if st.session_state.processed_buffer is not None:
            st.session_state.processed_buffer = None


def show_paywall():
    st.markdown("""
        <div class='paywall-box'>
            <h3>⛔ CẢNH BÁO BẢO MẬT</h3>
            <p>Bạn đã sử dụng hết lượt miễn phí.</p>
            <p>Để tiếp tục bảo vệ thông tin cá nhân, vui lòng kích hoạt bản quyền.</p>
            <hr>
            <p>💰 Phí bản quyền: <b>29.000đ / Sử dụng vĩnh viễn</b></p>
            <p>👉 Zalo Admin: <b>0931.458.778</b></p>
        </div>
    """, unsafe_allow_html=True)

    code = st.text_input("🔑 Nhập Code kích hoạt:", type="password")
    if st.button("MỞ KHÓA NGAY"):
        if code in VALID_CODES:
            # 1. Ghi Cookie (cho lần sau)
            cookie_manager.set("ez_vip_status", "true", key="set_vip")
            # 2. Ghi Session (để mở NGAY LẬP TỨC không cần chờ cookie)
            st.session_state.temp_vip = True
            st.success("Mã đúng! Đang vào hệ thống...")
            time.sleep(0.5)
            st.rerun()
        else:
            st.error("Mã không đúng!")


if __name__ == "__main__":
    main()