# license.py
import uuid
import hashlib
import os
import config


def get_hwid():
    """
    Lấy Mã máy (Hardware ID) dựa trên MAC Address.
    Trả về: Chuỗi 12 ký tự viết hoa.
    """
    mac = uuid.getnode()
    # Băm mã MAC để nó trông ngắn gọn và chuyên nghiệp hơn
    hwid_raw = f"{mac}{config.APP_NAME}"
    hashed = hashlib.md5(hwid_raw.encode()).hexdigest().upper()

    # Lấy 12 ký tự đầu, chia nhóm cho đẹp: XXXX-XXXX-XXXX
    return f"{hashed[:4]}-{hashed[4:8]}-{hashed[8:12]}"


def generate_key(hwid):
    """
    Tạo Key kích hoạt dựa trên HWID và SECRET_KEY trong config.
    Đây là thuật toán 'tạo chìa khóa'.
    """
    # Kết hợp HWID với Mật khẩu bí mật của bạn
    data = f"{hwid}@{config.SECRET_KEY}"

    # Băm ra chuỗi SHA256
    signature = hashlib.sha256(data.encode()).hexdigest().upper()

    # Lấy 16 ký tự làm key: AAAA-BBBB-CCCC-DDDD
    return f"{signature[:4]}-{signature[4:8]}-{signature[8:12]}-{signature[12:16]}"


def check_license():
    """
    Kiểm tra xem máy này đã có file license hợp lệ chưa.
    """
    if not os.path.exists(config.LICENSE_FILE):
        return False

    try:
        with open(config.LICENSE_FILE, "r") as f:
            saved_key = f.read().strip()

        current_hwid = get_hwid()
        expected_key = generate_key(current_hwid)

        return saved_key == expected_key
    except:
        return False


def save_license(key):
    """Lưu key vào file để lần sau không phải nhập lại"""
    with open(config.LICENSE_FILE, "w") as f:
        f.write(key.strip())