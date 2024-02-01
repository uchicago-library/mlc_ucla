$(document).ready(function(){
	var user_closed_c = parseInt(localStorage.getItem('timestamp_closed_campus_message'));
	var user_closed_r = parseInt(localStorage.getItem('timestamp_closed_restricted_message'));
	var current = new Date().getTime();
	var enough_time = 7889400000;
	var enough_c_time = user_closed_c && current>(user_closed_c+enough_time);
	var enough_r_time = user_closed_r && current>(user_closed_r+enough_time);
	
	if( user_closed_c && !enough_c_time){
		$('#alert-campus').alert('close');
	}else if( (user_closed_c && enough_c_time) || !user_closed_c ){
		$('#alert-campus').on('closed.bs.alert', function () {
			localStorage.setItem('timestamp_closed_campus_message', new Date().getTime())
		})
		if ( enough_c_time ){
			localStorage.removeItem('timestamp_closed_campus_message')
		}
	}

	if( user_closed_r && !enough_r_time){
		$('#alert-restricted').alert('close');
	}else if( (user_closed_r && enough_c_time) || !user_closed_r ){
		$('#alert-restricted').on('closed.bs.alert', function () {
			localStorage.setItem('timestamp_closed_restricted_message', new Date().getTime())
		})
		if ( enough_r_time ){
			localStorage.removeItem('timestamp_closed_restricted_message')
		}
	}

});
