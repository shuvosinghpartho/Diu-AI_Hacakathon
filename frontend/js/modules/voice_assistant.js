const VoiceAssistant = {
  enabled: true,
  currentUtterance: null,

  init() {
    if (!('speechSynthesis' in window)) {
      console.warn("[VoiceAssistant] Web Speech API not supported on this browser.");
      this.enabled = false;
      return false;
    }
    
    // Trigger voice loading in advance
    window.speechSynthesis.getVoices();
    window.speechSynthesis.onvoiceschanged = () => {
        window.speechSynthesis.getVoices();
    };
    
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
    utterance.rate = 0.85; // Slightly slower for much clearer Bengali articulation
    utterance.pitch = 1.05; // Slight pitch up for clarity
    
    // Select the best available Bengali voice (Google's is usually the clearest)
    const voices = window.speechSynthesis.getVoices();
    if (voices && voices.length > 0) {
      let bnVoice = voices.find(v => (v.lang === 'bn-BD' || v.lang === 'bn-IN') && (v.name.includes('Google') || v.name.includes('Online')));
      if (!bnVoice) {
        bnVoice = voices.find(v => v.lang.includes('bn'));
      }
      if (bnVoice) {
        utterance.voice = bnVoice;
      }
    }

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