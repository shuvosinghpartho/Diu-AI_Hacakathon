const CameraStream = {
  video: null,
  canvas: null,
  ctx: null,
  stream: null,
  isActive: false,

  init() {
    this.video = document.getElementById('videoElement');
    this.canvas = document.getElementById('overlayCanvas');
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
      if (this.stream) {
        this.stop();
      }
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: { ideal: "environment" }
        },
        audio: false
      });

      this.video.srcObject = this.stream;
      this.video.classList.remove('hidden');
      this.isActive = true;

      const placeholder = document.getElementById('cameraPlaceholder');
      if (placeholder) placeholder.style.display = 'none';

      const uploadedImg = document.getElementById('uploadedImgPreview');
      if (uploadedImg) uploadedImg.remove();

      return true;
    } catch (err) {
      console.error("[CameraStream] Camera stream could not be started:", err);
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

  stop() {
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }
    this.isActive = false;
    this.clearCanvas();
    if (this.video) this.video.classList.add('hidden');
    const placeholder = document.getElementById('cameraPlaceholder');
    if (placeholder) placeholder.style.display = 'flex';
  },

  clearCanvas() {
    if (this.ctx && this.canvas) {
      this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }
  },

  drawBoundingBoxes(detections = []) {
    if (!this.ctx || !this.canvas) return;
    this.syncCanvasResolution();
    this.clearCanvas();
    if (this.video) this.video.classList.add('hidden');

    if (!detections || detections.length === 0) return;

    const scaleX = this.canvas.width / 640;
    const scaleY = this.canvas.height / 360;

    detections.forEach(det => {
      const rx = det.x * scaleX;
      const ry = det.y * scaleY;
      const rw = det.w * scaleX;
      const rh = det.h * scaleY;

      this.ctx.strokeStyle = det.color || '#00e5ff';
      this.ctx.lineWidth = 3;
      this.ctx.strokeRect(rx, ry, rw, rh);

      this.ctx.fillStyle = det.color || '#00e5ff';
      const fontSize = Math.max(12, Math.floor(13 * scaleX));
      this.ctx.font = `bold ${fontSize}px Plus Jakarta Sans, sans-serif`;

      const textWidth = this.ctx.measureText(det.label).width;
      this.ctx.fillRect(rx, Math.max(0, ry - 24), textWidth + 12, 24);

      this.ctx.fillStyle = '#07090e';
      this.ctx.fillText(det.label, rx + 6, Math.max(16, ry - 7));
    });
  }
};