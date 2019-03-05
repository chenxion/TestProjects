# coding:utf-8
# 验证码模块

from . import api
from ihome.utils.captcha.captcha import captcha  # 导入验证码
from ihome import redis_store, constants, db  # 导入redis连接, 常量时间模块, 数据库
from flask import current_app, jsonify, make_response, request  # 导入整个项目的api：app, 返回json数据的函数, 返回响应内容, 接收请求内容
from ihome.utils.response_code import RET  # 导入自定义状态码
from ihome.models import User  # 导入数据库模型类
from ihome.libs.yuntongxun.sms import CCP  # 发送短信类
import random  # 导入随机数
from ihome.tasks.task_sms import send_sms  # 异步发送任务


# 图片验证码
# GET: 127.0.0.1/api/v1.0/image_codes/<image_code_id>
@api.route("/image_codes/<image_code_id>")  # 配置接口路由
def get_image_code(image_code_id):
    """
    获取图片验证码
    :params image_code_id: 图片验证码编号
    :return: 正常：验证码图片  异常：返回json数据
    """
    # 1. 获取参数 可以跳过，url上面已经带了图片验证码编号
    # 2. 检验参数 可以跳过，因为如果接收不到数据，浏览器都进来不了
    # 3. 业务处理
    # 生成验证码图片返回：名字,真实文本,图片数据
    name, text, image_data = captcha.generate_captcha()
    # 将验证码真实文本与编号保存到redis中，设置有效期
    # 使用哈希虽然实现了需求，但是有效期只能设置整体时间，不可用
    # 单条维护记录，选用字符串 "image_code_编号"："真实值"
    # 方法一：
    # redis_store.set("image_code_%s" % image_code_id, text)
    # 设置验证码有效期
    # redis_store.expire("image_code_%S" % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES)
    # 方法二：
    try:  # 因为是网络连接，如果断网了，程序会崩溃，报错
        redis_store.setex("image_code_%s" % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        # 记录抛出异常的日志
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="save image code id failed")

    # 4. 返回应答，并设置内容数据类型:图片
    resp = make_response(image_data)
    resp.headers["Content-Type"] = "image/jpg"
    return resp


# 短信验证码
# GET /api/v1.0/sms_codes/<mobile>?image_code=xxx&image_code_id=xxx
# @api.route("/sms_codes/<re(r'1[34578]\d{9}'):mobile>")
# def get_sms_code(mobile):
#     """获取短信验证码"""
#     # 1. 获取参数： 图片验证码和图片验证码的编号
#     image_code = request.args.get("image_code")
#     image_code_id = request.args.get("image_code_id")
#
#     # 2. 校验参数
#     if not all([image_code, image_code_id]):
#         # 表示参数不完整
#         return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")
#
#     # 3. 业务处理
#     # 从redis中取出真实的图片验证码
#     try:  # redis连接，可能网络发生故障，必须try起来
#         real_image_code = redis_store.get("image_code_%s" % image_code_id)
#     except Exception as e:
#         current_app.logger.error(e)
#         return jsonify(errno=RET.DBERR, errmsg="redis数据库异常")
#
#     # 判断图片验证码是否过期
#     if real_image_code is None:
#         # 表示图片验证码过期
#         return jsonify(errno=RET.NODATA, errmsg="图片验证码失效")
#
#     # 删除redis中的图片验证码，防止用户使用同一个图片验证码验证多次
#     try:
#         redis_store.delete("image_code_%s" % image_code_id)
#     except Exception as e:
#         current_app.logger.error(e)
#
#     # 与用户填写的值进行对比
#     if real_image_code.lower() != image_code.lower():
#         # 表示用户填写错误
#         return jsonify(errno=RET.DATAERR, errmsg="图片验证码错误")
#
#     # 判断对于这个手机号的操作，60秒内有记录就不接受处理
#     try:  # 获取不到说明没有记录，可以通过
#         send_flag = redis_store.get("send_sms_code_%s" % mobile)
#     except Exception as e:
#         current_app.logger.error(e)
#     else:
#         if send_flag is not None:
#             # 表示在60秒之前有记录
#             return jsonify(errno=RET.REQERR, errmsg="请60秒后进行重试")
#
#     # 判断手机号是否注册过
#     try:  # mysql连接，可能网络发生故障，必须try起来
#         user = User.query.filter_by(mobile=mobile).first()
#     except Exception as e:
#         current_app.logger.error(e)
#     else:
#         if user is not None:
#             # 表示手机号已经存在
#             return jsonify(errno=RET.DATAEXIST, errmsg="手机号已存在")
#
#     # 生成短信验证码: 000000~999999之间的数字
#     sms_code = "%06d" % random.randint(0, 999999)
#
#     # 保存真实的短信验证码到redis数据库
#     try:  # redis连接，可能网络发生故障，必须try起来   key        有效时间               短信验证码
#         redis_store.setex("sms_code_%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
#         # 保存发送给这个手机号的记录，防止用户在60秒反复发短信
#         redis_store.setex("send_sms_code_%s" % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
#     except Exception as e:
#         current_app.logger.error(e)
#         return jsonify(errno=RET.DBERR, errmsg="短信验证码异常")
#
#     # 发送短信
#     try:  # 云通讯连接，可能网络发生故障，必须try起来
#         ccp = CCP()
#         result = ccp.send_template_sms(mobile, [sms_code, int(constants.SMS_CODE_REDIS_EXPIRES/60)], 1)
#     except Exception as e:
#         current_app.logger.error(e)
#         return jsonify(errno=RET.THIRDERR, errmsg="发送短信失败")
#
#     # 4. 返回值
#     if result == 0:  # 云通讯的返回的值，代表用户收到验证码
#         # 发送成功
#         return jsonify(errno=RET.OK, errmsg="发送成功")
#     else:
#         return jsonify(errno=RET.THIRDERR, errmsg="发送失败")


