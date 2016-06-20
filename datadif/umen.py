#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import hashlib
import requests
import time
import sys
reload(sys)
sys.setdefaultencoding('utf8')

# debug key and secret key
SECRET_KEY = 'ij1a4iltc4p2ml29swvkgjoanxyron5m'
APP_KEY = '575e809b67e58eb219000d78'
if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), '__test__')):
    PRODUCTION_MODE = "false"
else:
    PRODUCTION_MODE = "true"

BODYTPL = {
    "ticker": True,
    "title": True,
    "text": True,
    "icon": True,
    "largeIcon": True,
    "img": True,
    "sound": True,
    "builder_id": True,
    "play_vibrate": True,
    "play_lights": True,
    "play_sound": True,
    "after_open": True,
    "url": True,
    "activity": True,
    "custom": True,
}

POLICYTPL = {
    "start_time": True,
    "expire_time": True,
    "max_send_num": True,
}

def timestamp(self):
    return int(time.time()*1000)

def unserialize(self, data):
    return json.dumps(data, ensure_ascii=False, encoding='utf8', sort_keys=True).encode('utf-8')

def sign(self, url, data, key):
    return hashlib.md5('%s%s%s%s'%('POST', url, unserialize(data), key)).hexdigest()

def check(obj, src):
    for key in obj:
        if src.get(key):
            pass
        else:
            raise Exception("Key %s is not in (%s)." % (key, ','.join(src.keys())))

class UmengPush(object):
    """
        appkey：应用唯一标识。
        友盟消息推送服务提供的appkey
        和友盟统计分析平台使用的同一套appkey。

        app_master_secret：服务器秘钥，
        用于服务器端调用API，
        请求时对发送内容做签名验证。

        production_mode: 正式/测试模式。
        测试模式下，广播/组播只会将消息发给测试设备。
        测试设备需要到web上添加。
        Android测试设备属于正式设备的一个子集。

        thirdparty_id: 开发者自定义消息标识ID, 
        开发者可以为同一批发送的多条消息。
    """

    def __init__(self, url, appkey, appsecret, thirdparty=None):
        self.url = url
        self.appkey = appkey
        self.appsecret = appsecret
        self.thirdparty = thirdparty

    def cast(self, content, 
            cast_type='unicast', 
            token='',
            intent='',
            activity='com.adesk.picasso.view.HomeActivity', 
            display_type='notification', 
            **kwargs):

        if 'title' not in message:
            message['title'] = '安卓壁纸'

        if 'ticker' not in message:
            message['ticker'] = message['text']

        if display_type == 'message':
            message['custom'] = self.touchuan_message(message['title'], message['text'], 
                message['ticker'], action=intent)
            message['after_open'] ='go_custom'

        if 'activity' not in message:
            message['activity'] = activity

        data = {
            'appkey': APP_KEY,
            'device_tokens': token,
            'payload': {
                "aps":{
                    "alert": "我们都是好孩子"
                },
            },
            'timestamp': timestamp(),
            'type': cast_type,
            'production_mode': PRODUCTION_MODE,
            'description': message['title'],
        }

        data.update(kwargs)

        if 'after_open' not in message:
            message['after_open'] = 'go_activity'

        sign = sign(self.PUSH_URL, data, SECRET_KEY)
        body = unserialize(data)
        result = requests.post(('%s?sign=%s')%(self.PUSH_URL, sign), data=body)
        print result.content

    def send(self, payload, policy={}):
        check(payload['body'], BODYTPL)
        check(policy, POLICYTPL)
        sign = sign(self.PUSH_URL, data, SECRET_KEY)
        body = unserialize(data)
        result = requests.post(('%s?sign=%s')%(self.PUSH_URL, sign), data=body)
        return result.content

    @abstractmethod
    def directedcast(self, device_token, body, display_type='notification', extra={}, policy={}, description=""):
        """
            定向播: 向指定的设备发送消息，
            包括单播(unicast) or 列播(listcast)
            向若干个device_token或者若干个alias发消息。
        """
        pass

    @abstractmethod
    def broadcast(self, body, display_type='notification', extra={}, policy={}, description=""):
        """
            广播(broadcast，属于task): 向安装该App的所有设备发送消息。
        """
        pass

    @abstractmethod
    def filecast(self, content, token, intent='', **kwargs):
        """
            文件播(filecast，属于task)：开发者将批量的device_token
            或者alias存放到文件, 通过文件ID进行消息发送。
        """
        pass

    @abstractmethod
    def groupcast(self, content, token, intent='', **kwargs):
        """
            组播(groupcast，属于task): 向满足特定条件的设备集合发送消息，
            例如: "特定版本"、"特定地域"等。
            友盟消息推送所支持的维度筛选
            和友盟统计分析所提供的数据展示维度是一致的，
            后台数据也是打通的
        """
        pass

    @abstractmethod
    def customizedcast(self, content, token, intent='', **kwargs):
        """
            自定义播(customizedcast，属于task): 开发者通过自有的alias进行推送, 
            可以针对单个或者一批alias进行推送，
            也可以将alias存放到文件进行发送。
        """
        pass


class UmengIosPush(UmengPush):

    def unicast(self, content, device_token, display_type='', intent='', **kwargs):
        self.cast(content, 'unicast', token, intent=intent, **kwargs)

    def broadcast(self, content,):
        self.cast(content, 'broadcast', intent=intent, **kwargs)

    def listcast(self, content, token, intent='', **kwargs):
        self.cast(content, 'unicast', token, intent=intent, **kwargs)

    def filecast(self, content, token, intent='', **kwargs):
        self.cast(content, 'unicast', token, intent=intent, **kwargs)

    def groupcast(self, content, token, intent='', **kwargs):
        self.cast(content, 'unicast', token, intent=intent, **kwargs)

    def customizedcast(self, content, token, intent='', **kwargs):
        self.cast(content, 'unicast', token, intent=intent, **kwargs)

    def touchuan_message(self, title='', content='', ticker='', action=None, voice=True, delete=True):
        msg = {"title":"安卓壁纸", "content":"", "voice":voice, "vibrate":voice, "delete":delete, "action":None}
        if title:
            msg['title'] = title 

        if ticker:
            msg['ticker'] = ticker

        if content:
            msg['content'] = content
        
        if action:
            msg['action'] = action
        
        return unserialize(msg)


def umen_push(_id):
    print 'abc'


if __name__ == '__main__':
    intent = 'androidesk://subject/558269d369401b611a4c86bb'
    token = 'add1d6d1a09a738d6c4d5c56f2de2c2bb1375a768d9ad03e52bc2408a56cb5fc'
    tui = UmengPush()
    tui.broadcast({'text': 'broadcast'}, token=token)
#     tui.broadcast_message({'text': 'broadcast'}, intent=intent)
#     tui.unicast_message({'text': 'test'}, token=token, intent=intent)
#     tui.unicast({'title': 'test', 'text': 'test', 'ticker': 'test'}, token=token, intent=intent)
