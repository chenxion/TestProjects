// 获取cookie中的token数据
function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

// 点击退出按钮时执行的函数
function logout() {
    // $.get("/api/logout", function(data){
    //     if (0 == data.errno) {
    //         location.href = "/";
    //     }
    // })
    $.ajax({
        url: "/api/v1.0/sessions",
        type: "delete",
        headers: {
            "X-CSRFToken": getCookie("csrf_token")
        },
        dataType: "json",
        success: function (resp) {
            // 后端将session里面的数据清空，返回ok，前端调用重定向到首页
            if ("0" == resp.errno) {
                location.href = "/index.html";
            }
        }
    });
}

$(document).ready(function(){
    $.get("/api/v1.0/user", function(resp){
        // 用户未登录
        if ("4101" == resp.errno) {
            location.href = "/login.html";
        }
        // 查询到了用户的信息
        else if ("0" == resp.errno) {
            $("#user-name").html(resp.data.name);
            $("#user-mobile").html(resp.data.mobile);
            if (resp.data.avatar) {
                $("#user-avatar").attr("src", resp.data.avatar);
            }

        }
    }, "json");
})