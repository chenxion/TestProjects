# -*- coding: utf-8 -*-
# 七牛云图片存储API

from qiniu import Auth, put_file, etag, put_data
import qiniu.config

#需要填写你的 Access Key 和 Secret Key
access_key = 'cD39pD8pQ0c3ASWJduXSkI0Ru0XFFevh7QHaOVEY'
secret_key = '_AnH_NZcYgbxR2KclJjCQvNMIh7Xc-bshWNsvQz6'

# #构建鉴权对象
# q = Auth(access_key, secret_key)
#
# #要上传的空间
# bucket_name = ''
#
# #生成上传 Token，可以指定过期时间等
# token = q.upload_token(bucket_name, None, 3600)
#
# ret, info = put_data(token, None, localfile)  # put_data上传数据，put_file上传本地图片
# print(info)
# assert ret['key'] == key
# assert ret['hash'] == etag(localfile)

# 封装成函数
def storage(file_data):
    """
    上传文件到七牛
    :param file_data:要上传的文件数据
    :return:
    """
    # 构建鉴权对象
    q = Auth(access_key, secret_key)

    # 要上传的空间
    bucket_name = 'ihome-python'

    # 生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name, None, 3600)

    ret, info = put_data(token, None, file_data)  # put_data上传数据，put_file上传本地图片

    if info.status_code == 200:
        # 表示上传成功,返回文件名
        return ret.get("key")
    else:
        # 表示上传失败，主动抛出异常，告知信息
        raise Exception("上传七牛失败")




