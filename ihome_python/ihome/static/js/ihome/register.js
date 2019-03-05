// js读取cookie的方法，正则匹配 \\b：单词边界，只匹配name开头
function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    // r为真返回数据，为假返回undefined(none)
    return r ? r[1] : undefined;
}

// 保存之后生成的图片验证码编号
var imageCodeId = "";

function generateUUID() {  // uuid 生成一个图片验证码编号
    var d = new Date().getTime();
    if(window.performance && typeof window.performance.now === "function"){
        d += performance.now(); //use high-precision timer if available
    }
    var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = (d + Math.random()*16)%16 | 0;
        d = Math.floor(d/16);
        return (c=='x' ? r : (r&0x3|0x8)).toString(16);
    });
    return uuid;
}

function generateImageCode() {
    // 形成图片验证码的后端地址， 设置到页面中，让浏览请求验证码图片
    // 1. 生成图片验证码编号
    imageCodeId = generateUUID();
    // 是指图片url
    var url = "/api/v1.0/image_codes/" + imageCodeId;
    $(".image-code img").attr("src", url);
}

function sendSMSCode() {
    // 点击发送短信验证码后被执行的函数
    $(".phonecode-a").removeAttr("onclick");
    var mobile = $("#mobile").val();
    if (!mobile) {
        $("#mobile-err span").html("请填写正确的手机号！");
        $("#mobile-err").show();
        $(".phonecode-a").attr("onclick", "sendSMSCode();");
        return;
    }
    var imageCode = $("#imagecode").val();
    if (!imageCode) {
        $("#image-code-err span").html("请填写验证码！");
        $("#image-code-err").show();
        $(".phonecode-a").attr("onclick", "sendSMSCode();");
        return;
    }

    // 构造向后端请求的参数
    var req_data = {
        image_code: imageCode,  // 图片验证码的值
        image_code_id: imageCodeId  // 图片验证码的编号 (全局变量)
    };

    // 向后端发送请求
    $.get("/api/v1.0/sms_codes/" + mobile, req_data, function (resp) {
        // resp是后端返回的响应值，ajax的json值
        if (resp.errno == "0") {
            var num = 60;
            // 表示发送成功, 创建一个定时器：60秒
            var timer = setInterval(function () {
                if (num > 1) {
                    // 修改倒计时文本
                    $(".phonecode-a").html(num + "秒");
                    num -= 1;
                } else {
                    $(".phonecode-a").html("获取验证码");
                    $(".phonecode-a").attr("onclick", "sendSMSCode();");
                    clearInterval(timer);  // 清除定时器
                }
            }, 1000, 60);  // 定时间每1秒执行一次
        } else {
            // 表示发送失败
            alert(resp.errmsg);
            $(".phonecode-a").attr("onclick", "sendSMSCode();");
        }
    });
}

$(document).ready(function() {
    // 页面加载时，自动生成图片验证码
    generateImageCode();
    // 页面加载时，先自动隐藏下面的错误信息，用户做出错误操作显示出来
    $("#mobile").focus(function(){
        $("#mobile-err").hide();
    });
    $("#imagecode").focus(function(){
        $("#image-code-err").hide();
    });
    $("#phonecode").focus(function(){
        $("#phone-code-err").hide();
    });
    $("#password").focus(function(){
        $("#password-err").hide();
        $("#password2-err").hide();
    });
    $("#password2").focus(function(){
        $("#password2-err").hide();
    });

    // 修改了表单提交的行为，补充自定义的函数行为   (提交事件e)
    $(".form-register").submit(function(e){
        // 阻止浏览器对于表单的默认自动提交行为
        e.preventDefault();
        // 点击提交按钮时，执行一下行为
        var mobile = $("#mobile").val();
        var phoneCode = $("#phonecode").val();
        var passwd = $("#password").val();
        var passwd2 = $("#password2").val();
        if (!mobile) {
            $("#mobile-err span").html("请填写正确的手机号！");
            $("#mobile-err").show();
            return;
        } 
        if (!phoneCode) {
            $("#phone-code-err span").html("请填写短信验证码！");
            $("#phone-code-err").show();
            return;
        }
        if (!passwd) {
            $("#password-err span").html("请填写密码!");
            $("#password-err").show();
            return;
        }
        if (passwd != passwd2) {
            $("#password2-err span").html("两次密码不一致!");
            $("#password2-err").show();
            return;
        }

        // 定义ajax向后端发送上下文
        var req_data = {
            mobile: mobile,
            sms_code: phoneCode,
            password: passwd,
            password2: passwd2
        };

        // 上下文转换成json数据
        var req_json = JSON.stringify(req_data);

        // 调用ajax向后端发送注册请求以及回调操作
        $.ajax({
            url: "/api/v1.0/users",  // 发送的地址
            type: "post",            // 发送类型
            data: req_json,          // 发送的数据
            contentType: "application/json", // 数据的类型：json
            dataType: "json",        // 要求后端回传过来的数据类型
            headers: {               // 请求头，将csrf_token放到请求头中，方便后端验证
                "X-CSRFToken": getCookie("csrf_token")

            },
            success: function (resp) { // 发送成功，执行回调函数
                if (resp.errno == "0") {
                    // 注册成功，跳转到主页
                    location.href = "/index.html";
                } else {
                    alert(resp.errmsg);
                }
            }
        })
    });
})