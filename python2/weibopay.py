# coding:utf-8
__author__ = 'newpepsi'
import os
import requests

BASE = os.path.dirname(__file__)
# 用户微博支付私钥
CERT = os.path.join(BASE, 'cert', 'rsa_private_key.pem')
# 用户微博支付公钥
PUB_CERT = os.path.join(BASE, 'cert', 'rsa_public_key.pem')
# 微博支付公钥
WB_PUB_CERT = os.path.join(BASE, 'cert', 'weibo_pay_public_key.pem')


class InvalidSignError(BaseException):
    pass


class WeiboApp(object):
    wid = 'appid'
    appkey = 'appkey'
    appsecert = 'appsecret'
    name = u'微博应用'

    def __init__(self, user_id, appkey, secret, **kwargs):
        self.wid = user_id
        self.appkey = appkey
        self.appsecert = secret
        for k, v in kwargs.items():
            setattr(self, k, v)


class WeiboPay(object):
    VERIFY_KEYS = ('appkey', 'body', 'seller_id', 'total_amount', 'extra', 'pay_id', 'sign', 'out_pay_id', 'status',
                   'pay_time', 'sign_type', 'notify_time', 'buyer_id', 'notify_id', 'notify_type', 'subject')
    API = 'http://pay.sc.weibo.com/api/{}'

    def __init__(self, platform, private_cert=CERT):
        self.platform = platform
        self.seller_id = platform.wid
        self.appkey = platform.appkey
        self.cert = private_cert

    def post(self, url, data):
        return requests.post(url, data=data, timeout=3)

    def _call(self, api):
        return self.API.format(api)

    def cashier_url(self, order):
        import urllib
        self.params = order.params
        self.params['seller_id'] = self.seller_id
        self.params['appkey'] = self.appkey
        url_params = self.to_url_params(self.params)
        sign = self.make_sign(url_params)
        self.params['sign'] = sign
        order.seller_id = self.seller_id
        order.appkey = self.appkey
        order.sign = sign
        order.save()
        api = self._call('merchant/pay/cashier')
        return '?'.join([api, urllib.urlencode(self.params)]).replace('&amp;', '&')

    def pay_query(self, order):
        pass

    def message_send(self, params):
        url_params = self.to_url_params(params)
        sign = self.make_sign(url_params)
        params['sign'] = sign
        params['sign_type'] = 'RSA'
        api = self._call('merchant/message/send')
        return self.post(api, params)

    @classmethod
    def verify_data(cls, data, sign):
        from OpenSSL import crypto
        import base64
        if isinstance(data, dict):
            data = cls.gen_url_params(data)
            print data
        pk = crypto.load_publickey(crypto.FILETYPE_PEM, open(WB_PUB_CERT, 'r').read())
        cert = crypto.X509()
        cert.set_pubkey(pk)
        try:
            result = crypto.verify(cert, base64.b64decode(sign), data, 'sha1')
            return True
        except Exception as e:
            print e
            return False

    @classmethod
    def gen_url_params(cls, data):
        params = []
        for k in sorted(data.keys()):
            if data.get(k) and (not k in ['sign', 'sign_type']):
                if isinstance(data.get(k), unicode):
                    data[str(k)] = data.get(k).encode('utf-8')
                segment = '{}={}'.format(k, data.get(k))
                params.append(segment)
        return '&'.join(params)

    def to_url_params(self, data):
        params = []
        for k in sorted(data.keys()):
            if data.get(k) and (not k in ['sign', 'sign_type']):
                if isinstance(data.get(k), unicode):
                    data[k] = data.get(k).encode('utf-8')
                segment = '{}={}'.format(k, data.get(k))
                params.append(segment)
        return '&'.join(params)

    def make_sign(self, data):
        from OpenSSL import crypto
        import base64
        import rsa
        # pri_key = rsa.PrivateKey.load_pkcs1(open(self.cert, 'r').read())
        # d = rsa.sign(data, pri_key, 'SHA-1')
        pri_key = crypto.load_privatekey(crypto.FILETYPE_PEM, open(self.cert, 'r').read())
        d = crypto.sign(pri_key, data, 'sha1')
        return base64.b64encode(d)
