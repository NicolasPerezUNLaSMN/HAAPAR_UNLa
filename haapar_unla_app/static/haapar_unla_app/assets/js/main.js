document.addEventListener('DOMContentLoaded', function () {
    const sidebar = document.querySelector('.sidebar');
    const toggleBtn = document.querySelector('.toggle-btn');
    const toggleThemeBtn = document.getElementById('toggle-theme');
    const body = document.body;

    // Sidebar hover behavior
    sidebar.addEventListener('mouseenter', function () {
        sidebar.classList.remove('collapsed');
    });

    sidebar.addEventListener('mouseleave', function () {
        sidebar.classList.add('collapsed');
    });

    toggleBtn.addEventListener('click', function () {
        sidebar.classList.toggle('collapsed');
    });

     // Modo oscuro: cargar preferencia
  if (localStorage.getItem('theme') === 'dark') {
    body.classList.add('dark-mode');
    if (toggleThemeBtn) {
      toggleThemeBtn.innerHTML = '<i class="fa-solid fa-sun"></i> Modo Claro';
    }
  }

  // Modo oscuro: alternar
  if (toggleThemeBtn) {
    toggleThemeBtn.addEventListener('click', function () {
      body.classList.toggle('dark-mode');

      if (body.classList.contains('dark-mode')) {
        localStorage.setItem('theme', 'dark');
        toggleThemeBtn.innerHTML = '<i class="fa-solid fa-sun"></i> Modo Claro';
      } else {
        localStorage.setItem('theme', 'light');
        toggleThemeBtn.innerHTML = '<i class="fa-solid fa-moon"></i> Modo Oscuro';
      }
    });
  }

});