# 短信验证码
# GET /api/v1.0/sms_codes/<mobile>?image_code=xxx&image_code_id=xxx
@api.route("/sms_codes/<re(r'1[34578]\d{9}'):mobile>")
def get_sms_code(mobile):
    """获取短信验证码"""
    # 1. 获取参数： 图片验证码和图片验证码的编号
    image_code = request.args.get("image_code")
    image_code_id = request.args.get("image_code_id")

    # 2. 校验参数
    if not all([image_code, image_code_id]):
        # 表示参数不完整
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 3. 业务处理
    # 从redis中取出真实的图片验证码
    try:  # redis连接，可能网络发生故障，必须try起来
        real_image_code = redis_store.get("image_code_%s" % image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="redis数据库异常")

    # 判断图片验证码是否过期
    if real_image_code is None:
        # 表示图片验证码过期
        return jsonify(errno=RET.NODATA, errmsg="图片验证码失效")

    # 删除redis中的图片验证码，防止用户使用同一个图片验证码验证多次
    try:
        redis_store.delete("image_code_%s" % image_code_id)
    except Exception as e:
        current_app.logger.error(e)

    # 与用户填写的值进行对比
    if real_image_code.lower() != image_code.lower():
        # 表示用户填写错误
        return jsonify(errno=RET.DATAERR, errmsg="图片验证码错误")

    # 判断对于这个手机号的操作，60秒内有记录就不接受处理
    try:  # 获取不到说明没有记录，可以通过
        send_flag = redis_store.get("send_sms_code_%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if send_flag is not None:
            # 表示在60秒之前有记录
            return jsonify(errno=RET.REQERR, errmsg="请60秒后进行重试")

    # 判断手机号是否注册过
    try:  # mysql连接，可能网络发生故障，必须try起来
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
    else:
        if user is not None:
            # 表示手机号已经存在
            return jsonify(errno=RET.DATAEXIST, errmsg="手机号已存在")

    # 生成短信验证码: 000000~999999之间的数字
    sms_code = "%06d" % random.randint(0, 999999)

    # 保存真实的短信验证码到redis数据库
    try:  # redis连接，可能网络发生故障，必须try起来   key        有效时间               短信验证码
        redis_store.setex("sms_code_%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        # 保存发送给这个手机号的记录，防止用户在60秒反复发短信
        redis_store.setex("send_sms_code_%s" % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="短信验证码异常")

    # 使用celery异步发送短信，delay函数钓鱼能后立即返回
    send_sms.delay(mobile, [sms_code, int(constants.SMS_CODE_REDIS_EXPIRES / 60)], 1)

    # 4. 返回值
    # 发送成功
    return jsonify(errno=RET.OK, errmsg="发送成功")
