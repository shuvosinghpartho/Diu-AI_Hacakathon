const VoiceAssistant = {
  enabled: true,
  currentUtterance: null,

  init() {
    if (!('speechSynthesis' in window)) {
      console.warn("[VoiceAssistant] Web Speech API not supported on this browser.");
      this.enabled = false;
      return false;
    }
    return true;
  },

  toggle(status) {
    if (status !== undefined) {
      this.enabled = status;
    } else {
      this.enabled = !this.enabled;
    }
    if (!this.enabled) {
      this.stop();
    }
    return this.enabled;
  },

  stop() {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
  },

  speak(text) {
    if (!this.enabled || !text) return;

    this.stop();

    const cleanText = text.replace(/<[^>]*>/g, '').trim();
    const utterance = new SpeechSynthesisUtterance(cleanText);

    utterance.lang = 'bn-BD';
    utterance.rate = 0.95;
    utterance.pitch = 1.0;

    const transcriptEl = document.getElementById('speechTranscriptText');
    if (transcriptEl) {
      transcriptEl.innerText = `"${cleanText}"`;
    }

    const avatarRing = document.querySelector('.speech-avatar');
    if (avatarRing) {
      avatarRing.classList.add('pulse-audio');
    }

    utterance.onend = () => {
      if (avatarRing) avatarRing.classList.remove('pulse-audio');
    };

    utterance.onerror = (e) => {
      console.error("[VoiceAssistant] Speech synthesis error:", e);
      if (avatarRing) avatarRing.classList.remove('pulse-audio');
    };

    this.currentUtterance = utterance;
    window.speechSynthesis.speak(utterance);
  }
};