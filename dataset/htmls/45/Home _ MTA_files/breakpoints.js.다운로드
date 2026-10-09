var MtaApp = MtaApp || {};
MtaApp.Breakpoints = (function ($, Drupal) {
  'use strict';

  var tablet = 768;
  var desktop = 960;
  var mQ = {
    mobile: window.matchMedia('(max-width: ' + (tablet - 1) + 'px)'),
    onlyTablet: window.matchMedia('(min-width: ' + tablet + 'px) and (max-width: ' + (desktop - 1) + 'px)'),
    tablet: window.matchMedia('(min-width: ' + (tablet) + 'px)'),
    desktop: window.matchMedia('(min-width: ' + (desktop) + 'px)')
  };

  function isMobile() {
    return mQ.mobile.matches;
  }

  function isOnlyTablet() {
    return mQ.onlyTablet.matches;
  }

  function isTablet() {
    return mQ.tablet.matches;
  }

  function isDesktop() {
    return mQ.desktop.matches;
  }

  Drupal.behaviors.currentBreakpoint = {
    attach: function (context) {
      var breakpointStr = ['mobile', 'onlyTablet', 'desktop'];

      breakpointStr.forEach(function (bp) {
        mQ[bp].addListener(function (e) {
          if (e.matches) {
            $(document).trigger('changeBreakpoint');
          }
        });
      });
    }
  };

  return {
    isMobile: isMobile,
    isOnlyTablet: isOnlyTablet,
    isTablet: isTablet,
    isDesktop: isDesktop
  };

}(jQuery, Drupal));
