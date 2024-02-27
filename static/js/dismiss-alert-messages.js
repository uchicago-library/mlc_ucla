$(document).ready(function(){
	var pdata = $('#panopto-data').data();
	var enough_time = 31536000000; // one year in millisecnods - 365*24*60*60*1000
	var current = new Date().getTime();

	function show_help(){
		console.log('show_help');
		$('#panopto-help').removeClass('hidden')
		.on('click', function (){
			console.log('click help');
			show_alert();
			$('#panopto-help').addClass('hidden');
		});
	}

	function show_alert(){
		console.log('show_alert');
		//alert alert-warning alert-dismissible fade in
		var alert;
		var help_btn = $('#close-panopto-alert');
		var user_var;
		if(pdata.rights == 'campus'){
			console.log('rights= campus');
			alert = $('#alert-campus');
			user_var = "timestamp_closed_campus_message";
		}else if(pdata.rights == 'restricted'){
			console.log('rights= restricted');
			alert = $('#alert-restricted');
			user_var = "timestamp_closed_restricted_message";
		}

		alert.removeClass('hidden');
		help_btn.on('click', function () {
			alert.removeClass('hidden');
			alert.addClass('hidden');
			console.log('user_var: '+user_var);
			window.localStorage.setItem(user_var, new Date().getTime());
			console.log('closed value: '+parseInt(window.localStorage.getItem(user_var)));
			console.log('close alert');
			show_help();
		});
		window.localStorage.removeItem(user_var);
	}

	if(pdata.identifier){
		var user_closed;
		if(pdata.rights == 'campus'){
			user_closed = parseInt(window.localStorage.getItem('timestamp_closed_campus_message'));
		}else if(pdata.rights == 'restricted'){
			user_closed = parseInt(window.localStorage.getItem('timestamp_closed_restricted_message'));
		}
		console.log('user_closed: '+user_closed);
		if( user_closed ){
			console.log('user closed');
			show_help();
		}else{
			console.log('user NOT closed');
			show_alert();
		}
	}
});
