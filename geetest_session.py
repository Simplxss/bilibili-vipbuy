from enum import Enum, unique
import json
import re
import time
from io import BytesIO

from requests import session
from PIL import Image

from param import get_full_page_w1, get_full_page_w2, get_track, get_slide_w, get_s
from captcha import calculate_offset


@unique
class Resp(Enum):
    SUCCESS = 0
    SLIDE = 1
    TIMEOUT = 2
    SLIDE_ERR = 3
    TRACK_ERR = 4
    ILLEGAL_ERR = 5
    UNKNOWN_ERR = 6


class GSession:
    """获取极验Session"""

    def __init__(self):
        self.session = session()
        self.session.headers = {
            "Origin": "https://mall.bilibili.com",
            "Referer": "https://mall.bilibili.com/",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3"
            "Mobile/15E148 Safari/604.1",
        }
        self.res = Resp.SUCCESS
        self.gt = str()
        self.challenge = str()
        self.s = get_s()
        self.validate = str()
        self.bg_url = str()
        self.full_bg_url = str()
        self.offset = 0
        self.track = list()

    def get_php(self):
        """
        step=1:注册参数s:s经过多层加密拼接成w
        step=2:提交滑块
        """
        """"""
        resp = self.session.get(
            "https://api.geetest.com/get.php",
            params={
                "gt": self.gt,
                "challenge": self.challenge,
                "lang": "zh-cn",
                "pt": 3,
                "client_type": "web_mobile",
                "w": get_full_page_w1(self.gt, self.challenge, self.s),
                "callback": f"geetest_{int(time.time()*1000)}",
            },
        )

        if resp is None:
            print("无法注册参数s...")
            self.res = Resp.TIMEOUT
        return resp is not None

    def ajax_php(self, params=None):
        """
        step=1:发送请求,校验参数w
        step=2:滑动滑块
        """
        resp = self.session.get(
            "https://api.geetest.com/ajax.php",
            params=(
                {
                    "gt": self.gt,
                    "challenge": self.challenge,
                    "lang": "zh-cn",
                    "pt": 3,
                    "client_type": "web_mobile",
                    "w": get_full_page_w2(self.gt, self.challenge, self.s) + "1",
                    "callback": f"geetest_{int(time.time()*1000)}",
                }
                if params == None
                else params
            ),
        )

        if resp is None:
            self.res = Resp.TIMEOUT
            return False
        else:
            resp = re.search(r"geetest_.*?\((.*?)\)", resp.text, re.S)
            if resp is None:
                self.res = Resp.TIMEOUT
                return False
            res = json.loads(resp.group(1))
            if "success" in res:
                self.validate = res["validate"]
                return True
            elif "data" in res:
                self.res = Resp.SLIDE
                return True
            else:
                self.res = Resp.SLIDE_ERR
                return False

    def get_slide_images(self):
        """获取验证码图片的地址"""
        resp = self.session.get(
            "https://api.geetest.com/get.php",
            params={
                "is_next": "true",
                "type": "slide3",
                "gt": self.gt,
                "challenge": self.challenge,
                "lang": "zh-cn",
                "https": "true",
                "protocol": "https://",
                "offline": "false",
                "product": "embed",
                "api_server": "api.geetest.com",
                "isPC": "false",
                "autoReset": "true",
                "width": "100%",
                "callback": f"geetest_{int(time.time()*1000)}",
            },
        )

        if resp is None:
            self.res = Resp.TIMEOUT
            return False
        resp = re.search(r"geetest_.*?\((.*?)\)", resp.text, re.S)
        if resp == None:
            return False
        res = json.loads(resp.group(1))
        # 更新gt/challenge
        self.gt = res["gt"]
        self.challenge = res["challenge"]
        # 获得滑动验证码图片的URL(带缺口+不带缺口)
        self.bg_url = "https://static.geetest.com/" + res["bg"]
        self.full_bg_url = "https://static.geetest.com/" + res["fullbg"]
        return True

    def get_track(self):
        """获取滑动轨迹"""
        resp1 = self.session.get(self.bg_url)
        resp2 = self.session.get(self.full_bg_url)
        if not (resp1 and resp2):
            self.res = Resp.TIMEOUT
            return False
        img1 = Image.open(BytesIO(resp1.content))
        img2 = Image.open(BytesIO(resp2.content))

        # 计算偏移量
        self.offset = calculate_offset(img1, img2)

        # 根据偏移量获取轨迹
        self.track = get_track(self.offset)
        if self.track is None:
            self.res = Resp.TRACK_ERR
        return self.track is not None

    def slide(self):
        """滑动滑块"""
        return self.ajax_php(
            {
                "gt": self.gt,
                "challenge": self.challenge,
                "lang": "zh-cn",
                "$_BCX": 3,
                "client_type": "web_mobile",
                "w": get_slide_w(
                    self.gt, self.challenge, get_s(), self.offset, self.track
                ),
                "callback": f"geetest_{int(time.time()*1000)}",
            }
        )

    def get_validate(self, gt, challenge):
        self.gt, self.challenge = gt, challenge
        # 此处使用and操作符,当有某个请求返回false时,直接终止当前请求链
        _ = (
            self.get_php()
            and self.ajax_php()
            and self.get_slide_images()
            and self.get_track()
            and self.slide()
        )
        return self.challenge, self.validate
    