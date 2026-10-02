const MOCK_MODULE_DATABASE = {
  cash_count: {
    id: "cash_count",
    title: "1. Real-Time Cash Counter (YOLOv8 Engine)",
    desc: "ক্যামেরা ফ্রেমে থাকা বাংলাদেশী টাকার নোট শনাক্ত ও মোট পরিমাণ তাৎক্ষণিক গণনা।",
    badge: "PRECISION: 98.4%",
    total_notes: 4,
    total_amount: 2500,
    breakdown: [
      { note: "৳1000", count: 2, subtotal: 2000, color: "#10b981" },
      { note: "৳500", count: 1, subtotal: 500, color: "#00e5ff" },
      { note: "৳100", count: 1, subtotal: 100, color: "#f59e0b" }
    ],
    detections: [
      { label: "৳1000 Note (98%)", x: 40, y: 50, w: 240, h: 130, color: "#10b981" },
      { label: "৳1000 Note (96%)", x: 310, y: 70, w: 230, h: 125, color: "#10b981" },
      { label: "৳500 Note (97%)", x: 60, y: 220, w: 220, h: 120, color: "#00e5ff" },
      { label: "৳100 Note (94%)", x: 320, y: 240, w: 210, h: 110, color: "#f59e0b" }
    ],
    bangla_speech: "চারটি নোট শনাক্ত হয়েছে। মোট টাকার পরিমাণ দুই হাজার পাঁচশত টাকা।"
  },

  fake_note: {
    id: "fake_note",
    title: "2. Fake Note Screener (Security Pattern Analysis)",
    desc: "অপটিক্যাল ভ্যারিয়েবল ইংক (OVI), মাইক্রোপ্রিন্ট ও সিকিউরিটি থ্রেড পরীক্ষা।",
    badge: "INSPECTION: UV/TEXTURE",
    verdict: "SUSPECT_NOTE",
    verdict_label: "নকল / সন্দেহজনক নোট",
    confidence: "94.2%",
    features_failed: [
      "Security Thread Optical Shift Failed (সুতা পরিবর্তনশীল নয়)",
      "Micro-print Intaglio Missing (খসখসে কালির অভাব)",
      "UV Watermark Inconsistency (রয়েল বেঙ্গল টাইগার জলছাপ অনুপস্থিত)"
    ],
    detections: [
      { label: "CRITICAL: THREAD MISALIGNMENT", x: 120, y: 90, w: 380, h: 220, color: "#ef4444" }
    ],
    bangla_speech: "সতর্কতা! নোটটিতে নিরাপত্তা সুতা ও জলছাপের বিচ্যুতি ধরা পড়েছে। এটি জাল নোট হওয়ার তীব্র সম্ভাবনা রয়েছে।"
  },

  number_ocr: {
    id: "number_ocr",
    title: "3. Mobile Number OCR & Auto-Extractor",
    desc: "কাগজে লেখা বা প্রিন্টেড ১১-ডিজিটের বাংলাদেশী মোবাইল নম্বর শনাক্তকরণ।",
    badge: "BD REGEX: MATCHED",
    extracted_number: "01719842510",
    carrier: "Grameenphone (GP)",
    carrier_code: "017",
    confidence: "98.7%",
    detections: [
      { label: "MSISDN: 01719842510 (99%)", x: 80, y: 150, w: 420, h: 90, color: "#00e5ff" }
    ],
    bangla_speech: "মোবাইল নম্বর শনাক্ত হয়েছে: শূন্য এক সাত এক নয়, আট চার দুই, পাঁচ এক শূন্য।"
  },

  doc_verify: {
    id: "doc_verify",
    title: "4. Transaction Document Verifier (KYC & Slip Engine)",
    desc: "জাতীয় পরিচয়পত্র (NID) ও ব্যাংক চালানের বাউন্ডারি এবং সিল যাচাই।",
    badge: "STATUS: CERTIFIED",
    doc_type: "Smart National ID Card (NID)",
    status: "VALID_DOCUMENT",
    status_label: "বৈধ ও অবিকৃত নথি",
    fields_verified: [
      "Government Crest (গণপ্রজাতন্ত্রী বাংলাদেশ প্রতীক উপস্থিত)",
      "Holographic Seal (হলোগ্রাফিক সিল অক্ষত)",
      "Bengali Text Alignment (ফন্ট বিকৃতি শনাক্ত হয়নি)"
    ],
    detections: [
      { label: "NID BOUNDARY DETECTED (VALID)", x: 70, y: 60, w: 480, h: 280, color: "#10b981" }
    ],
    bangla_speech: "লেনদেন সংক্রান্ত পরিচয়পত্রটি সফলভাবে যাচাই হয়েছে। নথিপত্রটি সম্পূর্ণ বৈধ।"
  },

  receipt_fake: {
    id: "receipt_fake",
    title: "5. Fake Transaction Receipt Forensics (ELA Engine)",
    desc: "পেমেন্ট স্ক্রিনশটের ডিজিটাল কারচুপি, ফন্ট অসঙ্গতি ও TrxID বিশ্লেষণ।",
    badge: "FORENSICS: ELA ACTIVE",
    verdict: "TAMPERED_RECEIPT",
    verdict_label: "জাল বা কারচুপিকৃত রসিদ",
    risk_score: "89%",
    tamper_flags: [
      "Font Misalignment on TrxID (ফন্টের আকার মূল টেমপ্লেটের সাথে অসঙ্গতিপূর্ণ)",
      "High Pixel Compression Noise around Amount: ৳15,000",
      "Timestamp Layer Inconsistency (তারিখ পরে বসানো হয়েছে)"
    ],
    detections: [
      { label: "TAMPERED TEXT AREA (89%)", x: 140, y: 110, w: 320, h: 70, color: "#ef4444" },
      { label: "TRXID FONT ANOMALY", x: 100, y: 210, w: 400, h: 60, color: "#f59e0b" }
    ],
    bangla_speech: "সতর্ক থাকুন! রসিদের ট্রানজ্যাকশন আইডি ও টাকার পরিমাণে ডিজিটাল কারচুপি ধরা পড়েছে। এটি একটি নকল রসিদ।"
  },

  voice_suite: {
    id: "voice_suite",
    title: "6. Assistive Voice Suite for Visually Impaired",
    desc: "দৃষ্টি প্রতিবন্ধী ব্যবহারকারীদের জন্য স্বয়ংক্রিয় অডিও গাইডেন্স সিস্টেম।",
    badge: "TTS: ONLINE",
    tts_status: "Active (Native bn-BD Synthesis)",
    speed: "0.95x Natural Pace",
    latency: "12ms",
    detections: [],
    bangla_speech: "অ্যাসিস্টিভ অডিও মোড সক্রিয় রয়েছে। লেনদেনের প্রতিটি তথ্য স্বয়ংক্রিয়ভাবে বাংলায় ঘোষণা করা হবে।"
  }
};