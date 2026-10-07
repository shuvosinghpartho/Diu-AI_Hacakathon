const VisionPayApi = {
  baseUrl: window.VISIONPAY_API_BASE_URL || 'http://127.0.0.1:8000',

  endpoints: {
    cash_count: '/api/v1/cash/count',
    fake_note: '/api/v1/currency/verify-note',
    number_ocr: '/api/v1/ocr/extract-number',
    doc_verify: '/api/v1/document/verify',
    receipt_fake: '/api/v1/receipt/analyze-screenshot',
    dashboard_stats: '/api/v1/dashboard/stats'
  },

  async analyze(moduleKey, imageBlob, filename = 'capture.jpg') {
    const endpoint = this.endpoints[moduleKey];
    if (!endpoint) {
      throw new Error(`No vision endpoint is configured for ${moduleKey}.`);
    }
    if (!(imageBlob instanceof Blob)) {
      throw new Error('Choose an image or capture a camera frame before scanning.');
    }

    const formData = new FormData();
    formData.append('file', imageBlob, filename || 'capture.jpg');
    if (moduleKey === 'cash_count') {
      const denomination = document.getElementById('cashDenomination')?.value || '0';
      formData.append('denomination', denomination);
    }

    let response;
    try {
      response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'POST',
        headers: {
          'X-API-Key': 'vp-live-2026-secure-key'
        },
        body: formData
      });
    } catch (error) {
      throw new Error('Cannot reach the VisionPay API. Check that the backend is running.');
    }

    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      const detail = typeof payload.detail === 'string' ? payload.detail : 'Image analysis failed.';
      throw new Error(detail);
    }
    if (!payload.success) {
      throw new Error('The VisionPay API did not return a successful analysis.');
    }

    return payload;
  },

  async getDashboardStats() {
    try {
      const response = await fetch(`${this.baseUrl}${this.endpoints.dashboard_stats}`, {
        headers: { 'X-API-Key': 'vp-live-2026-secure-key' }
      });
      if (!response.ok) return null;
      return await response.json();
    } catch (e) {
      console.error("Dashboard fetch error:", e);
      return null;
    }
  }
};
