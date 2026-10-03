const CameraStream = {
  video: null,
  canvas: null,
  ctx: null,
  stream: null,
  isActive: false,
  lastError: '',

  init() {
    this.video = document.getElementById('webcamFeed');
    this.canvas = document.getElementById('detectionCanvas');
    if (this.canvas) {
      this.ctx = this.canvas.getContext('2d');
    }
    this.syncCanvasResolution();
    window.addEventListener('resize', () => this.syncCanvasResolution());
  },

  syncCanvasResolution() {
    if (!this.canvas || !this.canvas.parentElement) return;
    const rect = this.canvas.parentElement.getBoundingClientRect();
    this.canvas.width = rect.width;
    this.canvas.height = rect.height;
  },

  async start() {
    try {
      this.lastError = '';
      if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
        this.lastError = 'Camera requires HTTPS on a phone. Use Upload Image, or open the app through an HTTPS address.';
        return false;
      }
      if (this.stream) {
        this.stop();
      }
      const frozenFrame = document.getElementById('frozenFramePreview');
      if (frozenFrame) frozenFrame.remove();
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: { ideal: "environment" }
        },
        audio: false
      });

      this.video.srcObject = this.stream;
      this.isActive = true;

      const placeholder = document.getElementById('cameraPlaceholder');
      if (placeholder) placeholder.style.display = 'none';

      const uploadedImg = document.getElementById('uploadedImgPreview');
      if (uploadedImg) uploadedImg.remove();

      return true;
    } catch (err) {
      console.error("[CameraStream] Camera stream could not be started:", err);
      this.lastError = err.name === 'NotAllowedError'
        ? 'Camera permission was denied. Allow camera access in the browser site settings.'
        : 'The camera could not be opened. Check browser permission and whether another app is using it.';
      return false;
    }
  },

  async captureFrame() {
    if (!this.isActive || !this.video || !this.video.videoWidth || !this.video.videoHeight) {
      throw new Error('Start the camera and wait for the preview before scanning.');
    }

    const frame = document.createElement('canvas');
    frame.width = this.video.videoWidth;
    frame.height = this.video.videoHeight;
    frame.getContext('2d').drawImage(this.video, 0, 0, frame.width, frame.height);

    return new Promise((resolve, reject) => {
      frame.toBlob(blob => {
        if (blob) resolve(blob);
        else reject(new Error('Could not capture a camera frame.'));
      }, 'image/jpeg', 0.92);
    });
  },

  async freezeFrame(blob) {
    if (!(blob instanceof Blob) || !this.video?.parentElement) return;
    const previous = document.getElementById('frozenFramePreview');
    if (previous) previous.remove();

    const preview = document.createElement('img');
    preview.id = 'frozenFramePreview';
    preview.alt = 'Captured camera frame';
    preview.style.cssText = `
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      object-fit: contain;
      object-position: center;
      background: #020617;
      z-index: 2;
    `;
    const objectUrl = URL.createObjectURL(blob);
    await new Promise((resolve, reject) => {
      preview.onload = resolve;
      preview.onerror = reject;
      preview.src = objectUrl;
      this.video.parentElement.appendChild(preview);
    }).finally(() => URL.revokeObjectURL(objectUrl));

    this.video.pause();
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }
    this.isActive = false;
  },

  stop() {
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }
    this.isActive = false;
    this.clearCanvas();
    const frozenFrame = document.getElementById('frozenFramePreview');
    if (frozenFrame) frozenFrame.remove();
    const placeholder = document.getElementById('cameraPlaceholder');
    if (placeholder) placeholder.style.display = 'flex';
  },

  clearCanvas() {
    if (this.ctx && this.canvas) {
      this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }
  },

  drawBoundingBoxes(detections = [], sourceWidth = 640, sourceHeight = 360) {
    if (!this.ctx || !this.canvas) return;
    this.syncCanvasResolution();
    this.clearCanvas();

    if (!detections || detections.length === 0) return;

    const scale = Math.min(this.canvas.width / sourceWidth, this.canvas.height / sourceHeight);
    const renderedWidth = sourceWidth * scale;
    const renderedHeight = sourceHeight * scale;
    const offsetX = (this.canvas.width - renderedWidth) / 2;
    const offsetY = (this.canvas.height - renderedHeight) / 2;

    detections.forEach(det => {
      const rx = offsetX + det.x * scale;
      const ry = offsetY + det.y * scale;
      const rw = det.w * scale;
      const rh = det.h * scale;

      this.ctx.strokeStyle = det.color || '#00e5ff';
      this.ctx.lineWidth = 3;
      this.ctx.strokeRect(rx, ry, rw, rh);

      this.ctx.fillStyle = det.color || '#00e5ff';
      const fontSize = Math.max(12, Math.min(18, Math.floor(13 * scale)));
      this.ctx.font = `bold ${fontSize}px Plus Jakarta Sans, sans-serif`;

      const textWidth = this.ctx.measureText(det.label).width;
      this.ctx.fillRect(rx, Math.max(0, ry - 24), textWidth + 12, 24);

      this.ctx.fillStyle = '#07090e';
      this.ctx.fillText(det.label, rx + 6, Math.max(16, ry - 7));
    });
  }
};
