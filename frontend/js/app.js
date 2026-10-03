document.addEventListener('DOMContentLoaded', () => {

  // Mobile Menu Toggle
  const mobileMenuBtn = document.getElementById('mobileMenuBtn');
  const closeMenuBtn = document.getElementById('closeMenuBtn');
  const sidebar = document.getElementById('sidebar');
  const mobileMenu = document.getElementById('mobileMenu');

  if (mobileMenuBtn && closeMenuBtn && sidebar && mobileMenu) {
    const toggleMenu = () => {
      sidebar.classList.toggle('-translate-x-full');
      if (mobileMenu.classList.contains('hidden')) {
        mobileMenu.classList.remove('hidden');
        setTimeout(() => mobileMenu.classList.remove('opacity-0'), 10);
      } else {
        mobileMenu.classList.add('opacity-0');
        setTimeout(() => mobileMenu.classList.add('hidden'), 300);
      }
    };
    mobileMenuBtn.addEventListener('click', toggleMenu);
    closeMenuBtn.addEventListener('click', toggleMenu);
    mobileMenu.addEventListener('click', toggleMenu);
  }


  

  VoiceAssistant.init();
  CameraStream.init();

  let activeModuleKey = document.body.dataset.module || 'dashboard';
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
    toast.className = `flex items-center gap-3 px-5 py-4 rounded-xl border shadow-xl transform transition-all duration-300 translate-y-0 opacity-100 ${isError ? 'bg-white border-red-200 text-red-600' : 'bg-white border-[#4F46E5]/30 text-gray-800'}`;
    const icon = document.createElement('i');
    icon.className = `fa-solid ${isError ? 'fa-circle-exclamation text-red-500' : 'fa-circle-check text-[#4F46E5]'} text-xl`;
    const text = document.createElement('span');
    text.textContent = message;
    text.className = "text-base font-bold";
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

    const statBoxClasses = "bg-white border border-gray-100 shadow-[0_2px_10px_rgba(0,0,0,0.02)] rounded-[16px] p-5 flex flex-col gap-1.5";
    const statBoxHighlightClasses = "bg-[#EEF2FF] border border-[#4F46E5]/20 rounded-[16px] p-5 flex flex-col gap-1.5";
    const statBoxDangerClasses = "bg-red-50 border border-red-100 rounded-[16px] p-5 flex flex-col gap-1.5";
    const labelClasses = "text-[11px] font-bold text-gray-500 uppercase tracking-wider";
    const valClasses = "text-xl md:text-2xl font-black text-gray-900 break-words tracking-tight";

    if (key === 'cash_count') {
      html = `
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="${statBoxHighlightClasses}">
            <span class="${labelClasses}">Total Cash</span>
            <div class="${valClasses} text-emerald-600">৳${data.total_amount.toLocaleString()}</div>
          </div>
          <div class="${statBoxClasses}">
            <span class="${labelClasses}">Total Notes</span>
            <div class="${valClasses}">${data.total_notes} টি</div>
          </div>
          <div class="${statBoxClasses}">
            <span class="${labelClasses}">Accuracy</span>
            <div class="${valClasses} text-[#4F46E5]">${confidence}</div>
          </div>
        </div>
        <div class="mt-5 bg-white border border-gray-100 shadow-[0_2px_10px_rgba(0,0,0,0.02)] rounded-xl p-4 relative flex-1 min-h-[180px]">
           <canvas id="moduleChart"></canvas>
        </div>
      `;
    } else if (key === 'fake_note') {
      html = `
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="${statBoxDangerClasses}">
            <span class="${labelClasses}">Note Status</span>
            <div class="${valClasses} text-red-600">${data.verdict_label}</div>
          </div>
          <div class="${statBoxClasses}">
            <span class="${labelClasses}">Forgery Risk</span>
            <div class="${valClasses} text-orange-600">${data.risk_score || confidence}</div>
          </div>
          <div class="${statBoxClasses}">
            <span class="${labelClasses}">Inspection Ch.</span>
            <div class="${valClasses} text-[#4F46E5]">Color-Shift & OVI</div>
          </div>
        </div>
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-5 mt-5 flex-1 min-h-[200px]">
          <div class="bg-white border border-gray-100 shadow-[0_2px_10px_rgba(0,0,0,0.02)] rounded-xl p-4 relative">
             <canvas id="moduleChart"></canvas>
          </div>
          <div class="flex flex-col gap-2 overflow-y-auto pr-1">
            ${data.features_failed.map(f => `
              <div class="flex justify-between items-center bg-white border border-red-200 rounded-xl p-3 shadow-sm">
                <span class="flex items-center gap-3 text-sm font-semibold text-gray-900">
                  <i class="fa-solid fa-circle-xmark text-red-500 text-lg"></i> 
                  <span>${f}</span>
                </span>
                <span class="text-xs font-bold px-2.5 py-1 bg-red-100 text-red-700 rounded-full">ত্রুটি</span>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    } else if (key === 'number_ocr') {
      html = `
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="${statBoxHighlightClasses}">
            <span class="${labelClasses}">Detected Num</span>
            <div class="${valClasses} text-[#4F46E5]">${data.extracted_number}</div>
          </div>
          <div class="${statBoxClasses}">
            <span class="${labelClasses}">Telecom Net</span>
            <div class="${valClasses}">${data.carrier}</div>
          </div>
          <div class="${statBoxClasses}">
            <span class="${labelClasses}">OCR Conf.</span>
            <div class="${valClasses} text-emerald-600">${confidence}</div>
          </div>
        </div>
        <div class="mt-5 bg-white border border-gray-100 shadow-[0_2px_10px_rgba(0,0,0,0.02)] rounded-xl p-4 relative flex-1 min-h-[160px]">
           <canvas id="moduleChart"></canvas>
        </div>
        <button id="btnCopyNumber" class="mt-5 w-full py-4 rounded-xl bg-white border border-gray-100 text-gray-900 hover:bg-gray-50 transition-colors flex items-center justify-center gap-2 font-bold shadow-sm shrink-0"><i class="fa-regular fa-copy"></i> Copy Number</button>
      `;
    } else if (key === 'doc_verify' || key === 'receipt_fake') {
      const isFake = key === 'receipt_fake';
      const statusBoxClasses = isFake ? statBoxDangerClasses : statBoxHighlightClasses;
      const valColor = isFake ? "text-red-600" : "text-[#4F46E5]";
      
      html = `
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="${statusBoxClasses}">
            <span class="${labelClasses}">${isFake ? 'Forensics' : 'Document Type'}</span>
            <div class="${valClasses} ${valColor}">${isFake ? data.verdict_label : data.doc_type}</div>
          </div>
          <div class="${statBoxClasses}">
            <span class="${labelClasses}">${isFake ? 'Risk Score' : 'Verification Result'}</span>
            <div class="${valClasses} text-orange-600">${isFake ? data.risk_score : data.status_label}</div>
          </div>
        </div>
        <div class="mt-5 bg-white border border-gray-100 shadow-[0_2px_10px_rgba(0,0,0,0.02)] rounded-xl p-4 relative flex-1 min-h-[180px]">
           <canvas id="moduleChart"></canvas>
        </div>
      `;
    }

    if (dynamicContainer) {
        dynamicContainer.innerHTML = html;
        dynamicContainer.classList.add('overflow-y-auto', 'pr-2', 'pb-2');
    }

    // Chart.js rendering
    if (currentChartInstance) {
      currentChartInstance.destroy();
      currentChartInstance = null;
    }

    const ctx = document.getElementById('moduleChart');
    if (ctx) {
      Chart.defaults.color = '#64748B';
      Chart.defaults.font.family = "'Outfit', 'Hind Siliguri', sans-serif";
      
      if (key === 'cash_count') {
        const labels = data.breakdown.map(b => b.note + (' Note'));
        const chartData = data.breakdown.map(b => b.count);
        const colors = data.breakdown.map(b => b.color || '#22d3ee');

        currentChartInstance = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: labels,
            datasets: [{
              label: document.body.getAttribute('data-lang') === 'en' ? 'Note Count' : 'Note Count',
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
              y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.05)' } },
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
              backgroundColor: ['#EF4444', '#E2E8F0'],
              borderWidth: 2,
              borderColor: '#ffffff',
              borderRadius: [10, 0]
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
      } else if (key === 'number_ocr') {
        const score = parseFloat(data.confidence || 0.95) * 100;
        currentChartInstance = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: ['Format Match', 'Digit Conf.', 'Carrier Val.', 'Region Check'],
            datasets: [{
              label: 'Accuracy %',
              data: [score, score - 2, 100, score - 5],
              backgroundColor: ['#4F46E5', '#10B981', '#3B82F6', '#8B5CF6'],
              borderRadius: 6
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              y: { beginAtZero: true, max: 100, grid: { color: 'rgba(0,0,0,0.05)' } },
              x: { grid: { display: false } }
            }
          }
        });
      } else if (key === 'doc_verify') {
        const score = parseFloat(data.confidence || 0.95) * 100;
        currentChartInstance = new Chart(ctx, {
          type: 'radar',
          data: {
            labels: ['Hologram', 'Micro-print', 'Face Match', 'Font Integrity', 'Layout Align'],
            datasets: [{
              label: 'Verification Score',
              data: [score, score-5, score+2, score-8, score],
              backgroundColor: 'rgba(16, 185, 129, 0.15)',
              borderColor: '#10B981',
              pointBackgroundColor: '#10B981',
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              r: {
                angleLines: { color: 'rgba(0,0,0,0.1)' },
                grid: { color: 'rgba(0,0,0,0.1)' },
                pointLabels: { color: '#64748B', font: { size: 10, family: 'Inter' } },
                ticks: { display: false }
              }
            }
          }
        });
      } else if (key === 'receipt_fake') {
        const riskScore = parseFloat(data.risk_score || 85.5);
        currentChartInstance = new Chart(ctx, {
          type: 'polarArea',
          data: {
            labels: ['Noise Variance', 'Pixel Uniformity', 'Font Render', 'Edge Sharpness', 'Luminance Delta'],
            datasets: [{
              data: [riskScore, riskScore-10, riskScore+5, riskScore-15, riskScore-5],
              backgroundColor: [
                'rgba(239, 68, 68, 0.7)',
                'rgba(249, 115, 22, 0.7)',
                'rgba(234, 179, 8, 0.7)',
                'rgba(79, 70, 229, 0.7)',
                'rgba(139, 92, 246, 0.7)'
              ],
              borderWidth: 1
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              r: { ticks: { display: false }, grid: { color: 'rgba(0,0,0,0.05)' } }
            }
          }
        });
      }
    }

    const btnCopy = document.getElementById('btnCopyNumber');
    if (btnCopy) {
      btnCopy.addEventListener('click', () => {
        navigator.clipboard.writeText(data.extracted_number);
        showToast(`Number ${data.extracted_number} copied!`);
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
        b.classList.remove('glass-active', 'text-[#4F46E5]');
        b.classList.add('text-gray-900Light');
      });
      button.classList.remove('text-gray-900Light');
      button.classList.add('glass-active', 'text-[#4F46E5]');
      activeModuleKey = button.getAttribute('data-module');
      renderModuleView(activeModuleKey);

      CameraStream.clearCanvas();
      showToast(`${MOCK_MODULE_DATABASE[activeModuleKey].title} is ready`);
    });
  });

  // Start Camera Action
  const btnStartCam = document.getElementById('btnStartCam');
  if (btnStartCam) {
    btnStartCam.addEventListener('click', async () => {
      const active = await CameraStream.start();
      if (active) {
        selectedImageFile = null;
        showToast("Camera live view activated");
        VoiceAssistant.speak("ক্যামেরা সক্রিয় হয়েছে। নোট অথবা নথিপত্র ফ্রেমে রাখুন।");
      } else {
        showToast("Could not activate camera. Please check permissions.");
      }
    });
  }

  // Execute AI Scan Action
  const btnScan = document.getElementById('btnRunScan');
  if (btnScan) {
    btnScan.addEventListener('click', async () => {
      if (activeModuleKey !== 'voice_suite' && !selectedImageFile && !CameraStream.isActive) {
        showToast('Please turn on the camera or upload an image before scanning.', true);
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
        showToast(activeModuleKey === 'voice_suite' ? 'Voice test complete' : 'API analysis completed successfully');
      } catch (error) {
        console.error('[VisionPay] Scan failed:', error);
        showToast(error.message || 'Scan could not be completed.', true);
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
        btnAssistive.className = 'flex items-center gap-2 px-4 py-2 rounded-lg bg-green-500/10 text-emerald-600 border border-green-500/20 hover:bg-green-500/20 transition-all text-sm font-medium';
        showToast("Voice assistant activated");
        VoiceAssistant.speak("Assistive audio mode activated.");
      } else {
        btnAssistive.innerHTML = `<i class="fa-solid fa-volume-xmark"></i> <span class="hidden sm:inline">Audio Off</span>`;
        btnAssistive.className = 'flex items-center gap-2 px-4 py-2 rounded-lg bg-red-500/10 text-red-600 border border-red-500/20 hover:bg-red-500/20 transition-all text-sm font-medium';
        showToast("Voice assistant deactivated", true);
      }
    });
  }

  // Local File Upload Handler
  const fileUploadInput = document.getElementById('fileUpload');
  if (fileUploadInput) {
    fileUploadInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (!file) return;
      if (!file.type.startsWith('image/')) {
        selectedImageFile = null;
        showToast('Please select a valid image file.', true);
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
        const vid = document.getElementById('videoElement');
        if (vid) vid.classList.add('hidden');
        if (placeholder) placeholder.style.display = 'none';

        CameraStream.clearCanvas();
        showToast("File loaded. Press 'Verify Information'.");
        VoiceAssistant.speak("নথির ছবি লোড হয়েছে। স্ক্যান বোতাম চাপুন।");
      };
      reader.readAsDataURL(file);
    });
  }

  // Initial View
  renderModuleView(activeModuleKey);
});