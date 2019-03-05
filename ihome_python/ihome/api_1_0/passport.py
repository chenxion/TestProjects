# coding:utf-8
# 处理注册 登陆 认证相关的业务

from . import api  # 导入蓝图
from flask import request, jsonify, current_app, session  # 接收请求参数, 返回json数据, flask本身
from ihome.utils.response_code import RET  # 自定义状态码
from ihome import redis_store, db, constants  # 导入redis连接, 数据库, 常量文件
from ihome.models import User  # 导入用户模型类
from sqlalchemy.exc import IntegrityError  # 数据库出现重复键抛出异常
from werkzeug.security import generate_password_hash, check_password_hash  # 生成密码的哈希，检验密码的哈希
import re  # 导入正则


@api.route("/users", methods=["POST"])
def register():
    """注册
    请求的参数： 手机号 短信验证码 密码 确认密码
    参数格式： json
    """
    # 接收请求的json数据，返回字典
    req_dict = request.get_json()
    mobile = req_dict.get("mobile")
    sms_code = req_dict.get("sms_code")
    password = req_dict.get("password")
    password2 = req_dict.get("password2")

    # 校验参数
    if not all([mobile, sms_code, password, password2]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 判断手机号格式
    if not re.match(r"1[34578]\d{9}", mobile):
        # 表示格式不对
        return jsonify(errno=RET.PARAMERR, errmsg="手机号格式错误")

    if password != password2:
        return jsonify(errno=RET.PARAMERR, errmsg="两次密码不一致")

    # 从redis中取出短信验证码
    try:
        real_sms_code = redis_store.get("sms_code_%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="读取真实短信验证码异常")

    # 判断短信验证码是否过期
    if real_sms_code is None:
        return jsonify(errno=RET.NODATA, errmsg="短信验证码失效")

    # 删除redis中的短信验证码，防止重复使用
    try:
        redis_store.delete("sms_code_%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)

    # 判断用户填写的的短信验证码的正确性
    if real_sms_code != sms_code:
        return jsonify(errno=RET.DATAERR, errmsg="短信验证码错误")

    # 方法1： 需要查询数据库，影响性能
    # try:  判断用户的手机号是否注册过
    #     user = User.query.filter_by(mobile=mobile).first()
    # except Exception as e:
    #     current_app.logger.error(e)
    #     return jsonify(errno=RET.DBERR, errmsg="数据库异常")
    # else:
    #     if user is not None:
    #         # 表示手机号已经存在
    #         return jsonify(errno=RET.DATAEXIST, errmsg="手机号已存在")

    # 方法2： # 因为数据库手机号只能注册一个用户，重复会异常，所以跳过数据库查询
    user = User(name=mobile, mobile=mobile)  # 保存用户的注册数据到数据库中
    # user.generate_password_hash(password)  # 对密码进行sha256加密并保存到数据库
    user.password = password  # 设置属性,效果和上面相同
    try:
        db.session.add(user)
        db.session.commit()  # 提交事务
    except IntegrityError as e:
        db.session.rollback()  # 数据库错误，事务回滚，回到提交事务之前
        # 表示手机号出现了重复值，即手机已经注册过
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAEXIST, errmsg="手机号已存在")
    except Exception as e:
        db.session.rollback()  # 数据库错误，事务回滚，回到提交事务之前
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据库异常")

    # 保存登陆状态到session中
    session["name"] = mobile
    session["mobile"] = mobile
    session["user_id"] = user.id

    # 返回结果
    return jsonify(errno=RET.OK, errmsg="注册成功")


@api.route("/sessions", methods=["POST"])
def login():
    """用户登录
    参数： 手机号、密码， json
    """
    # 获取参数
    req_dict = request.get_json()
    mobile = req_dict.get("mobile")
    password = req_dict.get("password")

    # 校验参数
    # 参数完整的校验
    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 手机号的格式
    if not re.match(r"1[34578]\d{9}", mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号格式错误")

    # 判断错误次数是否超过限制，如果超过限制，则返回
    # redis记录： "access_nums_请求的ip": "次数"
    user_ip = request.remote_addr  # 用户的ip地址
    try:
        access_nums = redis_store.get("access_num_%s" % user_ip)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if access_nums is not None and int(access_nums) >= constants.LOGIN_ERROR_MAX_TIMES:
            return jsonify(errno=RET.REQERR, errmsg="错误次数过多，请稍后重试")

    # 从数据库中根据手机号查询用户的数据对象
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取用户信息失败")

    # 用数据库的密码与用户填写的密码进行对比验证
    if user is None or not user.check_password(password):
        # 如果验证失败，记录错误次数，返回信息
        try:
            # redis的incr可以对字符串类型的数字数据进行加一操作，如果数据一开始不存在，则会初始化为1
            redis_store.incr("access_num_%s" % user_ip)
            redis_store.expire("access_num_%s" % user_ip, constants.LOGIN_ERROR_FORBID_TIME)
        except Exception as e:
            current_app.logger.error(e)

        return jsonify(errno=RET.DATAERR, errmsg="用户名或密码错误")

    # 如果验证相同成功，保存登录状态， 在session中
    session["name"] = user.name
    session["mobile"] = user.mobile
    session["user_id"] = user.id

    return jsonify(errno=RET.OK, errmsg="登录成功")


@api.route("/sessions", methods=["GET"])
def check_login():
    """检查登陆状态"""
    # 尝试从session中获取用户的名字
    name = session.get("name")
    # 如果session中数据name名字存在，则表示用户已登录，否则未登录
    if name is not None:
        return jsonify(errno=RET.OK, errmsg="true", data={"name": name})
    else:
        return jsonify(errno=RET.SESSIONERR, errmsg="fales")


@api.route("/sessions", methods=["DELETE"])
def logout():
    """登出"""
    # 清除session数据
    # 解决登录退出后，csrf_token缺失的bug
    csrf_token = session.get("csrf_token")  # 先获取session里面的csrf
    session.clear()
    session["csrf_token"] = csrf_token  # 清除session之后，再将csrf设置回去
    return jsonify(errno=RET.OK, errmsg="OK")
