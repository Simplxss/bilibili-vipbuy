import json
import random
import time

from BilibiliQRcode.BilibiliQRcode import BilibiliQRcode
from BilibiliShow import BilibiliShow
from BilibiliVgate import BilibiliVgate

from geetest import get_validate


def main():
    bilibili = BilibiliQRcode()
    cookies = bilibili.login()
    
    projectId = int(input("会展ID: "))
    count = int(input("抢几张票: "))

    show = BilibiliShow(cookies)
    json0 = show.get_info(projectId)
    idBind = json0["data"]["id_bind"]
    needContact = json0["data"]["need_contact"]
    buyerInfo = json0["data"]["buyer_info"]
    for i in json0["data"]["screen_list"]:
        print(i["name"])
    screen_length = len(json0['data']['screen_list'])
    screenType = int(input(f"抢第几场的票(1~{screen_length}): ")) - 1
    if screenType >= screen_length or screenType < 0:
        print("场次不存在")
        return
    screen = json0["data"]["screen_list"][screenType]
    screenId = screen["id"]
    for i in screen["ticket_list"]:
        print(i["desc"], i["price"])
    ticket_length = len(screen["ticket_list"])
    ticketType = int(input(f"抢第几种的票(1~{ticket_length}): ")) - 1
    if ticketType >= ticket_length or ticketType < 0:
        print("票种不存在")
        return
    ticket = screen["ticket_list"][ticketType]
    skuId = ticket["id"]
    payMoney = ticket["price"]
    isPackage = ticket["is_package"]
    packageNum = ticket["package_num"]

    json0 = show.get_buyer(projectId)
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

    buyers = json.dumps(list, ensure_ascii=False)

    print("开始抢票")

    while True:
        try:
            json1 = show.get_info(projectId)
            if json1["errno"] != 0:
                continue
            for i in json1["data"]["screen_list"]:
                if i["id"] == screenId:
                    for j in i["ticket_list"]:
                        if j["id"] == skuId:
                            # if j["clickable"]:
                            #     print(time.ctime(), "有票了")
                            while True:
                                json2 = show.get_token(
                                    projectId, screenId, count, skuId, buyerInfo)

                                if json2["errno"] == -401:
                                    ga = json2["data"]["ga_data"]
                                    print(
                                        f"需要验证: {ga["decisions"]}")
                                    try:
                                        vgate = BilibiliVgate(cookies)
                                        res = vgate.get_geetest(
                                            ga["riskParams"]["buvid"],
                                            ga["riskParams"]["decision_type"],
                                            ga["riskParams"]["ip"],
                                            ga["riskParams"]["mid"],
                                            ga["riskParams"]["origin_scene"],
                                            ga["riskParams"]["scene"],
                                            ga["riskParams"]["ua"],
                                            ga["riskParams"]["v_voucher"])

                                        if res["code"] != 0:
                                            print(f"获取 geetest 验证失败: {
                                                  res["message"]}")
                                            continue

                                        token = res["data"]["token"]
                                        gt = res["data"]["geetest"]["gt"]
                                        challenge = res["data"]["geetest"]["challenge"]

                                        (
                                            seccode,
                                            validate
                                        ) = get_validate(gt, challenge)

                                        res = vgate.verify(
                                            token, challenge, seccode, validate)

                                        if res["code"] != 0:
                                            print(f"验证失败: {res["message"]}")
                                            continue

                                        json2 = show.get_token(
                                            projectId, screenId, count, skuId, token, token)

                                        if json2["errno"] != 0:
                                            print(json2["errno"], json2["msg"])
                                            continue
                                    except:
                                        print("验证错误")
                                        breakpoint()
                                elif json2["errno"] != 0:
                                    # 100041 您的账号存在异常，暂时无法购票
                                    print(json2["errno"], json2["msg"])
                                    continue

                                token = json2["data"]["token"]
                                while True:
                                    json3 = show.create_order(
                                        projectId, screenId, count, payMoney, idBind, isPackage, packageNum, needContact, skuId, token, buyers)

                                    if json3["errno"] == 0:
                                        print("抢到了，请尽快去支付")
                                        return
                                    elif json3["errno"] == 100001:
                                        # 前方拥堵，请重试
                                        # 请慢一点
                                        time.sleep(random.randint(1, 3))
                                        continue
                                    elif json3["errno"] == 100009:
                                        print("当前票被抢")
                                        break
                                    elif json3["errno"] == 100051:
                                        print("验证超时")
                                        break
                                    print(json3["errno"], json3["msg"])
                                if json3["errno"] == 100009:
                                    break
        except Exception as e:
            print(e)
        time.sleep(random.randint(8, 15))


if __name__ == "__main__":
    main()
