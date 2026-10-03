const VoiceAssistant = {
  enabled: true,
  currentUtterance: null,
  voices: [],

  init() {
    if (!('speechSynthesis' in window)) {
      console.warn("[VoiceAssistant] Web Speech API not supported on this browser.");
      this.enabled = false;
      return false;
    }
    const loadVoices = () => {
      this.voices = window.speechSynthesis.getVoices?.() || [];
    };
    loadVoices();
    window.speechSynthesis.addEventListener?.('voiceschanged', loadVoices);
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

  speak(text, fallbackText = '') {
    if (!this.enabled || !text) return;

    this.stop();

    const cleanText = text.replace(/<[^>]*>/g, '').trim();
    const cleanFallback = fallbackText.replace(/<[^>]*>/g, '').trim();
    const voices = this.voices.length ? this.voices : (window.speechSynthesis.getVoices?.() || []);
    const banglaVoice = voices.find(voice => /^bn(?:-|$)/i.test(voice.lang));
    const spokenText = banglaVoice ? cleanText : (cleanFallback || cleanText);
    const utterance = new SpeechSynthesisUtterance(spokenText);

    if (banglaVoice) {
      utterance.voice = banglaVoice;
      utterance.lang = banglaVoice.lang;
    } else {
      const englishVoice = voices.find(voice => /^en(?:-|$)/i.test(voice.lang));
      if (englishVoice) utterance.voice = englishVoice;
      utterance.lang = englishVoice?.lang || 'en-US';
    }
    utterance.rate = 0.95;
    utterance.pitch = 1.0;

    const transcriptEl = document.getElementById('speechTranscriptText');
    if (transcriptEl) {
      transcriptEl.innerText = `"${spokenText}"`;
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
    window.speechSynthesis.resume?.();
    window.speechSynthesis.speak(utterance);
  }
};
