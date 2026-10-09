(function initSentry() {
  var options = window.ikeaExternalScriptOptions || {};
  var sentryOptions = options.sentry || {};
  var dsn = sentryOptions.dsn;
  var env = sentryOptions.env;
  var sampleRate = sentryOptions.sampleRate;
  var tracesSampleRate = sentryOptions.tracesSampleRate;
  var replaysSessionSampleRate = sentryOptions.replaysSessionSampleRate;
  var replaysOnErrorSampleRate = sentryOptions.replaysOnErrorSampleRate;

  if (!env || !window.Sentry) {
    return;
  }

  var integrations = [];

  if (tracesSampleRate) {
    integrations.push(window.Sentry.browserTracingIntegration());
  }
  if (replaysSessionSampleRate || replaysOnErrorSampleRate) {
    integrations.push(window.Sentry.replayIntegration());
  }

  var sentryConfig = {
    dsn,
    environment: env,
    sampleRate,
    tracesSampleRate,
    replaysSessionSampleRate,
    replaysOnErrorSampleRate,
    integrations,
    beforeSend: (event, hint) => {
      var err = hint && hint.originalException;

      if (err && err.message) {
        var ignorePatterns = [
          /null is not an object \(evaluating 'this.selector.appendChild'\)/,
          /Preflight response is not successful/,
          /NotAllowedError: The request is not allowed by the user agent/,
          /Network request failed/,
          /NetworkError when attempting to fetch resource/,
          /cancelled/,
          /Abgebrochen/,
          /geannuleerd/,
          /avbruten/,
          /annullato/,
          /cancelado/,
          /annulé/,
          /annulleret/,
          /anulowane/,
          /avbrutt/,
        ];

        for (var i = 0; i < ignorePatterns.length; i++) {
          if (err.message.match(ignorePatterns[i])) {
            return null;
          }
        }
      }

      return event;
    },
  };

  window.Sentry.init(sentryConfig);
})();
