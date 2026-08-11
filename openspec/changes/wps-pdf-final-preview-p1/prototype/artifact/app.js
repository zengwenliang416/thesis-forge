'use strict';

const shell = document.querySelector('.app-shell');
const stateButtons = Array.from(document.querySelectorAll('[data-set-state]'));
const modeButtons = Array.from(document.querySelectorAll('[data-preview-mode]'));

function setPressed(buttons, active, attribute) {
  for (const button of buttons) {
    button.setAttribute(
      'aria-pressed',
      String(button.getAttribute(attribute) === active),
    );
  }
}

for (const button of stateButtons) {
  button.addEventListener('click', () => {
    const state = button.getAttribute('data-set-state');
    shell.setAttribute('data-specnav-state', state);
    shell.setAttribute('data-preview-mode', 'final');
    setPressed(stateButtons, state, 'data-set-state');
    setPressed(modeButtons, 'final', 'data-preview-mode');
  });
}

for (const button of modeButtons) {
  button.addEventListener('click', () => {
    const mode = button.getAttribute('data-preview-mode');
    shell.setAttribute('data-preview-mode', mode);
    setPressed(modeButtons, mode, 'data-preview-mode');
  });
}
