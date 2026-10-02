document.addEventListener('DOMContentLoaded', () => {
  VoiceAssistant.init();
  CameraStream.init();

  let activeModuleKey = 'cash_count';
  let assistiveModeEnabled = true;
  let selectedImageFile = null;
  let currentChartInstance = null;

  const titleEl = document.getElementById('moduleTitle');
  const descEl = document.getElementById('moduleDescription');
  const latencyEl = document.getElementById('moduleLatency');
  const dynamicContainer = document.getElementById('dynamicResultContent');
  const cameraWrapper = document.getElementById('cameraWrapper');

  const showToast = (message, isError = false) => {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `flex items-center gap-3 px-4 py-3 rounded-xl border shadow-lg transform transition-all duration-300 translate-y-0 opacity-100 ${isError ? 'bg-red-500/10 border-red-500/20 text-red-200 shadow-red-500/10' : 'bg-brand-500/10 border-brand-500/20 text-brand-100 shadow-brand-500/10'}`;
    const icon = document.createElement('i');
    icon.className = `fa-solid ${isError ? 'fa-circle-exclamation text-red-400' : 'fa-circle-check text-brand-400'} text-lg`;
    const text = document.createElement('span');
    text.textContent = message;
    text.className = "text-sm font-medium";
    toast.append(icon, text);
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('translate-y-0', 'opacity-100');
    }, 10);

    setTimeout(() => {
      toast.classList.remove('translate-y-0', 'opacity-100');
      toast.classList.add('translate-y-4', 'opacity-0');
      setTimeout(() => toast.remove(), 300);
    }, 3200);
  };

  const renderModuleView = (key, result = MOCK_MODULE_DATABASE[key]) => {
    const data = result;
    if (!data) return;
    const confidence = typeof data.confidence === 'number'
      ? `${(data.confidence * 100).toFixed(1)}%`
      : (data.confidence || data.badge?.match(/[\d.]+%/)?.[0] || 'N/A');

    if (titleEl) titleEl.innerText = data.title;
    if (descEl) descEl.innerText = data.desc;
    if (latencyEl) latencyEl.innerText = data.badge || 'READY';

    let html = '';

    const statBoxClasses = "bg-dark-800/50 border border-white/5 rounded-xl p-4 flex flex-col gap-1";
    const statBoxHighlightClasses = "bg-brand-500/10 border border-brand-500/20 rounded-xl p-4 flex flex-col gap-1 shadow-inner shadow-brand-500/10";
    const statBoxDangerClasses = "bg-red-500/10 border border-red-500/20 rounded-xl p-4 flex flex-col gap-1 shadow-inner shadow-red-500/10";
    const labelClasses = "text-xs font-semibold text-gray-400 uppercase tracking-wider";
    const valClasses = "text-xl font-bold text-gray-100";

    if (key === 'cash_count') {
      html = `
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="${statBoxHighlightClasses}">
            <span class="${labelClasses}">মোট গণনাকৃত টাকা</span>
            <div class="${valClasses} text-green-400">৳${data.total_amount.toLocaleString()}</div>
          </div>
          <div class="${statBoxClasses}">
            <span class="${labelClasses}">মোট নোট সংখ্যা</span>
            <div class="${valClasses}">${data.total_notes} টি</div>
          </div>
          <div class="${statBoxClasses}">
            <span class="${labelClasses}">শনাক্তকরণ নির্ভুলতা</span>
            <div class="${valClasses} text-brand-400">${confidence}</div>
          </div>
        </div>
        <div class="mt-4 bg-dark-800/50 border border-white/5 rounded-xl p-4 relative" style="height: 250px;">
           <canvas id="moduleChart"></canvas>
        </div>
      `;
    } else if (key === 'fake_note') {
      html = `
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="${statBoxDangerClasses}">
            <span class="${labelClasses}">নোটের স্ট্যাটাস</span>
            <div class="${valClasses} text-red-400">${data.verdict_label}</div>
          </div>
          <div class="${statBoxClasses}">
            <span class="${labelClasses}">কারচুপির সম্ভাবনা</span>
            <div class="${valClasses} text-orange-400">${data.risk_score || confidence}</div>
          </div>
          <div class="${statBoxClasses}">
            <span class="${labelClasses}">ইনসপেকশন চ্যানেল</span>
            <div class="${valClasses} text-brand-400">Color-Shift & OVI</div>
          </div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
          <div class="bg-dark-800/50 border border-white/5 rounded-xl p-4 relative" style="height: 220px;">
             <canvas id="moduleChart"></canvas>
          </div>
          <div class="flex flex-col gap-2 overflow-y-auto" style="height: 220px;">
            ${data.features_failed.map(f => `
              <div class="flex justify-between items-center bg-red-500/5 border border-red-500/10 rounded-lg p-2.5">
                <span class="flex items-center gap-3 text-xs text-gray-300">
                  <i class="fa-solid fa-triangle-exclamation text-red-400"></i> 
                  <span>${f}</span>
                </span>
                <span class="text-[10px] font-semibold px-2 py-1 bg-red-500/20 text-red-400 rounded-md">ত্রুটি</span>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    } else if (key === 'number_ocr') {
      html = `
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="${statBoxHighlightClasses}">
            <span class="${labelClasses}">শনাক্তকৃত নম্বর</span>
            <div class="${valClasses} text-brand-400">${data.extracted_number}</div>
          </div>
          <div class="${statBoxClasses}">
            <span class="${labelClasses}">টেলিকম নেটওয়ার্ক</span>
            <div class="${valClasses}">${data.carrier}</div>
          </div>
          <div class="${statBoxClasses}">
            <span class="${labelClasses}">OCR কনফিডেন্স</span>
            <div class="${valClasses} text-green-400">${confidence}</div>
          </div>
        </div>
        <div class="mt-4 bg-dark-800/50 border border-white/5 rounded-xl p-4 relative" style="height: 200px;">
           <canvas id="moduleChart"></canvas>
        </div>
        <button id="btnCopyNumber" class="mt-4 w-full py-3 rounded-xl bg-dark-800 border border-white/10 text-gray-300 hover:text-white hover:bg-white/10 transition-colors flex items-center justify-center gap-2 font-medium">
          <i class="fa-regular fa-copy"></i> নম্বরটি ক্যাশ-ইন / সেন্ড মানি ফিল্ডে কপি করুন
        </button>
      `;
    } else if (key === 'doc_verify' || key === 'receipt_fake') {
      const isFake = key === 'receipt_fake';
      const statusBoxClasses = isFake ? statBoxDangerClasses : statBoxHighlightClasses;
      const valColor = isFake ? "text-red-400" : "text-brand-400";
      
      html = `
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="${statusBoxClasses}">
            <span class="${labelClasses}">${isFake ? 'ফরেনসিক ফলাফল' : 'নথিপত্রের ধরন'}</span>
            <div class="${valClasses} ${valColor}">${isFake ? data.verdict_label : data.doc_type}</div>
          </div>
          <div class="${statBoxClasses}">
            <span class="${labelClasses}">${isFake ? 'কারচুপি স্কোর' : 'যাচাইকরণের ফলাফল'}</span>
            <div class="${valClasses} text-orange-400">${isFake ? data.risk_score : data.status_label}</div>
          </div>
        </div>
        <div class="mt-4 bg-dark-800/50 border border-white/5 rounded-xl p-4 relative" style="height: 250px;">
           <canvas id="moduleChart"></canvas>
        </div>
      `;
    }

    if (dynamicContainer) dynamicContainer.innerHTML = html;

    // Chart.js rendering
    if (currentChartInstance) {
      currentChartInstance.destroy();
      currentChartInstance = null;
    }

    const ctx = document.getElementById('moduleChart');
    if (ctx) {
      Chart.defaults.color = '#94a3b8';
      Chart.defaults.font.family = "'Outfit', 'Hind Siliguri', sans-serif";
      
      if (key === 'cash_count') {
        const labels = data.breakdown.map(b => b.note + " নোট");
        const chartData = data.breakdown.map(b => b.count);
        const colors = data.breakdown.map(b => b.color || '#22d3ee');

        currentChartInstance = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: labels,
            datasets: [{
              label: 'নোট সংখ্যা',
              data: chartData,
              backgroundColor: colors,
              borderRadius: 6
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false }
            },
            scales: {
              y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' } },
              x: { grid: { display: false } }
            }
          }
        });
      } else if (key === 'fake_note') {
        const risk = parseFloat(data.risk_score || confidence) || 94.2;
        currentChartInstance = new Chart(ctx, {
          type: 'doughnut',
          data: {
            labels: ['Risk Score', 'Authenticity'],
            datasets: [{
              data: [risk, 100 - risk],
              backgroundColor: ['#ef4444', '#1e293b'],
              borderWidth: 0
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '75%',
            plugins: {
              legend: { display: false }
            }
          }
        });
      } else {
         const score = parseFloat(data.confidence || 0.95) * 100;
         currentChartInstance = new Chart(ctx, {
          type: 'radar',
          data: {
            labels: ['Edge Quality', 'Texture', 'Watermark', 'Text Alignment', 'Consistency'],
            datasets: [{
              label: 'Metrics',
              data: [score, score-5, score+2, score-8, score],
              backgroundColor: 'rgba(34, 211, 238, 0.2)',
              borderColor: '#22d3ee',
              pointBackgroundColor: '#06b6d4',
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              r: {
                angleLines: { color: 'rgba(255,255,255,0.1)' },
                grid: { color: 'rgba(255,255,255,0.1)' },
                pointLabels: { color: '#94a3b8' },
                ticks: { display: false }
              }
            }
          }
        });
      }
    }

    const btnCopy = document.getElementById('btnCopyNumber');
    if (btnCopy) {
      btnCopy.addEventListener('click', () => {
        navigator.clipboard.writeText(data.extracted_number);
        showToast(`নম্বর ${data.extracted_number} কপি হয়েছে!`);
      });
    }

    // Update Speech Transcript Text globally
    const transcriptEl = document.getElementById('speechTranscriptText');
    if(transcriptEl) transcriptEl.innerText = `"${data.bangla_speech}"`;
  };

  // Tab Selection
  document.querySelectorAll('.tab-item').forEach(button => {
    button.addEventListener('click', () => {
      document.querySelectorAll('.tab-item').forEach(b => {
        b.classList.remove('glass-active', 'text-brand-400');
        b.classList.add('text-gray-400');
      });
      button.classList.remove('text-gray-400');
      button.classList.add('glass-active', 'text-brand-400');
      activeModuleKey = button.getAttribute('data-module');
      renderModuleView(activeModuleKey);

      CameraStream.clearCanvas();
      showToast(`${MOCK_MODULE_DATABASE[activeModuleKey].title} প্রস্তুত`);
    });
  });

  // Start Camera Action
  const btnStartCam = document.getElementById('btnStartCamera');
  if (btnStartCam) {
    btnStartCam.addEventListener('click', async () => {
      const active = await CameraStream.start();
      if (active) {
        selectedImageFile = null;
        showToast("ক্যামেরা লাইভ ভিউ সক্রিয় হয়েছে");
        VoiceAssistant.speak("ক্যামেরা সক্রিয় হয়েছে। নোট অথবা নথিপত্র ফ্রেমে রাখুন।");
      } else {
        showToast("ক্যামেরা সক্রিয় করা যায়নি। অনুগ্রহ করে পারমিশন চেক করুন।");
      }
    });
  }

  // Execute AI Scan Action
  const btnScan = document.getElementById('btnRunScan');
  if (btnScan) {
    btnScan.addEventListener('click', async () => {
      if (activeModuleKey !== 'voice_suite' && !selectedImageFile && !CameraStream.isActive) {
        showToast('স্ক্যানের আগে ক্যামেরা চালু করুন অথবা একটি ছবি আপলোড করুন।', true);
        return;
      }

      if (cameraWrapper) cameraWrapper.classList.add('scanning');
      btnScan.disabled = true;

      const loader = document.getElementById('globalLoader');
      if (loader) {
        loader.style.display = 'flex';
        // Need a small timeout to allow display:flex to apply before transition
        setTimeout(() => {
          loader.classList.remove('pointer-events-none', 'opacity-0');
        }, 10);
      }

      try {
        const mockData = MOCK_MODULE_DATABASE[activeModuleKey];
        let result = mockData;

        if (activeModuleKey !== 'voice_suite') {
          const image = selectedImageFile || await CameraStream.captureFrame();
          const response = await VisionPayApi.analyze(activeModuleKey, image, image.name || 'camera-capture.jpg');
          result = {
            ...mockData,
            ...response,
            confidence: typeof response.confidence === 'number'
              ? `${(response.confidence * 100).toFixed(1)}%`
              : response.confidence
          };
        }

        renderModuleView(activeModuleKey, result);
        if (result.detections && result.detections.length > 0) {
          CameraStream.drawBoundingBoxes(result.detections);
        } else {
          CameraStream.clearCanvas();
        }

        VoiceAssistant.speak(result.bangla_speech);
        showToast(activeModuleKey === 'voice_suite' ? 'ভয়েস পরীক্ষা সম্পন্ন হয়েছে' : 'API বিশ্লেষণ সফলভাবে সম্পন্ন হয়েছে');
      } catch (error) {
        console.error('[VisionPay] Scan failed:', error);
        showToast(error.message || 'স্ক্যান সম্পন্ন করা যায়নি।', true);
      } finally {
        if (cameraWrapper) cameraWrapper.classList.remove('scanning');
        btnScan.disabled = false;

        if (loader) {
          loader.classList.add('opacity-0', 'pointer-events-none');
          setTimeout(() => {
              loader.style.display = 'none';
          }, 300);
        }
      }
    });
  }

  // Replay Bangla Voice
  const btnReplay = document.getElementById('btnSpeakerReplay');
  if (btnReplay) {
    btnReplay.addEventListener('click', () => {
      const currentData = MOCK_MODULE_DATABASE[activeModuleKey];
      VoiceAssistant.speak(currentData.bangla_speech);
    });
  }

  // Toggle Assistive Mode
  const btnAssistive = document.getElementById('btnToggleAssistive');
  if (btnAssistive) {
    btnAssistive.addEventListener('click', () => {
      assistiveModeEnabled = VoiceAssistant.toggle();
      if (assistiveModeEnabled) {
        btnAssistive.innerHTML = `<i class="fa-solid fa-universal-access"></i> <span class="hidden sm:inline">Assistive Audio</span>`;
        btnAssistive.className = 'flex items-center gap-2 px-4 py-2 rounded-lg bg-green-500/10 text-green-400 border border-green-500/20 hover:bg-green-500/20 transition-all text-sm font-medium';
        showToast("দৃষ্টি প্রতিবন্ধী ভয়েস অ্যাসিস্ট্যান্ট চালু করা হয়েছে");
        VoiceAssistant.speak("অ্যাসিস্টিভ অডিও মোড চালু করা হয়েছে।");
      } else {
        btnAssistive.innerHTML = `<i class="fa-solid fa-volume-xmark"></i> <span class="hidden sm:inline">Audio Off</span>`;
        btnAssistive.className = 'flex items-center gap-2 px-4 py-2 rounded-lg bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20 transition-all text-sm font-medium';
        showToast("ভয়েস অ্যাসিস্ট্যান্ট বন্ধ করা হয়েছে", true);
      }
    });
  }

  // Local File Upload Handler
  const fileUploadInput = document.getElementById('fileInputUpload');
  if (fileUploadInput) {
    fileUploadInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (!file) return;
      if (!file.type.startsWith('image/')) {
        selectedImageFile = null;
        showToast('অনুগ্রহ করে একটি বৈধ ছবির ফাইল নির্বাচন করুন।', true);
        fileUploadInput.value = '';
        return;
      }

      selectedImageFile = file;

      const reader = new FileReader();
      reader.onload = (event) => {
        let preview = document.getElementById('uploadedImgPreview');
        if (!preview) {
          preview = document.createElement('img');
          preview.id = 'uploadedImgPreview';
          preview.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
            z-index: 2;
          `;
          if (cameraWrapper) cameraWrapper.appendChild(preview);
        }
        preview.src = event.target.result;

        const placeholder = document.getElementById('cameraPlaceholder');
        if (placeholder) placeholder.style.display = 'none';

        CameraStream.clearCanvas();
        showToast("ফাইল লোড হয়েছে। 'Execute AI Scan' চাপুন।");
        VoiceAssistant.speak("নথির ছবি লোড হয়েছে। স্ক্যান বোতাম চাপুন।");
      };
      reader.readAsDataURL(file);
    });
  }

  // Initial View
  renderModuleView('cash_count');
});