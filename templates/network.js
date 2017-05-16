<script type="text/javascript">
jQuery(function($){

    var tagdata = {{ newtags|safe }};
    console.log(tagdata);
    $('#example').DataTable( {
        "ajax": {
            "url": '/upload',
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

    var table = $('#example').DataTable();

    $('#upJQuery').on('click', function() {
        var fd = new FormData();
        var uploaddata = $("#fileupload").get(0).files[0];
        console.log(uploaddata);
        if(uploaddata){
            fd.append("upload", 1);
            fd.append("upfile", uploaddata);
             $.ajax({
                url: "/upload",
                type: "POST",
                processData: false,
                contentType: false,
                data: fd,
                success: function(d) {
                    console.log(d);
                    table.ajax.url('/upload').load();
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

});


</script>