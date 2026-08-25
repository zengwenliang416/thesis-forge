'use strict';

const shell = document.querySelector('.app-shell');
const stateButtons = Array.from(document.querySelectorAll('[data-set-state]'));
const panelButtons = Array.from(document.querySelectorAll('[data-panel]'));
const previewButtons = Array.from(document.querySelectorAll('[data-preview]'));

shell.setAttribute('data-mobile-panel', 'outline');

for (const button of stateButtons) {
  button.addEventListener('click', () => {
    shell.setAttribute('data-specnav-state', button.dataset.setState);
    for (const item of stateButtons) {
      item.setAttribute('aria-pressed', String(item === button));
    }
  });
}

for (const button of panelButtons) {
  button.addEventListener('click', () => {
    shell.setAttribute('data-mobile-panel', button.dataset.panel);
    for (const item of panelButtons) {
      item.setAttribute('aria-pressed', String(item === button));
    }
  });
}

for (const button of previewButtons) {
  button.addEventListener('click', () => {
    for (const item of previewButtons) {
      item.setAttribute('aria-pressed', String(item === button));
    }
  });
}
