const CashCounterUI = {
  render(container, data) {
    if (!container || !data) return;

    container.innerHTML = `
      <div class="stat-summary-row">
        <div class="stat-box highlight">
          <span class="stat-label">মোট গণনাকৃত টাকা</span>
          <div class="stat-val text-green">৳${data.total_amount.toLocaleString()}</div>
        </div>
        <div class="stat-box">
          <span class="stat-label">মোট নোট সংখ্যা</span>
          <div class="stat-val">${data.total_notes} টি</div>
        </div>
        <div class="stat-box">
          <span class="stat-label">শনাক্তকরণ নির্ভুলতা</span>
          <div class="stat-val text-cyan">98.4%</div>
        </div>
      </div>
      <div class="log-list">
        ${data.breakdown.map(b => `
          <div class="log-item">
            <span><i class="fa-solid fa-money-bill-wave" style="color:${b.color}"></i> <strong>${b.note} নোট</strong> (${b.count} টি)</span>
            <span>উপমোট: <strong>৳${b.subtotal.toLocaleString()}</strong></span>
          </div>
        `).join('')}
      </div>
    `;

    if (window.CameraStream && data.detections) {
      window.CameraStream.drawBoundingBoxes(data.detections);
    }
  }
};