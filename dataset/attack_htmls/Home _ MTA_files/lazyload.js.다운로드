var ILApp = ILApp || {};
ILApp.Modules = ILApp.Modules || {};
ILApp.Modules.Lazyload = (function ($) {
  // Module settings
  var settings = {
  };

  /**
   * Initialize function. Executed once, when the module is loaded
   */
  function init() {
    $(window).on('load', function () {
      $('html').addClass('page-loaded');

      loadImages();
    });
  }

  /**
   * Apply lazy loading to images
   */
  function loadImages() {
    $('img.lazy').each(function () {
      $(this)
        .attr('src', $(this).data('original'))
    });
  }


  // Call initialize function
  init();

  // Return the exposed functions
  return {};
})(jQuery);
