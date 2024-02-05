$(document).ready(function(){
	var pdata = $('#panopto-data').data();
	var enough_time = 7889400000;
	var current = new Date().getTime();
	if(pdata.identifier){

		if(pdata.rights == 'campus'){
			var user_closed_c = parseInt(window.localStorage.getItem('timestamp_closed_campus_message'));
			var enough_c_time = user_closed_c && current>(user_closed_c+enough_time);

			if( user_closed_c && !enough_c_time){
				$('#panopto-help').removeClass('hidden');
			}
			if( (user_closed_c && enough_c_time) || !user_closed_c ){
				$('#alert-campus').removeClass('hidden')
				.on('closed.bs.alert', function () {
					window.localStorage.setItem('timestamp_closed_campus_message', new Date().getTime());
				});
				window.localStorage.removeItem('timestamp_closed_campus_message');
			}

		}else if(pdata.rights == 'restricted'){
			var user_closed_r = parseInt(window.localStorage.getItem('timestamp_closed_restricted_message'));
			var enough_r_time = user_closed_r && current>(user_closed_r+enough_time);

			if( user_closed_r && !enough_r_time){
				$('#panopto-help').removeClass('hidden');
			}
			if( (user_closed_r && enough_r_time) || !user_closed_r ){
				$('#alert-restricted').removeClass('hidden')
				.on('closed.bs.alert', function () {
					window.localStorage.setItem('timestamp_closed_restricted_message', new Date().getTime());
				});
				window.localStorage.removeItem('timestamp_closed_restricted_message');
			}

		}
		$('#panopto-help').on('click', function (){
			window.localStorage.removeItem('timestamp_closed_campus_message');
			window.localStorage.removeItem('timestamp_closed_restricted_message');
			$('#alert-campus').removeClass('hidden');
			$('#alert-restricted').removeClass('hidden');
			$('#panopto-help').addClass('hidden');
		});
	}
});
