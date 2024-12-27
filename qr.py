import pyqrcode


def generate_qr_code(content: str) -> str:
    qr = pyqrcode.create(content)
    return qr.terminal(quiet_zone=1)
