# coding:utf-8
from weibopay import WeiboApp, WeiboPay
import tornado.ioloop
import tornado.web

SELLER_ID = '3292350247'  # 商户ID(就是微博ID)
APPKEY = 'demo'
CERT = 'test_private_key.pem'


def create_nonce(length=12):
    import string, random
    return ''.join(random.sample(string.ascii_letters + string.digits, length))


class WeiboOrder(object):
    def __init__(self, *args, **kwargs):
        self._params = {}
        for k, v in kwargs.items():
            setattr(self, k, v)


    @classmethod
    def new_order(cls, data):
        import arrow
        pay_id = arrow.now().format('YYYYMMDDHHmmss') + create_nonce(10)
        data['out_pay_id'] = pay_id
        order = cls(**data)
        order.save()
        order._params = {}
        order._params.update(data)
        return order

    @property
    def params(self):
        return self._params

    def save(self):
        '''save order params to local'''
        pass


class WeiboPayHandler(tornado.web.RequestHandler):
    def get(self):
        base_url = 'http://youdomain.com'
        data = {
            'sign_type': 'rsa',
            'subject': u'接入收银台实例'.encode('utf-8'),
            'total_amount': 1,
            'expire': 30 * 60,
            'notify_url': '{}/notify'.format(base_url),
            'return_url': '{}/return'.format(base_url),
            'body': u'接入收银台实例'.encode('utf-8'),
            'extra': u'额外参数.可以是个json字符串'
        }
        order = WeiboOrder.new_order(data)
        app = WeiboApp(SELLER_ID, APPKEY, 'appsecert')
        weibo_payment = WeiboPay(platform=app, private_cert=CERT)
        url = weibo_payment.cashier_url(order)

        context = {'url': url}
        context['data'] = data
        context['order'] = order

        return self.render('./templates/payment.html', title=u'微博支付测试', context=context)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('./templates/index.html')


application = tornado.web.Application([
    (r"/weibopay", WeiboPayHandler),
    (r"/", MainHandler),
])

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
