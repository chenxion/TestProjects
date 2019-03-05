# coding:utf-8

from . import api
from ihome import db, models
import logging
from flask import current_app  # 全局应用对象


@api.route('/index')
def index():
    # logging.error(" ")  # 错误级别
    # logging.warn(" ")  # 警告级别
    # logging.info(" ")  # 消息提示级别
    # logging.debug(" ")  # 调试级别
    current_app.logger.error()
    return "index page"