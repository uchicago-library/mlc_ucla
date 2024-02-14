$(document).ready(function(){
	var pdata = $('#panopto-data').data();
	var enough_time = 31536000000; // one year in millisecnods - 365*24*60*60*1000
	var current = new Date().getTime();

	function show_help(){
		$('#panopto-help').removeClass('hidden')
		.on('click', function (){
			show_alert();
			$('#panopto-help').addClass('hidden');
		});
	}

	function show_alert(){
		if(pdata.rights == 'campus'){
			$('#alert-campus').removeClass('hidden')
			.on('closed.bs.alert', function () {
				$('#panopto-help').removeClass('hidden');
				bind_help();
				window.localStorage.setItem('timestamp_closed_campus_message', new Date().getTime());
			});
			window.localStorage.removeItem('timestamp_closed_campus_message');
		}else if(pdata.rights == 'restricted'){
			$('#alert-restricted').removeClass('hidden')
			.on('closed.bs.alert', function () {
				$('#panopto-help').removeClass('hidden');
				bind_help();
				window.localStorage.setItem('timestamp_closed_restricted_message', new Date().getTime());
			});
			window.localStorage.removeItem('timestamp_closed_restricted_message');

		}
	}

	if(pdata.identifier){
		var user_closed;
		var is_enough_time;
		if(pdata.rights == 'campus'){
			user_closed = parseInt(window.localStorage.getItem('timestamp_closed_campus_message'));
		}else if(pdata.rights == 'restricted'){
			user_closed = parseInt(window.localStorage.getItem('timestamp_closed_restricted_message'));
		}
		is_enough_time = user_closed && current>(user_closed+enough_time);
		// user has closed the message before
		if( user_closed && !is_enough_time){
			show_help();
		}
		// user has closed the message before, but enough time has ellapsed
		// OR user did not close dismiss the message before
		if( (user_closed && is_enough_time) || !user_closed ){
			show_alert();
		}

	}
});
