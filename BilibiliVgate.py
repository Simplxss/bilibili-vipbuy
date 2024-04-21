import requests


class BilibiliVgate:
    def __init__(self, cookies):
        self.csrf = cookies["bili_jct"]
        self.session = requests.session()
        self.session.headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
        }
        self.session.cookies = requests.utils.cookiejar_from_dict(cookies)

    def get_geetest(self, buvid,  decision_type, ip, mid, origin_scene, scene, ua, v_voucher):
        return self.session.post(
            "https://api.bilibili.com/x/gaia-vgate/v1/register",
            params={
                "csrf": self.csrf,
                "buvid": buvid,
                "decision_type": decision_type,
                "ip": ip,
                "mid": mid,
                "origin_scene": origin_scene,
                "scene": scene,
                "ua": ua,
                "v_voucher": v_voucher
            }
        ).json()

    def verify(self, token, challenge, seccode, validate):
        return self.session.post(
            "https://api.bilibili.com/x/gaia-vgate/v1/validate",
            params={
                "csrf": self.csrf,
                "token": token,
                "challenge": challenge,
                "seccode": seccode,
                "validate": validate,
            }
        ).json()
