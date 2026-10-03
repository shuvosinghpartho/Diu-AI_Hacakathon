const NumberScannerUI = {
  render(container, data, notify) {
    container.replaceChildren();
    const numbers = Array.isArray(data.numbers) ? data.numbers : [];
    const message = document.createElement('p');
    message.className = 'text-sm text-gray-300';
    message.setAttribute('role', 'status');
    message.textContent = data.pending ? 'নম্বর শনাক্ত করা হচ্ছে…'
      : data.error ? data.error
      : !data.scanned ? 'ছবি আপলোড করুন অথবা ক্যামেরা চালু করে স্ক্যান করুন।'
      : !numbers.length ? 'কোনো বৈধ বাংলাদেশি মোবাইল নম্বর পাওয়া যায়নি। পরিষ্কার ছবি দিয়ে আবার চেষ্টা করুন।'
      : `${numbers.length}টি নম্বর পাওয়া গেছে। কপি করার আগে ছবির সঙ্গে মিলিয়ে নিন।`;
    container.appendChild(message);
    if (!numbers.length) return;

    const label = document.createElement('label');
    label.htmlFor = 'numberSelection';
    label.textContent = 'কপি করার নম্বর নির্বাচন করুন';
    label.className = 'text-sm text-gray-300';
    const select = document.createElement('select');
    select.id = 'numberSelection';
    select.className = 'w-full p-3 rounded-xl bg-dark-800 border border-white/10 text-white';
    numbers.forEach(item => {
      const option = document.createElement('option');
      option.value = item.number;
      option.textContent = `${item.number} — ${item.carrier}`;
      select.appendChild(option);
    });
    const detail = document.createElement('p');
    detail.className = 'text-sm text-brand-400';
    const updateDetail = () => {
      const item = numbers.find(entry => entry.number === select.value);
      detail.textContent = `${item.carrier} · OCR কনফিডেন্স ${(item.confidence * 100).toFixed(1)}%`;
    };
    select.addEventListener('change', updateDetail);
    updateDetail();
    const note = document.createElement('p');
    note.className = 'text-xs text-gray-400';
    note.textContent = 'অপারেটর নম্বরের প্রিফিক্স অনুযায়ী দেখানো হচ্ছে। পোর্ট করা নম্বরের বর্তমান নেটওয়ার্ক আলাদা হতে পারে।';
    const copy = document.createElement('button');
    copy.id = 'btnCopyNumber';
    copy.className = 'w-full py-3 rounded-xl bg-brand-500/20 border border-brand-500/30 text-brand-400';
    copy.textContent = 'নির্বাচিত নম্বর কপি করুন';
    copy.addEventListener('click', async () => {
      const number = select.value;
      copy.disabled = true;
      try {
        if (navigator.clipboard?.writeText) {
          await navigator.clipboard.writeText(number);
        } else {
          manual.focus?.();
          manual.select();
          if (!document.execCommand?.('copy')) throw new Error('Clipboard unavailable');
        }
        notify(`নম্বর ${number} কপি হয়েছে!`);
      } catch {
        manual.focus?.();
        manual.select();
        notify('কপি করা যায়নি। নম্বরটি নির্বাচন করে ম্যানুয়ালি কপি করুন।', true);
      } finally {
        copy.disabled = false;
      }
    });
    const manual = document.createElement('input');
    manual.readOnly = true;
    manual.value = select.value;
    manual.setAttribute('aria-label', 'নির্বাচিত মোবাইল নম্বর');
    manual.className = 'w-full p-3 rounded-xl bg-dark-800 text-white font-mono';
    manual.addEventListener('click', () => manual.select());
    select.addEventListener('change', () => { manual.value = select.value; });
    container.append(label, select, detail, note, copy, manual);
  }
};
