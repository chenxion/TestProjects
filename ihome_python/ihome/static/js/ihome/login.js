function getCookie(name) {
    // 获取cookie
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function() {
    $("#mobile").focus(function(){
        $("#mobile-err").hide();
    });
    $("#password").focus(function(){
        $("#password-err").hide();
    });
    $(".form-login").submit(function(e){
        // 阻止表单按钮的默认行为
        e.preventDefault();
        mobile = $("#mobile").val();
        passwd = $("#password").val();
        if (!mobile) {
            $("#mobile-err span").html("请填写正确的手机号！");
            $("#mobile-err").show();
            return;
        } 
        if (!passwd) {
            $("#password-err span").html("请填写密码!");
            $("#password-err").show();
            return;
        }

        // 定义ajax向后端发送上下文
        var data = {
            mobile: mobile,
            password: passwd
        };

        // 上下文转换成json数据
        var jsonData = JSON.stringify(data);

        // 调用ajax向后端发送登录请求以及回调操
        $.ajax({
            url: "/api/v1.0/sessions",  // 发送的地址
            type: "post",            // 发送类型
            data: jsonData,          // 发送的数据
            contentType: "application/json", // 数据的类型：json
            dataType: "json",        // 要求后端回传过来的数据类型
            headers: {               // 请求头，将csrf_token放到请求头中，方便后端验证
                "X-CSRFToken": getCookie("csrf_token")
            },
            success: function (data) { // 发送成功，执行回调函数
                if (data.errno == "0") {
                    // 登录成功，跳转到主页
                    location.href = "/";
                }
                else {
                    // 其他错误信息，在页面中展示
                    $("#password-err span").html(data.errmsg);
                    $("#password-err").show()
                }
            }
        });
    });
});