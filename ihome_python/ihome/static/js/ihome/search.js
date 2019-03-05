var cur_page = 1;  // 全局变量，当前页数为1，后面会改变
var next_page = 1;  // 全局变量，下一页数为1，后面会改变
var total_page = 1;  // 全局变量，总页数为1，后面会改变
var house_data_querying = true;   // 全局变量，向后端获取查询数据，正在获取后端的查询请求时设为真，后端把数据发送过来之后设为假

// 解析url中的查询字符串
function decodeQuery(){
    var search = decodeURI(document.location.search);
    return search.replace(/(^\?)/, '').split('&').reduce(function(result, item){
        values = item.split('=');
        result[values[0]] = values[1];
        return result;
    }, {});
}

// 更新用户点选的筛选条件
function updateFilterDateDisplay() {
    var startDate = $("#start-date").val();
    var endDate = $("#end-date").val();
    var $filterDateTitle = $(".filter-title-bar>.filter-title").eq(0).children("span").eq(0);
    if (startDate) {
        var text = startDate.substr(5) + "/" + endDate.substr(5);
        $filterDateTitle.html(text);
    } else {
        $filterDateTitle.html("入住日期");
    }
}


// 更新房源列表信息
// action表示从后端请求的数据在前端的展示方式
// 默认采用追加方式
// action=renew 代表页面数据清空从新展示
function updateHouseData(action) {
    var areaId = $(".filter-area>li.active").attr("area-id");
    // 表示用户没有选择城区，设为空
    if (undefined == areaId) areaId = "";
    // 获取开始的时间
    var startDate = $("#start-date").val();
    // 获取结束的时间
    var endDate = $("#end-date").val();
    // 获取用户选择的排序方式
    var sortKey = $(".filter-sort>li.active").attr("sort-key");

    var params = {
        aid:areaId,  // 用户点击筛选的地区
        sd:startDate,  // 开始时间
        ed:endDate,  // 结束时间
        sk:sortKey,
        p:next_page
    };

    // 向后端发送请求，获取房屋数据
    $.get("/api/v1.0/houses", params, function(resp){
        house_data_querying = false;  // 表示上一次查询请求已经处理完了
        if ("0" == resp.errno) {
            if (0 == resp.data.total_page) {
                $(".house-list").html("暂时没有符合您查询的房屋信息。");
            } else {
                total_page = resp.data.total_page;
                // action=renew 代表页面数据清空重新展示页面
                if ("renew" == action) {
                    // 将当前页数改为1
                    cur_page = 1;
                    $(".house-list").html(template("house-list-tmpl", {houses:resp.data.houses}));
                }
                // 如果不是renew，就是追加，当前页数=刚刚请求的页数
                else {
                    cur_page = next_page;
                    $(".house-list").append(template("house-list-tmpl", {houses: resp.data.houses}));
                }
            }
        }
    })
}

