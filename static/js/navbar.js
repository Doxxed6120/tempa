$(document).ready(function() {
  $(window).scroll(function() {
    if ($(this).scrollTop() > 0) {
      $('.navbar').addClass('bg-dark');
    } else {
      $('.navbar').removeClass('bg-dark');
    }
  });
});