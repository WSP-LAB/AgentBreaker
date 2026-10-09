/**
 * @file
 * JavaScript general hacks.
 */
// Global function
function ShowHide (id) {
  jQuery('#' + id).toggle()
}

(function ($, Drupal) {
  'use strict';

  // Adding aria attributes for Google Captcha.
  var setCaptchaAttributes = function () {
    var textarea = [];
    textarea = document.getElementById("g-recaptcha-response");
    if(textarea === null) {
      return;
    }
    textarea.setAttribute("aria-hidden", "true");
    textarea.setAttribute("aria-label", "Captcha Textarea");
    textarea.setAttribute("aria-readonly", "true");
  };

  function actionCollapse(action) {
    $('.block-mta-info .main-level-collapse').collapse(action);
  }

  //This method used for removing tabindex from service status block tabs and add favorites modal tabs.
  function removeTabindex(){
    $("#service-status-widget li, #tp-results-tab-list li, #service-status-favorites li").find("a").removeAttr("tabindex")
    $("#ss-tabs-box-wrapper .tab-pane, #ss-favorites-tabs-box-wrapper .tab-pane").removeAttr("tabindex");
  }

  $(document).ready(function () {
    setCaptchaAttributes();
    // code for changing tabindex.
    $('#navbar-collapse li a').each(function() {
     $(this).attr('tabindex', '0');
    });
  });

  Drupal.behaviors.generalHacks = {
    attach: function(context, settings) {
      // Function to add aria attributes on load.
      $(window).on('load', function() {
        $('.goog-te-combo').attr("aria-label", "Languages Select");
        removeTabindex();

      });

      $(window).on('click',function(event){
      	if(!$("[id^='Acc']").length) {
          try {
            event.target.focus();
          } catch(e) {}
        }
        removeTabindex();
      });

      if (MtaApp.Breakpoints.isTablet()) {
        actionCollapse('show');
        $('.block-mta-info .tp-block').show();
        setTimeout(function(){
          $('#etix-footer').width($(window).width());
        })
      }

      $(window, context).on('changeBreakpoint', function () {
        if (MtaApp.Breakpoints.isTablet()) {
          actionCollapse('show');
          $('.block-mta-info .tp-block').show();
        }
        else {
          actionCollapse('hide');
          $('.close-preferences').click();
        }
      });

      $(window).resize(function() {
        setTimeout(function (){
          $('#etix-footer').width($(window).width());
        })
      });
    }
  }
}(jQuery, Drupal))
