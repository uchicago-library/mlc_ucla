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
		if(pdata.rights == 'campus'){
			console.log('rights= campus');
			$('#alert-campus').removeClass('hidden');
			$('#alert-campus .close').on('click', function () {
				$('#panopto-help').removeClass('hidden');
				$('#alert-campus').addClass('hidden');
				window.localStorage.setItem('timestamp_closed_campus_message', new Date().getTime());
				console.log('close alert');
				show_help();
			});
			window.localStorage.removeItem('timestamp_closed_campus_message');
		}else if(pdata.rights == 'restricted'){
			console.log('rights= restricted');
			$('#alert-restricted').removeClass('hidden');
			$('#alert-restricted .close').on('closed.bs.alert', function () {
				$('#panopto-help').removeClass('hidden');
				$('#alert-restricted').addClass('hidden');
				window.localStorage.setItem('timestamp_closed_restricted_message', new Date().getTime());
				console.log('close alert');
				show_help();
			});
			window.localStorage.removeItem('timestamp_closed_restricted_message');
		}
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