$(document).ready(function(){
    // 解析url请求中的查询字符串参数
    var queryData = decodeQuery();
    var startDate = queryData["sd"];  // 获取开始时间
    var endDate = queryData["ed"];  // 获取结束时间
    $("#start-date").val(startDate);
    $("#end-date").val(endDate);
    updateFilterDateDisplay();
    var areaName = queryData["aname"];  // 获取城区
    if (!areaName) areaName = "位置区域";
    $(".filter-title-bar>.filter-title").eq(1).children("span").eq(0).html(areaName);


    // 获取筛选条件中的城市区域信息
    $.get("/api/v1.0/areas", function(data){
        if ("0" == data.errno) {
            // 用户从首页跳转到这个搜索页面时可能选择了城区，所以尝试从url的查询字符串参数中提取用户选择的城区
            var areaId = queryData["aid"];
            // 如果提取到了城区id的数据
            if (areaId) {
                // 遍历从后端获取到的城区信息，添加到页面中
                for (var i=0; i<data.data.length; i++) {
                    // 对于从url查询字符串参数中拿到的城区，在页面中做高亮展示
                    // 后端获取到城区id是整型，从url参数中获取到的是字符串类型，所以将url参数中获取到的转换为整型，再进行对比
                    areaId = parseInt(areaId);
                    if (data.data[i].aid == areaId) {
                        $(".filter-area").append('<li area-id="'+ data.data[i].aid+'" class="active">'+ data.data[i].aname+'</li>');
                    } else {
                        $(".filter-area").append('<li area-id="'+ data.data[i].aid+'">'+ data.data[i].aname+'</li>');
                    }
                }
            } else {
                // 如果url参数中没有城区信息，不需要做额外处理，直接遍历展示到页面中
                for (var i=0; i<data.data.length; i++) {
                    $(".filter-area").append('<li area-id="'+ data.data[i].aid+'">'+ data.data[i].aname+'</li>');
                }
            }
            // 因为是第一次请求，在页面添加好城区选项信息后，更新展示房屋列表信息
            updateHouseData("renew");
            // 获取页面显示窗口的高度
            var windowHeight = $(window).height();
            // 为窗口的滚动添加事件函数
            window.onscroll=function(){
                // var a = document.documentElement.scrollTop==0? document.body.clientHeight : document.documentElement.clientHeight;
                var b = document.documentElement.scrollTop==0? document.body.scrollTop : document.documentElement.scrollTop;
                var c = document.documentElement.scrollTop==0? document.body.scrollHeight : document.documentElement.scrollHeight;
                // 如果滚动到接近窗口底部
                if(c-b<windowHeight+50){
                    // 如果没有正在向后端发送查询房屋列表信息的请求
                    if (!house_data_querying) {  // 如果为假，表示现在页面没有向后端发送请求
                        // 将正在向后端查询房屋列表信息的标志设置为真，
                        house_data_querying = true;  // 先将设为真，表示现在页面有查询请求
                        // 如果当前页面数还没到达总页数
                        if(cur_page < total_page) {
                            // 将要查询的页数设置为当前页数加1
                            next_page = cur_page + 1;
                            // 向后端发送请求，查询下一页房屋数据
                            updateHouseData();
                        } else {
                            house_data_querying = false;
                        }
                    }
                }
            }
        }
    });

    $(".input-daterange").datepicker({
        format: "yyyy-mm-dd",
        startDate: "today",
        language: "zh-CN",
        autoclose: true
    });
    var $filterItem = $(".filter-item-bar>.filter-item");
    $(".filter-title-bar").on("click", ".filter-title", function(e){
        var index = $(this).index();
        if (!$filterItem.eq(index).hasClass("active")) {
            $(this).children("span").children("i").removeClass("fa-angle-down").addClass("fa-angle-up");
            $(this).siblings(".filter-title").children("span").children("i").removeClass("fa-angle-up").addClass("fa-angle-down");
            $filterItem.eq(index).addClass("active").siblings(".filter-item").removeClass("active");
            $(".display-mask").show();
        } else {
            $(this).children("span").children("i").removeClass("fa-angle-up").addClass("fa-angle-down");
            $filterItem.eq(index).removeClass('active');
            $(".display-mask").hide();
            updateFilterDateDisplay();
        }
    });
    // 用户点击筛选条件下面的灰色区域时(遮掩框)触发
    $(".display-mask").on("click", function(e) {
        $(this).hide();  // 隐藏遮掩框
        $filterItem.removeClass('active');
        updateFilterDateDisplay();  // 更新用户筛选好之后返回的结果
        cur_page = 1;  // 当前页数设为1
        next_page = 1;  // 将要查询的页数设为1
        total_page = 1;  // 总页数默认设为1
        updateHouseData("renew");  // 发送请求向后端获取数据

    });
    $(".filter-item-bar>.filter-area").on("click", "li", function(e) {
        if (!$(this).hasClass("active")) {
            $(this).addClass("active");
            $(this).siblings("li").removeClass("active");
            $(".filter-title-bar>.filter-title").eq(1).children("span").eq(0).html($(this).html());
        } else {
            $(this).removeClass("active");
            $(".filter-title-bar>.filter-title").eq(1).children("span").eq(0).html("位置区域");
        }
    });
    $(".filter-item-bar>.filter-sort").on("click", "li", function(e) {
        if (!$(this).hasClass("active")) {
            $(this).addClass("active");
            $(this).siblings("li").removeClass("active");
            $(".filter-title-bar>.filter-title").eq(2).children("span").eq(0).html($(this).html());
        }
    })
})