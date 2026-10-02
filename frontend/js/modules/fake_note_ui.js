const FakeNoteUI = {
  render(container, data) {
    if (!container || !data) return;

    container.innerHTML = `
      <div class="stat-summary-row">
        <div class="stat-box danger">
          <span class="stat-label">নোটের স্ট্যাটাস</span>
          <div class="stat-val text-red">${data.verdict_label}</div>
        </div>
        <div class="stat-box">
          <span class="stat-label">কারচুপির সম্ভাবনা</span>
          <div class="stat-val text-amber">${data.confidence}</div>
        </div>
        <div class="stat-box">
          <span class="stat-label">ইনসপেকশন চ্যানেল</span>
          <div class="stat-val text-cyan">Color-Shift & OVI</div>
        </div>
      </div>
      <div class="log-list">
        ${data.features_failed.map(f => `
          <div class="log-item fake">
            <span><i class="fa-solid fa-triangle-exclamation text-red"></i> ${f}</span>
            <span class="text-red">ত্রুটি শনাক্ত</span>
          </div>
        `).join('')}
      </div>
    `;

    if (window.CameraStream && data.detections) {
      window.CameraStream.drawBoundingBoxes(data.detections);
    }
  }
};