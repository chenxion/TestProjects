function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function(){
    // ajax的get方式向后端获取城区信息
    $.get("/api/v1.0/areas", function (resp) {
        if (resp.errno == "0") {
            var areas = resp.data;
            // // 循环data字典,取出每一个城区：area
            // for (i=0; i<areas.length; i++) {
            //     var area = areas[i];
            //     $("#area-id").append('<option value="' + area.aid + '">' + area.aname + '</option>')
            // }

            // 使用js模板 art-template模板
            // 选择 id=areas-tmpl的模板，把areas数据传给模板进行渲染
            var html = template("areas-tmpl", {areas: areas});
            // 将模板渲染的结果传给 id=area-id 的这个标签
            $("#area-id").html(html);
        }
        else {
            alert(resp.errmsg);
        }

    }, "json");

    $("#form-house-info").submit(function (e) {
        e.preventDefault();
        // 定义空字典
        var data = {};
        // 获取表单所有输入的值通过map映射将name的值和value的值转换成了字典：{data.name=value}
        $("#form-house-info").serializeArray().map(function (x) {
            data[x.name] = x.value
        });
        // 定义空列表
        var facility = [];
        // 获取名字facility的复选框，遍历出来x是每一个复选框的值添加到列表里面
        $(":checked[name=facility]").each(function (index, x) {
            facility[index] = $(x).val()
        });
        // 在字典里面添加一个facility字段，值是facility列表
        data.facility = facility;

        // 向后端发送请求
        $.ajax({
            url: "/api/v1.0/houses/info",
            type: "post",
            contentType: "application/json",
            data: JSON.stringify(data),
            dataType: "json",
            headers: {
                "X-CSRFToken": getCookie("csrf_token")
            },
            success: function (resp) {
                if (resp.errno == "4101") {
                    // 用户未登录
                    location.href = "/login.html";
                }
                else if (resp.errno == "0") {
                    // 隐藏基本信息表单
                    $("#form-house-info").hide();
                    // 显示图片表单
                    $("#form-house-image").show();
                    // 设置图片表单中的house_id
                    $("#house-id").val(resp.data.house_id)
                }
                else {
                    alert(resp.errmsg);
                }
            }
        })
    });
    $("#form-house-image").submit(function (e) {
        e.preventDefault();
        $(this).ajaxSubmit({
            url: "/api/v1.0/houses/image",
            type: "post",
            dataType: "json",
            headers: {
                "X-CSRFToken": getCookie("csrf_token"),
            },
            success: function (resp) {
                if (resp.errno == "4101") {
                    location.href = "/login.html";
                }
                else if (resp.errno == "0") {
                    $(".house-image-cons").append('<img src="' + resp.data.image_url + '">');
                }
                else {
                    alert(resp.errmsg)
                }
            }
        })
    })
});