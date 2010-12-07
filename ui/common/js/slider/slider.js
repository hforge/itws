/*
 * jQuery ITWS slider
 *
 */

(function($) {
  var SliderITWS = function(element, options) {
    var default_vars = {
      width: 0,
      height: 0,
      currentSlide: 0,
      nbSlides: 0,
      images: new Array(),
      running: false
    };
    var vars = $.extend({}, default_vars, options);
    // Init slider
    var slider = $(element);
    slider.data('vars', vars);
    // Get kids
    var kids = $('a[rel="itws-slide"]');
    kids.each(function() {
      var child = $(this);
      child.css('display', 'block');
      $("img", child).css('display', 'none');
      vars.images.push(child);
      vars.nbSlides++;
    });
    // Set position of buttons
    $('.slider-itws-nav a').css('top', (vars.height-30)/2 + 'px');
    // Set first iteration background
    run(slider);
    // Bouton next
    $('a.next').bind('click', function() {
      go_next(slider);
    });
    // Bouton next
    $('a.previous').bind('click', function() {
      go_previous(slider);
    });
    // Navigation
    $('.slider-itws-nav').hide();
    slider.hover(function() {
      $('.slider-itws-nav').show();
    }, function(){
      $('.slider-itws-nav').hide();
    });
    // Run
    vars.timer = setInterval(function() { run(slider); }, 3000);
  }

  // == Go Next ==
  var go_next = function(slider) {
    var vars = slider.data('vars');
    if (vars.running) return false;
    clearInterval(vars.timer);
    vars.timer = '';
    run(slider);
  };

  // == Go previous ==
  var go_previous = function(slider, timer) {
    var vars = slider.data('vars');
    if (vars.running) return false;
    clearInterval(vars.timer);
    vars.timer = '';
    if (vars.currentSlide == 0) {
      vars.currentSlide = vars.nbSlides - 2;
    } else {
      vars.currentSlide -= 2;
    }
    if (vars.currentSlide < 0) {
      vars.currentSlide = (vars.nbSlides - 1);
    }
    run(slider);
  };

  // == RUN ==
  var run = function(slider) {
    var vars = slider.data('vars');
    vars.running = true;
    child = vars.images[vars.currentSlide];
    img = $("img", child);
    src = img.attr('src');
    title = img.attr('title');
    alt = img.attr('alt');
    $(".slider-link").attr('href', child.attr('href'));
    $(".slider-link").attr('target', child.attr('target'));
    $(".slider-itws-caption span").html(title);
    $(".slider-itws-caption p").html(alt);
    slider.css('background','url('+ src +') no-repeat');
    vars.currentSlide++;
    if (vars.currentSlide == vars.nbSlides) {
       vars.currentSlide = 0;
    }
    if (vars.timer == '') {
      vars.timer = setInterval(function() { run(slider); }, 3000);
    }
    vars.running = false;
  };

  $.fn.SliderITWS = function(options) {
    return this.each(function() {
      var element = $(this);
      var slideritws = new SliderITWS(this, options);
    });
  };

})(jQuery);
