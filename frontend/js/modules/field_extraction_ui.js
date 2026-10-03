const FieldExtractionUI = {
  labels: {
    name: 'Name', father_name: "Father's name", mother_name: "Mother's name",
    date_of_birth: 'Date of birth', nid_number: 'NID number', passport_number: 'Passport number',
    provider: 'Provider', transaction_id: 'Transaction ID', amount: 'Amount',
    date_time: 'Date and time', sender: 'Sender', receiver: 'Receiver',
    reference: 'Reference', transaction_type: 'Transaction type',
    counterparty_name: 'Person / store / bank', agent_number: 'Agent number',
    bank_name: 'Bank'
  },

  render(container, data, kind) {
    container.replaceChildren();
    const heading = document.createElement('div');
    heading.className = 'bg-brand-500/10 border border-brand-500/20 rounded-xl p-4';
    const title = document.createElement('p');
    title.className = 'text-lg font-bold text-brand-400';
    title.textContent = kind === 'document' ? (data.doc_type || 'Unknown document')
      : (data.verdict_label || 'Receipt OCR');
    const status = document.createElement('p');
    status.className = 'text-sm text-gray-300 mt-1';
    status.textContent = kind === 'document' ? (data.status_label || '')
      : 'OCR extracts text only. Confirm payment in the provider or bank system.';
    heading.append(title, status);
    container.appendChild(heading);

    const fields = data.extracted_fields || {};
    const grid = document.createElement('div');
    grid.className = 'grid grid-cols-1 md:grid-cols-2 gap-3';
    Object.entries(fields).forEach(([key, value]) => {
      const card = document.createElement('div');
      card.className = 'bg-dark-800/50 border border-white/5 rounded-xl p-3';
      const label = document.createElement('div');
      label.className = 'text-xs uppercase text-gray-400';
      label.textContent = this.labels[key] || key.replaceAll('_', ' ');
      const output = document.createElement('div');
      output.className = 'text-base text-white font-mono break-all mt-1';
      output.textContent = String(value);
      card.append(label, output);
      grid.appendChild(card);
    });
    if (!Object.keys(fields).length) {
      const empty = document.createElement('p');
      empty.className = 'text-sm text-gray-400';
      empty.textContent = data.scanned ? 'No supported fields were recognized. See OCR text below.'
        : 'Upload a clear image and run the scan.';
      grid.appendChild(empty);
    }
    container.appendChild(grid);

    if (Array.isArray(data.raw_text) && data.raw_text.length) {
      const details = document.createElement('details');
      details.className = 'bg-dark-800/50 border border-white/5 rounded-xl p-4';
      const summary = document.createElement('summary');
      summary.className = 'cursor-pointer text-sm text-gray-300';
      summary.textContent = 'Show all OCR text';
      const raw = document.createElement('pre');
      raw.className = 'mt-3 text-sm text-gray-300 whitespace-pre-wrap';
      raw.textContent = data.raw_text.join('\n');
      details.append(summary, raw);
      container.appendChild(details);
    }
  }
};
