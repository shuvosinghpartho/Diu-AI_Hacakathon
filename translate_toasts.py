import os

file_path = 'frontend/js/app.js'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    'কপি হয়েছে!': 'copied!',
    'প্রস্তুত': 'is ready',
    '"ক্যামেরা লাইভ ভিউ সক্রিয় হয়েছে"': '"Camera live view activated"',
    '"ক্যামেরা সক্রিয় করা যায়নি। অনুগ্রহ করে পারমিশন চেক করুন।"': '"Could not activate camera. Please check permissions."',
    "'ভয়েস পরীক্ষা সম্পন্ন হয়েছে'": "'Voice test complete'",
    "'API বিশ্লেষণ সফলভাবে সম্পন্ন হয়েছে'": "'API analysis completed successfully'",
    "'স্ক্যান সম্পন্ন করা যায়নি।'": "'Scan could not be completed.'",
    "'অনুগ্রহ করে একটি বৈধ ছবির ফাইল নির্বাচন করুন।'": "'Please select a valid image file.'",
    '"ফাইল লোড হয়েছে। \'Execute AI Scan\' চাপুন।"': '"File loaded. Press \'Verify Information\'."'
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated app.js")
