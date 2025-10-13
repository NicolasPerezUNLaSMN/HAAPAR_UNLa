// Auto-close alerts (lee data-autoclose en ms; pausa al hover)
(function () {
  const container = document.getElementById('global-messages');
  if (!container) return;
  const ms = parseInt(container.getAttribute('data-autoclose') || '0', 10);
  if (!ms) return; // 0 => no auto close

  container.querySelectorAll('.alert').forEach(alertEl => {
    let timeoutId = null;

    const closeAlert = () => {
      try {
        const inst = bootstrap.Alert.getOrCreateInstance(alertEl);
        inst.close();
      } catch (e) {
        alertEl.remove();
      }
    };

    const start = () => {
      timeoutId = setTimeout(closeAlert, ms);
    };
    const stop = () => {
      if (timeoutId) { clearTimeout(timeoutId); timeoutId = null; }
    };

    // start timer, pause on hover
    start();
    alertEl.addEventListener('mouseenter', stop);
    alertEl.addEventListener('mouseleave', () => { if (!timeoutId) start(); });
  });
})();
