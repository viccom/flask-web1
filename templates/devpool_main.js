<script type="text/javascript">
function generateUUID() {
    var d = new Date().getTime();
    var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      var r = (d + Math.random()*16)%16 | 0;
      d = Math.floor(d/16);
      return (c=='x' ? r : (r&0x3|0x8)).toString(16);
    });
    return uuid;
};

function uuid(len, radix) {
    var chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'.split('');
    var uuid = [], i;
    radix = radix || chars.length;

    if (len) {
    // Compact form
    for (i = 0; i < len; i++) uuid[i] = chars[0 | Math.random()*radix];
    } else {
    // rfc4122, version 4 form
    var r;

    // rfc4122 requires these characters
    uuid[8] = uuid[13] = uuid[18] = uuid[23] = '-';
    uuid[14] = '4';

    // Fill in random data. At i==19 set the high bits of clock sequence as
    // per rfc4122, sec. 4.1.5
    for (i = 0; i < 36; i++) {
    if (!uuid[i]) {
     r = 0 | Math.random()*16;
     uuid[i] = chars[(i == 19) ? (r & 0x3) | 0x8 : r];
    }
    }
    }

    return uuid.join('');
}
var pdict = {{protocoldict|safe}};
var iodevinfodict = {{iodevinfodict|safe}};
var table = $('#example').DataTable( {
        "ajax": {
            "url": '/get_devtags',
            "dataSrc": "tags"
        },
        "columns": [
            { "data": "tagname" },
            { "data": "tagdesc" },
            { "data": "fc" },
            { "data": "reg" },
            { "data": "datatype" },
        ]
    } );


function initialise() {

$("div .search-thumbnail").each(function(){
    $(this).click(function(){
        var devid = $(this).attr("data-devid");
        console.log(devid);
        if(devid!="newadd"){
          $.getJSON("/get_devinfo/"+devid,function(r){
              console.log(r);
              $("#dev-objid").val(devid);
              $("#dev-type").val(r.basic_info.dev_type);
              $("#dev-manuf").val(r.basic_info.dev_manufacturer);
              $("#dev-model").val(r.basic_info.dev_model);

              current_selected = r.Protocol_paramter.Protocol_Name;
              $('#Protocol_Name').val(current_selected);
            $("#protocolsetting_extend").empty();
            $("#protocolsetting_extend").append('<div class="col-xs-12 col-sm-6 col-lg-6"><div class="form-group"><label class="col-sm-3 control-label no-padding-right" for="form-field-1"> 协议版本 </label><div class="col-sm-9"><input type="text" id="Protocol_ver" placeholder="Protocol_ver" value="'+ r.Protocol_paramter.Protocol_ver+'" class="col-xs-10 col-sm-5" /></div></div></div>');

            var arr = r.Protocol_paramter.extend_parameter;
            $.each(arr, function(i, v) {
                //console.log(arr[i].name);
                //console.log(arr[i].parameter);
                $("#protocolsetting_extend").append('<div class="col-xs-12 col-sm-6 col-lg-6"><div class="form-group"><label class="col-sm-3 control-label no-padding-right" for="form-field-1"> '+arr[i].name+'</label><div class="col-sm-9"><input type="text" id="dev-type" placeholder="" value="'+arr[i].parameter+'" class="col-xs-10 col-sm-5" /></div></div></div>');
            });

            $('#id-message-new-navbar').removeClass('hide');
            $('#id-dev-form').removeClass('hide');

            $('#id-message-list-navbar').addClass('hide');
            $('#message-list').addClass('hide');

                table.ajax.url("/get_devtags?devname="+devid).load();


          });

        }

    });
});

$("div#devcontainer").each(function(){
    $(this).mouseenter(function(){
        //console.log($(this).find(".my_float_div"));
      $(this).find(".my_float_div").removeClass('hidden');
    });
    $(this).mouseleave(function(){
      $(this).find(".my_float_div").addClass('hidden');
    });
});

$("div .my_float_div").each(function(){
    $(this).click(function(){
      var devid = $(this).attr("data-devid");
      var pid = $(this).parent();
      $.post("/deldev/"+devid,function(r,status){
        var  ret = JSON.parse(r)
        console.log(ret.message);
        console.log("del "+devid+" successful");
        if(ret.message=="del "+devid+" successful"){
              pid.remove();
        }
        //console.log(status);
      });

    });
});

}


var app = new Vue({
    el: '#devinfovm',
    data: {
        dev_type: '',
        dev_manufacturer: '',
        dev_model: '',
    }
});


