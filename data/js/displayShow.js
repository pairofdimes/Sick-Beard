$(document).ready(function(){

  $('#changeStatus').click(function(){
  
    var epArr = new Array()

    $('.epCheck').each(function() {
      
      if (this.checked == true) {
        epArr.push($(this).attr('id'))
      }
      
    });  

    if (epArr.length == 0)
      return false

    url = 'setStatus?show='+$('#showID').attr('value')+'&eps='+epArr.join('|')+'&status='+$('#statusSelect').attr('value')

    window.location.href = url

  });

  $('.seasonCheck').click(function(){
    
    var seasCheck = this;
    var seasNo = $(seasCheck).attr('id');

    $('.epCheck').each(function(){
      var epParts = $(this).attr('id').split('x')

      if (epParts[0] == seasNo) {
        this.checked = seasCheck.checked 
      } 
    });
  });

  // edit in place with fallback if no javascript
  $('#editShowButton').live('click',function(e){		// load edit form
    $('#showStaticInfo').load($(e.target).attr('href') +' #showEditInfo', function(){
	    var cancelButton = $('<a href="displayShow?show='+ $('#showID').attr('value')+'" id="cancelEditShowButton" style="text-decoration:underline">Cancel</a>');
	    $(cancelButton).appendTo($('#showStaticInfo'));
  		$('#location').fileBrowser({ title: 'Select Show Location' });
	});
    return false;
  });
  $('#cancelEditShowButton').live('click',function(e){	// cancel changes
    $('#showStaticInfo').load($(e.target).attr('href') +' #showStaticInfo');
    return false;
  });

});
