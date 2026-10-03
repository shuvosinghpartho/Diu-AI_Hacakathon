const ImageCropper = {
  canvas: null, ctx: null, wrapper: null, image: null, sourceFile: null,
  selection: null, startPoint: null, active: false, resetButton: null, help: null,

  init(wrapper) {
    this.wrapper = wrapper;
    this.canvas = document.createElement('canvas');
    this.canvas.id = 'cropCanvas';
    this.canvas.className = 'absolute inset-0 w-full h-full z-[25] cursor-crosshair';
    this.canvas.style.cssText = 'touch-action:none;display:none';
    wrapper.appendChild(this.canvas);
    this.ctx = this.canvas.getContext('2d');

    this.help = document.createElement('div');
    this.help.className = 'absolute top-3 left-1/2 -translate-x-1/2 z-[30] px-3 py-1.5 rounded-lg bg-black/75 text-xs text-white pointer-events-none text-center';
    this.help.textContent = 'Drag over the area to scan';
    this.help.style.display = 'none';
    wrapper.appendChild(this.help);

    this.resetButton = document.createElement('button');
    this.resetButton.type = 'button';
    this.resetButton.className = 'absolute bottom-3 right-3 z-[30] px-3 py-2 rounded-lg bg-dark-800/90 border border-brand-500/40 text-xs text-brand-400';
    this.resetButton.textContent = 'Use full image';
    this.resetButton.style.display = 'none';
    this.resetButton.addEventListener('click', event => {
      event.stopPropagation();
      this.selection = null;
      this.draw();
    });
    wrapper.appendChild(this.resetButton);

    this.canvas.addEventListener('pointerdown', event => this.pointerDown(event));
    this.canvas.addEventListener('pointermove', event => this.pointerMove(event));
    this.canvas.addEventListener('pointerup', event => this.pointerUp(event));
    this.canvas.addEventListener('pointercancel', () => { this.startPoint = null; });
    window.addEventListener('resize', () => this.resize());
  },

  setImage(file, imageElement) {
    this.sourceFile = file;
    this.image = imageElement;
    this.selection = null;
    this.active = true;
    this.canvas.style.display = 'block';
    this.help.style.display = 'block';
    this.resetButton.style.display = 'block';
    this.resize();
  },

  clear() {
    this.active = false;
    this.sourceFile = this.image = this.selection = this.startPoint = null;
    if (this.canvas) this.canvas.style.display = 'none';
    if (this.help) this.help.style.display = 'none';
    if (this.resetButton) this.resetButton.style.display = 'none';
  },

  resize() {
    if (!this.canvas || !this.wrapper) return;
    const rect = this.wrapper.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    const oldWidth = this.canvas.width || rect.width;
    const oldHeight = this.canvas.height || rect.height;
    if (this.selection) {
      const sx = rect.width / oldWidth, sy = rect.height / oldHeight;
      this.selection = { x: this.selection.x * sx, y: this.selection.y * sy,
        width: this.selection.width * sx, height: this.selection.height * sy };
    }
    this.canvas.width = Math.round(rect.width);
    this.canvas.height = Math.round(rect.height);
    this.draw();
  },

  point(event) {
    const rect = this.canvas.getBoundingClientRect();
    return { x: Math.max(0, Math.min(this.canvas.width, event.clientX - rect.left)),
      y: Math.max(0, Math.min(this.canvas.height, event.clientY - rect.top)) };
  },

  pointerDown(event) {
    if (!this.active) return;
    this.canvas.setPointerCapture?.(event.pointerId);
    this.startPoint = this.point(event);
    this.selection = { x: this.startPoint.x, y: this.startPoint.y, width: 0, height: 0 };
    this.draw();
  },

  pointerMove(event) {
    if (!this.startPoint) return;
    const current = this.point(event);
    this.selection = { x: Math.min(this.startPoint.x, current.x), y: Math.min(this.startPoint.y, current.y),
      width: Math.abs(current.x - this.startPoint.x), height: Math.abs(current.y - this.startPoint.y) };
    this.draw();
  },

  pointerUp(event) {
    if (!this.startPoint) return;
    this.pointerMove(event);
    this.startPoint = null;
    if (this.selection.width < 12 || this.selection.height < 12) this.selection = null;
    this.draw();
  },

  draw() {
    if (!this.ctx) return;
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    if (!this.active || !this.selection) return;
    const { x, y, width, height } = this.selection;
    this.ctx.fillStyle = 'rgba(2,6,23,.5)';
    this.ctx.fillRect(0, 0, this.canvas.width, y);
    this.ctx.fillRect(0, y, x, height);
    this.ctx.fillRect(x + width, y, this.canvas.width - x - width, height);
    this.ctx.fillRect(0, y + height, this.canvas.width, this.canvas.height - y - height);
    this.ctx.strokeStyle = '#22d3ee';
    this.ctx.lineWidth = 3;
    this.ctx.setLineDash([8, 5]);
    this.ctx.strokeRect(x, y, width, height);
    this.ctx.setLineDash([]);
  },

  calculateSourceRect(iw, ih, vw, vh, selection) {
    if (!selection) return null;
    const scale = Math.min(vw / iw, vh / ih);
    const rw = iw * scale, rh = ih * scale;
    const ox = (vw - rw) / 2, oy = (vh - rh) / 2;
    const left = Math.max(ox, selection.x), top = Math.max(oy, selection.y);
    const right = Math.min(ox + rw, selection.x + selection.width);
    const bottom = Math.min(oy + rh, selection.y + selection.height);
    if (right - left < 2 || bottom - top < 2) return null;
    return { x: Math.round((left - ox) / scale), y: Math.round((top - oy) / scale),
      width: Math.round((right - left) / scale), height: Math.round((bottom - top) / scale) };
  },

  async getCroppedBlob() {
    if (!this.active || !this.sourceFile || !this.image || !this.selection) return this.sourceFile;
    const source = this.calculateSourceRect(this.image.naturalWidth, this.image.naturalHeight,
      this.canvas.width, this.canvas.height, this.selection);
    if (!source) return this.sourceFile;
    const output = document.createElement('canvas');
    output.width = source.width;
    output.height = source.height;
    output.getContext('2d').drawImage(this.image, source.x, source.y, source.width, source.height,
      0, 0, source.width, source.height);
    return new Promise((resolve, reject) => output.toBlob(
      blob => blob ? resolve(blob) : reject(new Error('Could not crop the image.')), 'image/jpeg', .95));
  }
};