jQuery(function($){

	//handling tabs and loading/displaying relevant messages and forms
	//not needed if using the alternative view, as described in docs


	//check/uncheck all messages
	$('#id-toggle-all').removeAttr('checked').on('click', function(){
		if(this.checked) {
			Inbox.select_all();
		} else Inbox.select_none();
	});

	//select all
	$('#id-select-message-all').on('click', function(e) {
		e.preventDefault();
		Inbox.select_all();
	});

	//select none
	$('#id-select-message-none').on('click', function(e) {
		e.preventDefault();
		Inbox.select_none();
	});

	//select read
	$('#id-select-message-read').on('click', function(e) {
		e.preventDefault();
		Inbox.select_read();
	});

	//select unread
	$('#id-select-message-unread').on('click', function(e) {
		e.preventDefault();
		Inbox.select_unread();
	});

	/////////
	$('#creat_devid').on('click', function(e) {
		var devid=uuid(10,16);
		console.log(devid);
		$('#dev-objid').val(devid);
	});

	//hide message list and display new message form

	$('#add_device').on('click', function(e){
		//e.preventDefault();
		//Inbox.show_form();
        var devid = uuid(10,16);
        $('#dev-objid').val(devid);

		$('#id-message-new-navbar').removeClass('hide');
		$('#id-dev-form').removeClass('hide');

		$('#id-message-list-navbar').addClass('hide');
		$('#message-list').addClass('hide');
		$('#modify_devinfo').addClass('hide');
		$('#del_devinfo').addClass('hide');
		$('div .messagebar-item-left').addClass('hide');
		$('div .messagebar-item-right').addClass('hide');

	});


	//show message list and hide new message form

	$('#discard_devinfo').on('click', function(e){
		//alert("选中了!");
		$('#id-message-new-navbar').addClass('hide');
		$('#id-dev-form').addClass('hide');

		$('#id-message-list-navbar').removeClass('hide');
		$('#message-list').removeClass('hide');

		$('#creatnewdev').removeClass('active');
		$('#localdevpool').addClass('active');
		$('#clouddevpool').removeClass('active');

	});


    initialise();

    $('#upJQuery').on('click', function() {
        var devid  = $("#dev-objid").val();
        var fd = new FormData();
        var uploaddata = $("#fileupload").get(0).files[0];
        console.log(uploaddata);
        if(uploaddata){
            fd.append("upload", 1);
            fd.append("upfile", uploaddata);
             $.ajax({
                url: "/upload/"+devid,
                type: "POST",
                processData: false,
                contentType: false,
                data: fd,
                success: function(d) {
                    console.log(d);
                    table.ajax.url("/upload/"+devid).load();
                }
             });
        }
        else{
            console.log("请选择文件");
        }

    });

    table.on( 'draw', function () {
        console.log( 'Table redrawn' );
    } );

	$('#getdata').on( 'click', function () {
	    var alldata=$('#example').dataTable().fnGetData();//获取表格所有数据
        console.log(alldata);
	} );

	$('#downloadtable').on( 'click', function () {
        var devname = "dfg234d13wqs";
         location.href = "/downtable/"+devname;
	} );


	$('#save_devinfo').on('click', function() {
	    var devinfopost = {};
	    //var devid  = $("#dev-objid").val();
	    var protocolname = $('#Protocol_Name').children('option:selected').val();
	    if(!protocolname){
	        alert("请选择协议名称！")
        }
	    else{
	    //console.log(devid);
	    //console.log(pdict);
	    //console.log(iodevinfodict);
	    //devinfolable = $("div#devinfo,lable");
	    //console.log(devinfolable);
	    var devbasicinfo = $("div#devinfo :text");
	    var compresult = true;
        for(var i = 0;i < 4; i++) {
	        console.log(devbasicinfo[i].value);
	        compresult = compresult && devbasicinfo[i].value;
        }
        console.log("fanaly",compresult);
        if(!compresult){
            alert("请填写所有必填项！")
        }
        else{
                //protocolsettinglable = $("div#protocolsetting,lable");
                devinfopost.devid = devbasicinfo[0].value;
                devinfopost.devinfo = {};
                devinfopost.devinfo.basic_info = {};
                devinfopost.devinfo.basic_info.dev_type = devbasicinfo[1].value;
                devinfopost.devinfo.basic_info.dev_manufacturer = devbasicinfo[2].value;
                devinfopost.devinfo.basic_info.dev_model = devbasicinfo[3].value;

                var protocolsetting = $("div#protocolsetting :text");
                devinfopost.devinfo.Protocol_paramter = {};
                devinfopost.devinfo.Protocol_paramter.Protocol_Name = protocolname;
                devinfopost.devinfo.Protocol_paramter.Protocol_ver = String(protocolsetting[0].value);
                devinfopost.devinfo.Protocol_paramter.extend_parameter = [];

                var e_p_arr = pdict[protocolname].extend_parameter;
                $.each(e_p_arr, function(i, v) {
                    devinfopost.devinfo.Protocol_paramter.extend_parameter[i]={};
                    devinfopost.devinfo.Protocol_paramter.extend_parameter[i].name = String(e_p_arr[i].name);
                    devinfopost.devinfo.Protocol_paramter.extend_parameter[i].parameter = String(protocolsetting[i+1].value);
                    //console.log(arr[i].name);
                    //console.log(arr[i].parameter);
                 });


                console.log(devinfopost);

                  $.post("/adddev/"+devbasicinfo[0].value,JSON.stringify(devinfopost),function(result,status){
                    console.log(result);
                    if(result){
                        console.log("增加DIV");
                        $("#last_div_add_device").before('<div class="col-xs-6 col-sm-4 col-md-3" id="devcontainer">' +
                            '<div class="my_float_div hidden" data-devid="'+devinfopost.devid+'"><i class="ace-icon fa fa-trash fa-lg red"></i></div>' +
                            '<div class="thumbnail search-thumbnail"  data-devid="'+devinfopost.devid+'"><div class="caption"><div class="clearfix">' +
                            '<span class="pull-right label label-grey info-label">'+devinfopost.devinfo.Protocol_paramter.Protocol_Name+'</span><div class="pull-left bigger-110">' +
                            '<p>'+devinfopost.devinfo.basic_info.dev_manufacturer+'</p></div> </div><h3 class="search-title"><a href="#" class="blue">'+
                            devinfopost.devinfo.basic_info.dev_type+'</a></h3><p>'+devinfopost.devinfo.basic_info.dev_model+'</p></div> </div> </div>');

                        initialise();
                    }



                    //console.log(status);
                  });
            }
/*
	       $.ajax({
            //提交数据的类型 POST GET
            type:"POST",
            //提交的网址
            url:"/adddev/"+devbasicinfo[0].value,
            //提交的数据
            data:JSON.stringify(devinfopost),
            //返回数据的格式
            datatype: "json",//"xml", "html", "script", "json", "jsonp", "text".
            //在请求之前调用的函数
            beforeSend:console.log("开始发送"),
            //成功返回之后调用的函数
            success:function(result){
                console.log(result);
            },
            //调用执行后调用的函数
            complete: function(XMLHttpRequest, textStatus){
                console.log(XMLHttpRequest);
                console.log(textStatus);
                //HideLoading();
            },
            //调用出错执行的函数
            error: function(){
                //请求出错处理
            }
         });
*/

/*        $.each(devinfolable, function(i, v) {
            console.log(devinfolable[i].innerText);
        });*/

/*        $.each(devbasicinfo, function(i, v) {
            console.log(devbasicinfo[i].value);
        });*/


        //console.log(protocolname);
/*        $.each(protocolsettinglable, function(i, v) {
            console.log(protocolsettinglable[i].innerText);
        });*/

        }

    });


	$('#Protocol_Name').change(function(){

        var p1=$(this).children('option:selected').val();//这就是selected的值
        //console.log(p1);
        //console.log(pdict[p1]);


        $("#protocolsetting_extend").empty();
        $("#protocolsetting_extend").append('<div class="col-xs-12 col-sm-6 col-lg-6"><div class="form-group"><label class="col-sm-3 control-label no-padding-right" for="form-field-1"> 协议版本 </label><div class="col-sm-9"><input type="text" id="Protocol_ver" placeholder="Protocol_ver" value="'+ pdict[p1].Protocol_ver+'" class="col-xs-10 col-sm-5" /></div></div></div>');

        var arr = pdict[p1].extend_parameter;
        $.each(arr, function(i, v) {
            //console.log(arr[i].name);
            //console.log(arr[i].parameter);
            $("#protocolsetting_extend").append('<div class="col-xs-12 col-sm-6 col-lg-6"><div class="form-group"><label class="col-sm-3 control-label no-padding-right" for="form-field-1"> '+arr[i].name+'</label><div class="col-sm-9"><input type="text" id="dev-type" placeholder="'+arr[i].parameter+'" class="col-xs-10 col-sm-5" /></div></div></div>');
        });


})
});
</script>