import json
import random
import time
import requests
from requests import utils

from BilibiliQRcode import BilibiliQRcode
from geetest_session import GSession


def main():
    projectId = int(input("会展ID: "))
    count = int(input("抢几张票: "))

    json0 = requests.get(
        "https://show.bilibili.com/api/ticket/project/get",
        params={"version": 134, "id": projectId, "project_id": projectId},
    ).json()
    id_bind = json0["data"]["id_bind"]
    need_contact = json0["data"]["need_contact"]
    for i in json0["data"]["screen_list"]:
        print(i["name"])
    day = int(input(f"抢第几天的票(1~{len(json0['data']['screen_list'])}): ")) - 1
    if day >= len(json0["data"]["screen_list"]) or day < 0:
        print("日期不存在")
        return
    screen = json0["data"]["screen_list"][day]
    screenId = screen["id"]
    for i in screen["ticket_list"]:
        print(i["desc"], i["price"])
    ticketType = int(input(f"抢第几种票(1~{len(screen['ticket_list'])}): ")) - 1
    if ticketType >= len(screen["ticket_list"]) or ticketType < 0:
        print("票种不存在")
        return
    ticket = screen["ticket_list"][ticketType]
    skuId = ticket["id"]
    payMoney = ticket["price"]

    bilibili = BilibiliQRcode()
    cookies = bilibili.login()

    s = requests.session()
    s.cookies = utils.cookiejar_from_dict(cookies)

    json0 = s.get(
        "https://show.bilibili.com/api/ticket/buyer/list",
        params={"project_id": projectId, "src": "ticket"},
    ).json()
    if count > len(json0["data"]["list"]):
        print("购票数大于购买人数, 请前往b站手动添加购买人")
        return
    for i in json0["data"]["list"]:
        print(i["name"])
    buyers = set(
        [
            int(i) - 1
            for i in input(f"第几位购买人(1~{len(json0['data']['list'])}, 多人用空格分隔): ").split()
        ]
    )
    if len(buyers) != count:
        print("购票数与购买人数不符")
        return

    list = []
    for i in buyers:
        if i >= len(json0["data"]["list"]) or i < 0:
            print("购买人不存在")
            return
        list.append(
            {
                "id": json0["data"]["list"][i]["id"],
                "name": json0["data"]["list"][i]["name"],
                "tel": json0["data"]["list"][i]["tel"],
                "personal_id": json0["data"]["list"][i]["personal_id"],
                "id_type": json0["data"]["list"][i]["id_type"],
            }
        )

    buyer_info = json.dumps(list, ensure_ascii=False)

    print("开始抢票")

    while True:
        try:
            json1 = requests.get(
                "https://show.bilibili.com/api/ticket/project/get",
                params={"version": 134, "id": projectId, "project_id": projectId},
            ).json()
            if json1["errno"] != 0:
                continue
            for i in json1["data"]["screen_list"]:
                if i["id"] == screenId:
                    for j in i["ticket_list"]:
                        if j["id"] == skuId:
                            if j["clickable"]:
                                print(time.ctime(), "有票了")
                                while True:
                                    json2 = s.post(
                                        "https://show.bilibili.com/api/ticket/order/prepare",
                                        params={"project_id": projectId},
                                        data={
                                            "project_id": projectId,
                                            "screen_id": screenId,
                                            "order_type": 1,
                                            "count": count,
                                            "sku_id": skuId,
                                            "token": "",
                                            "ticket_agent": "",
                                        },
                                    ).json()

                                    if json2["errno"] != 0:
                                        print(json2["msg"])
                                        continue

                                    if json2["data"]["shield"]["open"] == 1:
                                        print(
                                            f"遇到验证码 {json2['data']['shield']['naUrl']}"
                                        )
                                        res = s.post(
                                            "https://show.bilibili.com/openplatform/verify/tool/geetest/prepare",
                                            params={"oaccesskey": ""},
                                            data={
                                                "verify_type": 1,
                                                "business": "mall",
                                                "voucher": json2["data"]["shield"][
                                                    "voucher"
                                                ],
                                                "client_type": "h5",
                                                "csrf": cookies["bili_jct"],
                                            },
                                        ).json()

                                        captcha_id = res["data"]["captcha_id"]  # gt
                                        challenge = res["data"]["challenge"]
                                        geetest_voucher = res["data"]["geetest_voucher"]

                                        (
                                            challenge,
                                            validate,
                                        ) = GSession().get_validate(
                                            captcha_id, challenge
                                        )

                                        res = s.post(
                                            "https://show.bilibili.com/openplatform/verify/tool/geetest/check",
                                            params={"oaccesskey": ""},
                                            data={
                                                "success": 1,
                                                "captcha_id": captcha_id,
                                                "challenge": challenge,
                                                "validate": validate,
                                                "seccode": f"{validate}|jordan",
                                                "geetest_voucher": geetest_voucher,
                                                "client_type": "h5",
                                                "csrf": cookies["bili_jct"],
                                            },
                                        ).json()
                                        if res["code"] != 0:
                                            print(res["msg"])
                                            continue

                                    if json2["errno"] != 0:
                                        print(json2["errno"], json2["msg"])
                                        continue

                                    while True:
                                        json3 = s.post(
                                            "https://show.bilibili.com/api/ticket/order/createV2",
                                            params={"project_id": projectId},
                                            data={
                                                "project_id": projectId,
                                                "screen_id": screenId,
                                                "count": count,
                                                "pay_money": payMoney,
                                                "order_type": 1,
                                                "timestamp": int(time.time() * 1000),
                                                "id_bind": id_bind,
                                                "need_contact": need_contact,
                                                "is_package": 0,
                                                "package_num": 1,
                                                "contactInfo": [],
                                                "sku_id": skuId,
                                                "coupon_code": "",
                                                "again": 0,
                                                "token": json2["data"]["token"],
                                                "deviceId": "22c943523458064379f38455d0bd0578",
                                                "buyer_info": buyer_info,
                                            },
                                        ).json()

                                        if json3["errno"] == 0:
                                            print("抢到了，请尽快去支付")
                                            return
                                        elif json3["errno"] == 100001:
                                            continue
                                        elif json3["errno"] == 100009:
                                            print("当前票被抢")
                                            break
                                        elif json3["errno"] == 100051:
                                            print("验证超时")
                                            continue
                                        print(json3["errno"], json3["msg"])
                                    if json3["errno"] == 100009:
                                        break
        except Exception as e:
            print(e)
        time.sleep(random.randint(8, 15))


if __name__ == "__main__":
    main()
