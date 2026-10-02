const ReceiptCheckerUI = {
  render(container, data) {
    if (!container || !data) return;

    container.innerHTML = `
      <div class="stat-summary-row">
        <div class="stat-box danger">
          <span class="stat-label">ফরেনসিক ফলাফল</span>
          <div class="stat-val text-red">${data.verdict_label}</div>
        </div>
        <div class="stat-box">
          <span class="stat-label">কারচুপি স্কোর</span>
          <div class="stat-val text-amber">${data.risk_score}</div>
        </div>
      </div>
      <div class="log-list">
        ${data.tamper_flags.map(tf => `
          <div class="log-item fake">
            <span><i class="fa-solid fa-bug text-red"></i> ${tf}</span>
            <span class="text-red">বিচ্যুতি</span>
          </div>
        `).join('')}
      </div>
    `;

    if (window.CameraStream && data.detections) {
      window.CameraStream.drawBoundingBoxes(data.detections);
    }
  }
};