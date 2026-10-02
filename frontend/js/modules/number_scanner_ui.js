const NumberScannerUI = {
  render(container, data) {
    if (!container || !data) return;

    container.innerHTML = `
      <div class="stat-summary-row">
        <div class="stat-box highlight">
          <span class="stat-label">শনাক্তকৃত নম্বর</span>
          <div class="stat-val text-cyan">${data.extracted_number}</div>
        </div>
        <div class="stat-box">
          <span class="stat-label">টেলিকম নেটওয়ার্ক</span>
          <div class="stat-val">${data.carrier}</div>
        </div>
        <div class="stat-box">
          <span class="stat-label">OCR কনফিডেন্স</span>
          <div class="stat-val text-green">${data.confidence}</div>
        </div>
      </div>
      <button class="ctrl-btn btn-accent" id="btnCopyNumber" style="width: 100%; margin-top: 10px;">
        <i class="fa-regular fa-copy"></i> নম্বরটি ক্যাশ-ইন / সেন্ড মানি ফিল্ডে কপি করুন
      </button>
    `;

    const copyBtn = container.querySelector('#btnCopyNumber');
    if (copyBtn) {
      copyBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(data.extracted_number);
        alert(`নম্বর ${data.extracted_number} কপি করা হয়েছে!`);
      });
    }

    if (window.CameraStream && data.detections) {
      window.CameraStream.drawBoundingBoxes(data.detections);
    }
  }
};