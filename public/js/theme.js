(function(){
  const settingsToggle = document.getElementById('settings-toggle');
  const settingsMenu = document.getElementById('settings-menu');
  const themeToggle = document.getElementById('theme-toggle');
  const storageKey = 'orient6_theme_dark';

  function applyTheme(dark){
    if(dark) document.body.classList.add('theme-dark');
    else document.body.classList.remove('theme-dark');
    if(themeToggle) themeToggle.checked = !!dark;
  }

  function init(){
    const pref = localStorage.getItem(storageKey);
    const dark = pref === '1';
    applyTheme(dark);

    settingsToggle && settingsToggle.addEventListener('click', function(e){
      e.stopPropagation();
      settingsMenu.style.display = settingsMenu.style.display === 'block' ? 'none' : 'block';
    });

    document.addEventListener('click', function(){ if(settingsMenu) settingsMenu.style.display = 'none'; });

    themeToggle && themeToggle.addEventListener('change', function(){
      const enabled = !!this.checked;
      applyTheme(enabled);
      try{ localStorage.setItem(storageKey, enabled ? '1' : '0'); }catch(e){}
    });
  }

  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
