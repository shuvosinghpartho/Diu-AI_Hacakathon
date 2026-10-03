import re
from statistics import mean

from .ocr_service import ocr_service


class FieldExtractionService:
    digits = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")

    @staticmethod
    def _value_after_label(lines, labels):
        label_pattern = "|".join(re.escape(label) for label in sorted(labels, key=len, reverse=True))
        for index, line in enumerate(lines):
            match = re.search(rf"^\s*(?:{label_pattern})(?:\s*[:\-]\s*|\s+)(.+)$", line, re.I)
            if match and match.group(1).strip():
                return match.group(1).strip()
            if re.fullmatch(rf"\s*(?:{label_pattern})\s*[:\-]?\s*", line, re.I) and index + 1 < len(lines):
                return lines[index + 1].strip()
        return None

    @staticmethod
    def _first_match(text, patterns):
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return match.group(1) if match.lastindex else match.group(0)
        return None

    @staticmethod
    def _box(reading):
        points = reading.get("bbox") or []
        if len(points) < 2:
            return None
        try:
            xs = [float(point[0]) for point in points]
            ys = [float(point[1]) for point in points]
        except (TypeError, ValueError, IndexError):
            return None
        return min(xs), min(ys), max(xs), max(ys)

    def _value_below_label(self, readings, labels):
        """Find the closest OCR value below a label in the same visual column."""
        normalized_labels = {label.casefold() for label in labels}
        for label_reading in readings:
            if label_reading["text"].strip().rstrip(":").casefold() not in normalized_labels:
                continue
            label_box = self._box(label_reading)
            if not label_box:
                continue
            lx1, _, _, ly2 = label_box
            choices = []
            for candidate in readings:
                if candidate is label_reading:
                    continue
                candidate_box = self._box(candidate)
                if not candidate_box:
                    continue
                cx1, cy1, _, _ = candidate_box
                vertical_gap = cy1 - ly2
                horizontal_gap = abs(cx1 - lx1)
                if -5 <= vertical_gap <= 130 and horizontal_gap <= 130:
                    choices.append((vertical_gap * 3 + horizontal_gap, candidate["text"].strip()))
            if choices:
                return min(choices, key=lambda choice: choice[0])[1]
        return None

    def _top_card_values(self, readings, transaction_type):
        """Return OCR lines visually located between the title and field grid."""
        title_reading = next(
            (item for item in readings if item["text"].strip().casefold() == transaction_type.casefold()), None)
        title_box = self._box(title_reading) if title_reading else None
        field_labels = {
            "sent from", "time", "date", "date & time", "transaction id", "trx id",
            "total", "amount", "reference", "ref",
        }
        field_tops = [
            box[1] for item in readings
            if item["text"].strip().rstrip(":").casefold() in field_labels
            if (box := self._box(item))
        ]
        if not title_box or not field_tops:
            return []
        top, bottom = title_box[3], min(field_tops)
        values = []
        for item in readings:
            box = self._box(item)
            value = item["text"].strip()
            if box and top < box[1] < bottom and value.casefold() != transaction_type.casefold():
                values.append(value)
        return values

    def _base(self, readings):
        lines = [item["text"] for item in readings]
        confidence = round(mean(item["confidence"] for item in readings), 3) if readings else 0.0
        return lines, "\n".join(lines).translate(self.digits), confidence

    def parse_document(self, readings):
        lines, text, confidence = self._base(readings)
        lowered = text.lower()
        if "passport" in lowered or "পাসপোর্ট" in text:
            doc_type = "Bangladesh Passport"
        elif any(token in lowered for token in ("national id", "identity card", "nid")) or "জাতীয় পরিচয়" in text:
            doc_type = "Bangladesh National ID"
        else:
            doc_type = "Unknown document"

        fields = {}
        for key, labels in (
            ("name", ["Name", "নাম"]),
            ("father_name", ["Father's Name", "Father", "পিতা"]),
            ("mother_name", ["Mother's Name", "Mother", "মাতা"]),
        ):
            value = self._value_after_label(lines, labels)
            if value:
                fields[key] = value
        birth = self._first_match(text, [
            r"(?:date of birth|birth|dob|জন্ম(?:\s*তারিখ)?)\s*[:\-]?\s*([0-3]?\d[./-][01]?\d[./-](?:19|20)?\d{2})"
        ])
        if birth:
            fields["date_of_birth"] = birth
        passport = self._first_match(text, [r"\b([A-Z]{1,2}\d{7})\b"])
        nid = self._first_match(text, [
            r"(?:nid|national id|id no|পরিচয় নং)\s*[:\-]?\s*(\d{10}|\d{13}|\d{17})\b",
            r"\b(\d{10}|\d{13}|\d{17})\b",
        ])
        if passport:
            fields["passport_number"] = passport
        elif nid:
            fields["nid_number"] = nid

        return {
            "doc_type": doc_type,
            "status": "OCR_EXTRACTED" if readings else "NO_TEXT_FOUND",
            "status_label": "Fields extracted; authenticity not verified" if readings else "No readable text found",
            "confidence": confidence,
            "extracted_fields": fields,
            "raw_text": lines,
            "fields_verified": list(fields.keys()),
            "detections": [],
            "bangla_speech": (f"নথি থেকে {len(fields)}টি তথ্য পড়া হয়েছে। ছবির সঙ্গে মিলিয়ে দেখুন।"
                              if readings else "ছবিতে পড়ার মতো লেখা পাওয়া যায়নি।"),
        }

    def parse_receipt(self, readings):
        lines, text, confidence = self._base(readings)
        lowered = text.lower()
        provider = next((name for name in ("bKash", "Nagad", "Rocket", "Upay")
                         if name.lower() in lowered), None)
        if provider is None and any(token in text for token in ("বিকাশ", "কতাশ")):
            provider = "bKash"
        fields = {}
        if provider:
            fields["provider"] = provider

        transaction_id = self._value_below_label(readings, ["Transaction ID", "Trx ID"])
        if not transaction_id:
            transaction_id = self._first_match(text, [
                r"(?:trx\s*id|transaction\s*id)\s*[:#\-]?\s*([A-Z0-9/_-]{6,30})"
            ])
        if transaction_id and re.fullmatch(r"[A-Z0-9/_-]{6,30}", transaction_id, re.I):
            fields["transaction_id"] = transaction_id

        amount_source = self._value_below_label(readings, ["Amount", "Total", "টাকার পরিমাণ", "পরিমাণ"])
        if amount_source and re.match(r"^৮(?=[0-9])", amount_source.strip()):
            amount_source = amount_source.strip()[1:]
        normalized_amount = (amount_source or "").translate(self.digits)
        amount = self._first_match(normalized_amount, [r"(?:BDT|Tk|৳)?\s*([\d,]+(?:\.\d{1,2})?)"])
        if not amount:
            amount = self._first_match(text, [
                r"(?:amount|total|টাকার পরিমাণ|পরিমাণ)\s*[:\-]?\s*(?:BDT|Tk|৳)?\s*([\d,]+(?:\.\d{1,2})?)",
                r"(?:BDT|Tk|৳)\s*([\d,]+(?:\.\d{1,2})?)",
            ])
        if amount:
            fields["amount"] = amount.replace(",", "")

        date_time = self._value_below_label(readings, ["Time", "Date", "Date & Time"])
        if not date_time:
            date_time = self._first_match(text, [
                r"((?:[0-2]?\d:\d{2}(?::\d{2})?\s*(?:am|pm)?\s+)?[0-3]?\d[./-][01]?\d[./-](?:19|20)?\d{2})",
                r"((?:[0-3]?\d[./-][01]?\d[./-](?:19|20)?\d{2})(?:\s+[0-2]?\d:\d{2}(?::\d{2})?\s*(?:am|pm)?)?)",
            ])
        if date_time:
            fields["date_time"] = date_time

        sender = self._value_below_label(readings, ["Sent From", "From", "Sender", "প্রেরক"])
        if not sender:
            sender = self._value_after_label(lines, ["Sent From", "From", "Sender", "প্রেরক"])
        receiver = self._value_after_label(lines, ["To", "T0", "Receiver", "Recipient", "প্রাপক"])
        phone_numbers = []
        for match in re.finditer(r"(?<!\d)(01[3-9][0-9]{8})(?!\d)", text):
            if match.group(1) not in phone_numbers:
                phone_numbers.append(match.group(1))
        if not receiver and phone_numbers:
            receiver = phone_numbers[0]
        if sender:
            fields["sender"] = sender
        if receiver:
            fields["receiver"] = receiver

        reference = self._value_below_label(readings, ["Reference", "Ref"])
        if reference:
            fields["reference"] = reference
        transaction_types = {
            "send money": "Send Money",
            "mobile recharge": "Mobile Recharge",
            "received money": "Received Money",
            "cash out": "Cash Out",
            "loan repayment": "Loan Repayment",
            "payment": "Payment",
        }
        transaction_type = next(
            (canonical for line in lines
             if (canonical := transaction_types.get(line.strip().casefold()))), None)
        if transaction_type:
            fields["transaction_type"] = transaction_type

            top_values = self._top_card_values(readings, transaction_type)
            name_candidates = []
            for value in top_values:
                cleaned = re.sub(r"[_\s-]*01[3-9][0-9]{8}\b", "", value).strip(" _-")
                if (cleaned and not re.fullmatch(r"[0-9*]+", cleaned)
                        and cleaned.casefold() not in {"bkash", "বিকাশ", "কতাশ"}
                        and cleaned.casefold() not in {name.casefold() for name in name_candidates}):
                    name_candidates.append(cleaned)
            if name_candidates:
                fields["counterparty_name"] = name_candidates[0]
            if phone_numbers:
                if transaction_type == "Received Money":
                    fields["sender"] = phone_numbers[0]
                    fields.pop("receiver", None)
                elif transaction_type == "Cash Out":
                    fields["agent_number"] = phone_numbers[0]
                    fields.pop("receiver", None)
                else:
                    fields["receiver"] = phone_numbers[0]
            if transaction_type == "Loan Repayment" and name_candidates:
                fields["bank_name"] = name_candidates[0]

        return {
            "verdict": "FIELDS_EXTRACTED" if readings else "NO_TEXT_FOUND",
            "verdict_label": "Receipt fields extracted; payment not verified" if readings else "No readable text found",
            "risk_score": "N/A",
            "confidence": confidence,
            "extracted_fields": fields,
            "raw_text": lines,
            "tamper_flags": [],
            "detections": [],
            "bangla_speech": (f"রসিদ থেকে {len(fields)}টি তথ্য পড়া হয়েছে। লেনদেনটি আলাদাভাবে যাচাই করুন।"
                              if readings else "রসিদে পড়ার মতো লেখা পাওয়া যায়নি।"),
        }

    def extract_document(self, image_bytes):
        return self.parse_document(ocr_service.extract_text(image_bytes))

    def extract_receipt(self, image_bytes):
        return self.parse_receipt(ocr_service.extract_text(image_bytes))


field_extraction_service = FieldExtractionService()
