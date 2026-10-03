const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
class Element {
  constructor(tag) { this.tag = tag; this.children = []; this.listeners = {}; this.value = ''; }
  append(...children) { children.forEach(child => this.appendChild(child)); }
  appendChild(child) { this.children.push(child); if (this.tag === 'select' && !this.value) this.value = child.value; }
  replaceChildren() { this.children = []; }
  setAttribute() {}
  addEventListener(event, fn) { this.listeners[event] = fn; }
  select() { this.selected = true; }
}
const navigator = { clipboard: { writeText: async value => { navigator.copied = value; } } };
const document = { createElement: tag => new Element(tag), execCommand: command => command === 'copy' };
const context = vm.createContext({ document, navigator });
vm.runInContext(fs.readFileSync('frontend/js/modules/number_scanner_ui.js', 'utf8') + '\nglobalThis.ui = NumberScannerUI;', context);
(async () => {
  const container = new Element('div');
  const notices = [];
  const notify = (...args) => notices.push(args);
  context.ui.render(container, { scanned: false }, notify);
  assert.equal(container.children.length, 1);
  context.ui.render(container, { scanned: true, numbers: [] }, notify);
  assert.equal(container.children.length, 1);
  const numbers = [
    { number: '01712345678', carrier: 'GP', confidence: 0.9 },
    { number: '01812345678', carrier: 'Robi', confidence: 0.8 }
  ];
  context.ui.render(container, { scanned: true, numbers }, notify);
  const select = container.children.find(item => item.tag === 'select');
  const copy = container.children.find(item => item.tag === 'button');
  const manual = container.children.find(item => item.tag === 'input');
  select.value = numbers[1].number;
  select.listeners.change();
  assert.equal(manual.value, numbers[1].number);
  await copy.listeners.click();
  assert.equal(navigator.copied, numbers[1].number);
  assert.equal(notices.at(-1).length, 1);
  navigator.clipboard = null;
  await copy.listeners.click();
  assert.equal(notices.at(-1).length, 1);
  navigator.clipboard = { writeText: async () => { throw new Error('denied'); } };
  await copy.listeners.click();
  assert.equal(notices.at(-1)[1], true);
  assert.equal(copy.disabled, false);
  context.ui.render(container, { error: '<img onerror=alert(1)>' }, notify);
  assert.equal(container.children[0].textContent, '<img onerror=alert(1)>');
  console.log('Number scanner UI tests passed');
})().catch(error => { console.error(error); process.exitCode = 1; });
