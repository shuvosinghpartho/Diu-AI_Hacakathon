const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

let spoken;
let voices = [{ name: 'English', lang: 'en-US' }];
const speechSynthesis = {
  getVoices: () => voices,
  addEventListener: () => {},
  cancel: () => {},
  resume: () => {},
  speak: utterance => { spoken = utterance; }
};
class Utterance {
  constructor(text) { this.text = text; }
}
const transcript = {};
const avatar = { classList: { add: () => {}, remove: () => {} } };
const context = vm.createContext({
  window: { speechSynthesis }, speechSynthesis,
  SpeechSynthesisUtterance: Utterance,
  document: {
    getElementById: id => id === 'speechTranscriptText' ? transcript : null,
    querySelector: () => avatar
  },
  console
});
vm.runInContext(fs.readFileSync('frontend/js/modules/voice_assistant.js', 'utf8') +
  '\nglobalThis.assistant = VoiceAssistant;', context);

assert.equal(context.assistant.init(), true);
context.assistant.speak('বাংলা সারাংশ', 'Receipt scan complete. Amount 2040 taka.');
assert.equal(spoken.text, 'Receipt scan complete. Amount 2040 taka.');
assert.equal(spoken.lang, 'en-US');

voices = [{ name: 'Bangla', lang: 'bn-BD' }];
context.assistant.voices = voices;
context.assistant.speak('বাংলা সারাংশ', 'English fallback');
assert.equal(spoken.text, 'বাংলা সারাংশ');
assert.equal(spoken.lang, 'bn-BD');
assert.equal(transcript.innerText, '"বাংলা সারাংশ"');
console.log('Voice assistant tests passed');
