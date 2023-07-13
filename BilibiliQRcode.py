import time
from urllib.parse import urlparse, parse_qs
import qrcode
import requests


class BilibiliQRcode:
    def __init__(self):
        self.session = requests.session()
        self.qrcode_url = ""
        self.qrcode_key = ""
        self.csrf = ""

    def generate_qrcode(self):
        # 生成二维码
        res = self.session.get(
            "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
        ).json()
        if res["code"] != 0:
            print("Get qrcode Error")
            return False

        self.qrcode_url = res["data"]["url"]
        self.qrcode_key = res["data"]["qrcode_key"]
        # print("Scan URL:" + self.qrcode_url)
        # print("Scan Key:" + self.qrcode_key)

        qr = qrcode.QRCode()
        qr.add_data(self.qrcode_url)
        qr.print_ascii()

        return True

    def login(self):
        # 登录
        if not self.generate_qrcode():
            return {}
        while True:
            time.sleep(3)
            res = self.session.get(
                "https://passport.bilibili.com/x/passport-login/web/qrcode/poll",
                params={"qrcode_key": self.qrcode_key},
            ).json()
            if res["data"]["code"] == 86038:
                if not self.generate_qrcode():
                    return {}
            elif res["data"]["code"] != 86090 and res["data"]["code"] == 86101:
                break
            print("Scan Result:" + res["data"]["message"])

        if res["data"]["code"] != 0 or res["data"]["url"] == "":
            print("Login Error")
            return {}

        parsed_url = urlparse(res["data"]["url"])
        captured_value = parse_qs(parsed_url.query)

        self.csrf = captured_value["bili_jct"][0]
        # user_id = captured_value["DedeUserID"][0]
        # sess_data = captured_value["SESSDATA"][0]

        # print("Bilibili Csrf:" + self.csrf)
        # print("Bilibili User ID:" + user_id)
        # print("Bilibili Sessdata:" + sess_data)
        return self.session.cookies.get_dict()

    def get_sso_login(self, ssotype):
        if self.csrf == "":
            print("Please Login First")
            return {}
        # 获取 SSO 登录链接
        res = self.session.get(
            "https://passport.bilibili.com/x/passport-login/web/sso/list",
            params={"biliCSRF": self.csrf},
        ).json()
        if res["code"] != 0:
            print("Login Error")
            return {}
        sso_dict = res["data"]["sso"]
        # print("SsoAuthLink:", sso_dict)
        _ = self.session.get(sso_dict[ssotype])
        print("Login OK!")
        return self.session.cookies.get_dict()

    def get_user_info(self):
        # 获取用户信息
        res = self.session.get("https://api.bilibili.com/x/web-interface/nav").json()
        if res["code"] != 0:
            return ""
        return res["data"]


# 示例用法
bilibili = BilibiliQRcode()
bilibili.login()
print(bilibili.get_user_info())
print(bilibili.get_sso_login(0))
