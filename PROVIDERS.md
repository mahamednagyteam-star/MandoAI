# MandoAI — إعداد مزودي النماذج

يحتوي الخادم على موصلات اختيارية إلى واجهات API الرسمية. لا يتم تضمين مفاتيح الوصول داخل المستودع أو المتصفح.

أضف المتغيرات المطلوبة من Railway → Service → Variables، ثم أعد النشر أو انتظر إعادة التشغيل:

| المزود | المتغيرات المطلوبة | الافتراضي |
|---|---|---|
| OpenAI | OPENAI_API_KEY | OPENAI_MODEL=gpt-4.1-mini |
| DeepSeek | DEEPSEEK_API_KEY | DEEPSEEK_MODEL=deepseek-chat |
| Perplexity | PERPLEXITY_API_KEY | PERPLEXITY_MODEL=sonar |
| Claude | ANTHROPIC_API_KEY | ANTHROPIC_MODEL=claude-3-5-haiku-latest |
| Gemini | GEMINI_API_KEY | GEMINI_MODEL=gemini-2.5-flash |
| Llama عبر مزود متوافق مع OpenAI | LLAMA_API_KEY وLLAMA_BASE_URL وLLAMA_MODEL | لا يوجد افتراضي |

يمكن تخصيص عنوان API عبر OPENAI_BASE_URL وDEEPSEEK_BASE_URL وPERPLEXITY_BASE_URL وANTHROPIC_BASE_URL وGEMINI_BASE_URL عند استخدام نقطة نهاية متوافقة مع وثائق المزود.

النماذج الواردة من سكربتات Ptero وAppZone وAI Multi Search ظلت ظاهرة في القائمة لكنها غير مفعّلة؛ السكربتات تعتمد على رموز جلسات/اعتمادات خاصة بالخدمات أو معرفات استخدام غير موثقة، لذلك لم يتم نسخ آليات استخراجها أو إعادة استخدامها. فعّلها فقط بعد توفير API رسمي موثق ومصرّح به من صاحب الخدمة.

مفاتيح API سرية: لا تضعها في ملفات HTML أو GitHub أو رسائل الواجهة.