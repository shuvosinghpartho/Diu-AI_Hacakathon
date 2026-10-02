const DocVerifierUI = {
  render(container, data) {
    if (!container || !data) return;

    container.innerHTML = `
      <div class="stat-summary-row">
        <div class="stat-box highlight">
          <span class="stat-label">নথিপত্রের ধরন</span>
          <div class="stat-val text-cyan">${data.doc_type}</div>
        </div>
        <div class="stat-box">
          <span class="stat-label">যাচাইকরণের ফলাফল</span>
          <div class="stat-val text-green">${data.status_label}</div>
        </div>
      </div>
      <div class="log-list">
        ${data.fields_verified.map(f => `
          <div class="log-item">
            <span><i class="fa-solid fa-circle-check text-green"></i> ${f}</span>
            <span class="text-green">অক্ষত</span>
          </div>
        `).join('')}
      </div>
    `;

    if (window.CameraStream && data.detections) {
      window.CameraStream.drawBoundingBoxes(data.detections);
    }
  }
};