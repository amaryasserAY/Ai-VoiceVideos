import google.generativeai as genai
import os
from dotenv import load_dotenv

# تحميل المفتاح
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

print("🔍 جاري البحث عن الموديلات المتاحة لمفتاحك...")

try:
    found = False
    # جلب قائمة الموديلات
    for m in genai.list_models():
        # نحن نبحث فقط عن الموديلات التي تستطيع توليد نصوص (generateContent)
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ متاح: {m.name}")
            found = True
    
    if not found:
        print("⚠️ لم يتم العثور على أي موديل! تأكد من تفعيل الـ API في حساب جوجل.")

except Exception as e:
    print(f"❌ حدث خطأ أثناء الاتصال: {e}")