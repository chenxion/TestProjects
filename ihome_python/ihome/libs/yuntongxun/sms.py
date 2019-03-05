# coding=utf-8
# 短信发送模块

from CCPRestSDK import REST


# 主帐号
accountSid= '8a216da86904c06001690bf2669b034a'

# 主帐号Token
accountToken= '32b3018e05b244cca11891bb1fb4f7c9'

# 应用Id
appId='8a216da86904c06001690bf267020351'

# 请求地址，格式如下，不需要写http://
serverIP='app.cloopen.com'

# 请求端口
serverPort='8883'

# REST版本号
softVersion='2013-12-26'

  # 发送模板短信
  # @param to 手机号码
  # @param datas 内容数据 格式为列表 例如：['12','34']，如不需替换请填 ''
  # @param $tempId 模板Id


class CCP(object):
    """自定义封装的发短信的辅助类"""
    # 用来保存对象的类属性
    instance = None
    def __new__(cls):  # 单例方法
        # 判断CCP类有没有已经创建好的对象，如果没有，创建一个对象，并且保存
        if cls.instance is None:
            obj = super(CCP, cls).__new__(cls)

            # 初始化REST SDK
            obj.rest = REST(serverIP, serverPort, softVersion)
            obj.rest.setAccount(accountSid, accountToken)
            obj.rest.setAppId(appId)

            cls.instance = obj

        # 如果有，则将保存的对象直接返回
        return cls.instance

    def send_template_sms(self, to, datas, temp_id):
        """"""
        result = self.rest.sendTemplateSMS(to, datas, temp_id)
        # for k, v in result.iteritems():
        #
        #     if k == 'templateSMS':
        #         for k, s in v.iteritems():
        #             print '%s:%s' % (k, s)
        #     else:
        #         print '%s:%s' % (k, v)
        status_code = result.get("statusCode")
        if status_code == "000000":
            # 表示发送短信成功
            return 0
        else:
            # 发送失败
            return -1

if __name__ == '__main__':
    ccp = CCP()
    # 发送短信
    ret = ccp.send_template_sms("13163732809", ["1234", "5"], 1)
    print(ret)



#sendTemplateSMS(手机号码,内容数据,模板Id)