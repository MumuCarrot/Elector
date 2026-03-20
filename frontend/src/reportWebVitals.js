/**
 * Registers web-vitals callbacks (CLS, FID, FCP, LCP, TTFB) when a valid handler is provided.
 * Used by Create React App to report performance metrics.
 *
 * @param {Function} [onPerfEntry] - Callback invoked for each metric; skipped if not a function.
 * @returns {void}
 */
const reportWebVitals = onPerfEntry => {
  if (onPerfEntry && onPerfEntry instanceof Function) {
    import('web-vitals').then(({ getCLS, getFID, getFCP, getLCP, getTTFB }) => {
      getCLS(onPerfEntry);
      getFID(onPerfEntry);
      getFCP(onPerfEntry);
      getLCP(onPerfEntry);
      getTTFB(onPerfEntry);
    });
  }
};

export default reportWebVitals;
