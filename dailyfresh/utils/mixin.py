from django.contrib.auth.decorators import login_required
# 内部的登录认证系统，用户没有登录无法进行下一步操作
"""
UserOrderView(LoginRequiredMixin, View):  调用过程：
    1. 先调用 LoginRequiredMixin 里面的as_view() 方法，
       as_view() 方法又调用了super(LoginRequiredMixin, cls).as_view方法,也就是 UserInfoView.as_view方法等于(View.as_view)
    2. 用view接收了 UserInfoView.as_view()的返回值，最后用 login_required装饰器 进行了装饰返回给as_view()
    3. login_required(AddressView.as_view()) == UserOrderView(LoginRequiredMixin, View)
        view == AddressView.as_view() == UserInfoView.as_view() == UserOrderView.as_view()
"""


class LoginRequiredMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        # 调用cls的super的as_view方法
        # 调用cls(UserInfoView)的父类也就是View.as_view()方法
        #      super(LoginRequiredMixin, cls) = UserInfoView
        view = super(LoginRequiredMixin, cls).as_view(**initkwargs)
        # print("ssssssssssssssssssssss %s" % cls)
        return login_required(view)
