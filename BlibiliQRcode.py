import time
from urllib.parse import urlparse, parse_qs
import requests
import qrcode

"""
Parameters:
  param1 - type: 1: biligame.com 2: bilibili.cn 3: bilicomic.com 4: bilicomics.com
 
Returns:
    cookies in dict
"""


def login_var_qrcode(type=1) -> dict:
    s = requests.session()

    # 初始化获取 QRcode
    res = s.get(
        url="https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
    ).json()
    if res["code"] != 0:
        print("Get qrcode Error")
        return {}

    qrcode_url = res["data"]["url"]
    qrcode_key = res["data"]["qrcode_key"]
    print("Scan URL:" + qrcode_url)
    print("Scan Key:" + qrcode_key)

    # create a QR code instance
    qr = qrcode.QRCode(version=1, box_size=10, border=5)

    # add data to the QR code
    qr.add_data(qrcode_url)

    # generate the QR code
    qr.make(fit=True)

    # print the QR code as ASCII art
    qr.print_ascii()

    while True:
        time.sleep(3)
        verify_url = (
            "https://passport.bilibili.com/x/passport-login/web/qrcode/poll?qrcode_key="
            + qrcode_key
        )
        res = s.get(verify_url).json()
        if res["data"]["code"] == 86090 or res["data"]["code"] == 86101:
            # 86090 二维码已扫码未确认 86101 未扫码
            print("Scan Result:" + res["data"]["message"])
            continue
        else:
            break

    if res["data"]["code"] != 0 or res["data"]["url"] == "":
        print("Login Error")
        return {}

    print("Bilibili Login...")

    parsed_url = urlparse(res["data"]["url"])
    captured_value = parse_qs(parsed_url.query)

    csrf = captured_value["bili_jct"][0]
    user_id = captured_value["DedeUserID"][0]
    sess_data = captured_value["SESSDATA"][0]

    print("Bilibili Csrf:" + csrf)
    print("Bilibili User ID:" + user_id)
    print("Bilibili Sessdata:" + sess_data)
    res = s.get(
        "https://passport.bilibili.com/x/passport-login/web/sso/list",
        params={"biliCSRF": csrf},
    ).json()
    if res["code"] != 0:
        print("Login Error")
        return {}
    sso_dict = res["data"]["sso"]
    print("SsoAuthLink:", sso_dict)
    res = s.get(sso_dict[type])
    print("Login OK!")
    print("Cookies:", s.cookies.get_dict())
    return s.cookies.get_dict()


def get_user_info(cookie):
    res = requests.get(
        "https://api.bilibili.com/x/web-interface/nav", cookies=cookie
    ).json()
    if res["code"] != 0:
        print("Login Fail")
        exit(1)
    print(f"isLogin:{res['data']['isLogin']}")
    print("uname:" + res["data"]["uname"])
    print("current_face:" + res["data"]["face"])
    print(f"current_level:{res['data']['level_info']['current_level']}")
    print(f"current_exp:{res['data']['level_info']['current_exp']}")
