# web_app.py
import streamlit as st
import license
import config

st.set_page_config(page_title="Kích Hoạt Phần Mềm", page_icon="🔑")

# --- CSS làm đẹp ---
st.markdown("""
    <style>
    .stButton>button {
        background-color: #ee4d2d;
        color: white;
        font-weight: bold;
        width: 100%;
        height: 50px;
        border-radius: 5px;
    }
    .success-box {
        padding: 20px;
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        text-align: center;
        font-size: 20px;
        font-weight: bold;
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title(f"🔐 Kích hoạt: {config.APP_NAME}")

# --- XỬ LÝ LẤY MÃ TỪ URL (CODE SỬA LỖI) ---
# Cách mới nhất để lấy query params trong Streamlit
try:
    # Dành cho Streamlit bản mới
    hwid_param = st.query_params.get("hwid", "")
except:
    # Dành cho Streamlit bản cũ (dự phòng)
    try:
        hwid_param = st.experimental_get_query_params().get("hwid", [""])[0]
    except:
        hwid_param = ""

# Đảm bảo hwid_param là một chuỗi văn bản sạch sẽ
if isinstance(hwid_param, list):
    hwid_param = hwid_param[0] if hwid_param else ""

initial_value = str(hwid_param).strip()

# --- FORM NHẬP LIỆU ---
with st.form("activation_form"):
    # Kiểm tra xem có mã máy chưa để hiển thị hướng dẫn phù hợp
    if initial_value:
        st.success(f"✅ Hệ thống đã tự động điền Mã Máy của bạn: {initial_value}")
        label_text = "Mã Máy (Kiểm tra lại nếu cần)"
    else:
        st.warning("⚠️ Không tìm thấy Mã Máy tự động. Vui lòng copy thủ công từ phần mềm.")
        label_text = "Nhập Mã Máy thủ công"

    # Ô nhập Mã máy (Có giá trị mặc định là initial_value)
    hwid_input = st.text_input(label_text, value=initial_value)

    # Ô nhập mật khẩu
    secret_code = st.text_input("Nhập Mã Bảo Mật (Shop gửi trong tin nhắn)", type="password")

    submitted = st.form_submit_button("LẤY KEY KÍCH HOẠT")

# --- XỬ LÝ KHI BẤM NÚT ---
ACCESS_PASSWORD = "SHOPEE_29K_VIP"

if submitted:
    # 1. Kiểm tra đầu vào
    if not hwid_input:
        st.error("❌ Lỗi: Mã máy đang để trống. Vui lòng nhập vào.")
    elif secret_code != ACCESS_PASSWORD:
        st.error("❌ Lỗi: Sai Mã Bảo Mật.")
    else:
        # 2. Xử lý tạo key
        clean_hwid = hwid_input.strip().upper()
        try:
            # Gọi hàm tạo key
            key = license.generate_key(clean_hwid)

            st.markdown("---")
            st.success("🎉 TẠO KEY THÀNH CÔNG!")
            st.caption("Copy dòng chữ dưới đây và dán vào phần mềm:")

            # Hiển thị Key
            st.code(key, language="text")
            st.markdown(f'<div class="success-box">{key}</div>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Có lỗi xảy ra: {e}")

st.markdown("---")
st.caption("Hỗ trợ kỹ thuật: Chat qua Shopee. AITHANHAI 2026")