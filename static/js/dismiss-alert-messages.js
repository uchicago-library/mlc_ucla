$(document).ready(function(){
	var pdata = $('#panopto-data').data();

	function show_help(){
		$('#panopto-help').removeClass('hidden')
		.on('click', function (){
			show_alert();
			$('#panopto-help').addClass('hidden');
		});
	}

	function show_alert(){
		// console.log('show_alert');
		//alert alert-warning alert-dismissible fade in
		var alert;
		var help_btn = $('#close-panopto-alert');
		var user_var;
		if(pdata.rights == 'campus'){
			alert = $('#alert-campus');
			user_var = "timestamp_closed_campus_message";
		}else if(pdata.rights == 'restricted'){
			alert = $('#alert-restricted');
			user_var = "timestamp_closed_restricted_message";
		}
		window.localStorage.removeItem(user_var);

		alert.removeClass('hidden');
		help_btn.on('click', function () {
			alert.removeClass('hidden');
			alert.addClass('hidden');
			window.localStorage.setItem(user_var, new Date().getTime());
			show_help();
		});
	}

	if(pdata.identifier){
		var user_closed;
		if(pdata.rights == 'campus'){
			user_closed = parseInt(window.localStorage.getItem('timestamp_closed_campus_message'));
		}else if(pdata.rights == 'restricted'){
			user_closed = parseInt(window.localStorage.getItem('timestamp_closed_restricted_message'));
		}

		// console.log('user_closed: '+user_closed);
		if( user_closed && ( pdata.rights == 'restricted' || pdata.rights == 'campus' )){
			show_help();
		}else{
			show_alert();
		}
	}
});
