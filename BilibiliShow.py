import time
import requests


class BilibiliShow:
    def __init__(self, cookies):
        self.session = requests.session()
        self.session.headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
        }
        self.session.cookies = requests.utils.cookiejar_from_dict(cookies)

    def get_info(self, projectId):
        return self.session.get(
            "https://show.bilibili.com/api/ticket/project/getV2",
            params={"id": projectId, "project_id": projectId,
                    "requestSource": "neul-next"}
        ).json()

    def get_address(self, projectId):
        return self.session.get(
            "https://show.bilibili.com/api/ticket/addr/list",
            params={"project_id": projectId, "src": "ticket"},
        ).json()

    def get_buyer(self, projectId):
        return self.session.get(
            "https://show.bilibili.com/api/ticket/buyer/list",
            params={"project_id": projectId, "src": "ticket"},
        ).json()

    def get_token(self, projectId, screenId, count, skuId, buyerInfo, token=None, gaia_vtoken=None):
        return self.session.post(
            "https://show.bilibili.com/api/ticket/order/prepare",
            params={**{"project_id": projectId},
                    **({"token": token, "gaia_vtoken": gaia_vtoken}
                       if token and gaia_vtoken else {})},
            data={
                "count": count,
                "project_id": projectId,
                "screen_id": screenId,
                "order_type": 1,
                "sku_id": skuId,
                "buyer_info": buyerInfo,
                "ticket_agent": "",
                "token": "",
                "requestSource": "neul-next",
                "newRisk": True
            },
        ).json()

    def create_order(self, projectId, screenId, count, payMoney, idBind, needContact, isPackage, packageNum, skuId, buyerInfo, token):
        timestamp = int(time.time() * 1000)
        return self.session.post(
            "https://show.bilibili.com/api/ticket/order/createV2",
            params={"project_id": projectId},
            data={
                "project_id": projectId,
                "screen_id": screenId,
                "count": count,
                "pay_money": payMoney,
                "order_type": 1,
                "timestamp": timestamp,
                "id_bind": idBind,
                "need_contact": needContact,
                "is_package": isPackage,
                "package_num": packageNum,
                "contactInfo": [],
                "sku_id": skuId,
                "coupon_code": "",
                "again": 0,
                "token": token,
                "deviceId": "22c943523458064379f38455d0bd0578",
                "buyer_info": buyerInfo,
                "requestSource": "neul-next",
                "clickPosition": {
                    "now": timestamp,
                    "origin": timestamp - 21356,
                    "x": 326,
                    "y": 724
                },
                "requestSource": "neul-next",
                "newRisk": True
            },
        ).json()
