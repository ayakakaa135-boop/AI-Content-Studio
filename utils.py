import os
import requests
import json
import base64
from io import BytesIO
from dotenv import load_dotenv
import whisper
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

# =============================
# إعدادات Ollama
# =============================
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:3b"
API_KEY = os.getenv("STABILITY_API_KEY")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data")
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_db")

# =======
# =============================
# RAG - إنشاء Vector DB
# =============================
def initialize_rag_system():
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, "data")
    chroma_path = os.path.join(base_dir, "chroma_db")

    if not os.path.exists(data_path) or not os.listdir(data_path):
        print("⚠️ مجلد data فارغ.")
        return None

    try:

        loader = DirectoryLoader(data_path, glob="./*.txt", loader_cls=TextLoader, loader_kwargs={'encoding': 'utf-8'})
        documents = loader.load()

        if not documents:
            print("❌ لم يتم العثور على أي نصوص في ملفات الـ txt.")
            return None

        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        splits = text_splitter.split_documents(documents)

        embeddings = OllamaEmbeddings(model="nomic-embed-text")

        vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=embeddings,
            persist_directory=chroma_path
        )
        print("✅ تم إنشاء قاعدة بيانات المتجهات من ملفات TXT بنجاح!")
        return vectorstore
    except Exception as e:
        print(f"❌ خطأ أثناء معالجة ملفات النص: {e}")
        return None


def get_rag_chain(vectorstore):
   
    if vectorstore is None:
        return None

    # إعداد الموديل (Qwen)
    llm = OllamaLLM(model=OLLAMA_MODEL)

    # تصميم القالب (Prompt) لضمان الإجابة من المستندات فقط
    template = """استخدم المعلومات التالية فقط للإجابة على سؤال المستخدم. 
    إذا لم تجد الإجابة في المعلومات، قل أنك لا تعرف، ولا تحاول اختلاق إجابة.

    المعلومات المستخرجة من ملفاتك:
    {context}

    سؤال المستخدم: {question}

    الإجابة باللغة العربية:"""

    prompt = ChatPromptTemplate.from_template(template)

 
    chain = (
            {"context": vectorstore.as_retriever(search_kwargs={"k": 3}), "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
    )
    return chain

# =============================
# Ollama Call
# =============================
def call_ollama(prompt, model=OLLAMA_MODEL):
    """
    استدعاء Ollama API (بدون streaming)
    """
    try:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }

        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()

        result = response.json()
        return result.get('response', '').strip()

    except requests.exceptions.RequestException as e:
        print(f"خطأ في الاتصال بـ Ollama: {e}")
        return None


def call_ollama_stream(prompt, model=OLLAMA_MODEL):
    """
    استدعاء Ollama API مع streaming
    يُرجع generator يمكن استخدامه لإرسال البيانات تدريجياً
    """
    try:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True
        }

        response = requests.post(OLLAMA_URL, json=payload, stream=True)
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                try:
                    json_response = json.loads(line)
                    if 'response' in json_response:
                        yield json_response['response']

                   
                    if json_response.get('done', False):
                        break
                except json.JSONDecodeError:
                    continue

    except requests.exceptions.RequestException as e:
        print(f"خطأ في الاتصال بـ Ollama: {e}")
        yield None


# ==========================================
#  دوال التلخيص (عادي + Streaming)
# ==========================================

def summarize_article(article_text):
    """
    تلخيص المقال (عادي)
    """
    prompt = f"""قم بتلخيص المقال التالي بشكل واضح ومختصر باللغة العربية:

{article_text}

الملخص:"""

    return call_ollama(prompt)

def summarize_article_stream(article_text):
    """
    تلخيص المقال (Streaming) مع التأكد من إرسال أجزاء النص بشكل صحيح
    """
    prompt = f"قم بتلخيص المقال التالي بشكل واضح ومختصر باللغة العربية، واستخدم تنسيق Markdown (عناوين ونقاط):\n\n{article_text}\n\nالملخص:"

    # استدعاء دالة البث من Ollama
    for chunk in call_ollama_stream(prompt):
        if chunk:
            yield chunk
# ==========================================
#  دوال مساعدة (عنوان + كلمات مفتاحية)
# ==========================================

def generate_title(article_text):
    """
    توليد عنوان مقترح للمقال
    """
    prompt = f"""اقترح عنواناً جذاباً ومناسباً لتحسين محركات البحث (SEO) للمقال التالي. أعطني العنوان فقط بدون أي شرح أو علامات تنصيص:

{article_text}

العنوان:"""

    return call_ollama(prompt)


def generate_keywords(article_text):
    """
    توليد كلمات مفتاحية
    """
    prompt = f"""استخرج أهم 10 كلمات مفتاحية من النص التالي، مفصولة بفواصل فقط:

{article_text}

الكلمات المفتاحية:"""

    return call_ollama(prompt)


# ==========================================
#  دوال كتابة المقال (عادي + Streaming)
# ==========================================

def write_article_stream(title):

    prompt = f"""
    بصفتك كاتب محتوى خبير (Senior Content Strategist)، اكتب مقالاً معمقاً وحصرياً حول: "{title}"

    يجب أن يتبع المقال القواعد التالية بدقة:
    1. **تنسيق Markdown:** استخدم (#) للعنوان الرئيسي، (##) للعناوين الفرعية، و (**) للكلمات الجوهرية.
    2. **الهيكل:** (مقدمة تخطف الأنظار، فقرات تحليلية مدعومة بالحقائق، قوائم منقطة لسهولة القراءة، خاتمة قوية).
    3. **الواقعية:** ابتعد عن الحشو، وركز على تقديم أحدث المعلومات بأسلوب منطقي ومقنع.
    4. **اللغة:** عربية فصحى عصرية، قوية الأسلوب وسلسة الفهم.

    ابدأ بكتابة المقال الآن:
    """
    return call_ollama_stream(prompt)

def write_article(title):

    prompt = f"""
        بصفتك كاتب محتوى خبير (Senior Content Strategist)، اكتب مقالاً معمقاً وحصرياً حول: "{title}"

        يجب أن يتبع المقال القواعد التالية بدقة:
        1. **تنسيق Markdown:** استخدم (#) للعنوان الرئيسي، (##) للعناوين الفرعية، و (**) للكلمات الجوهرية.
        2. **الهيكل:** (مقدمة تخطف الأنظار، فقرات تحليلية مدعومة بالحقائق، قوائم منقطة لسهولة القراءة، خاتمة قوية).
        3. **الواقعية:** ابتعد عن الحشو، وركز على تقديم أحدث المعلومات بأسلوب منطقي ومقنع.
        4. **اللغة:** عربية فصحى عصرية، قوية الأسلوب وسلسة الفهم.

        ابدأ بكتابة المقال الآن:
        """
    return call_ollama(prompt)


def extend_article_stream(current_article):

    prompt = f"""استمر في كتابة المقال التالي بشكل طبيعي ومتسق:

{current_article}

الاستمرار:"""

    return call_ollama_stream(prompt)


def extend_article(current_article):

    prompt = f"""استمر في كتابة المقال التالي بشكل طبيعي ومتسق:

{current_article}

الاستمرار:"""

    return call_ollama(prompt)


# ==========================================
#  دالة الشات بوت (Streaming)
# ==========================================

def chat_stream(message):

    prompt = f"""أنت مساعد ذكي ومفيد تتحدث اللغة العربية بطلاقة.
أجب على سؤال المستخدم بشكل دقيق ومختصر.

السؤال: {message}
الإجابة:"""

    return call_ollama_stream(prompt)

# ==========================================
#  دوال الصور والصوت
# ==========================================
model_whisper = whisper.load_model("base") #

def transcribe_audio(audio_file_path):

    try:

        result = model_whisper.transcribe(audio_file_path, language='ar') #
        return result.get('text', '').strip() #
    except Exception as e:
        print(f"خطأ أثناء تفريغ الصوت: {e}") #
        return f"فشل التفريغ: {str(e)}" #

def generate_image_prompt(article_text):

    system_instruction = (
        "As a professional editorial photographer, create a conceptual and highly detailed "
        "English image prompt that captures the core essence of the following article. "
        "The image should be symbolic, artistic, and photorealistic. "
        "Style: Cinematic lighting, 8k resolution, professional composition. "
        "Output ONLY the English prompt."
    )

    full_prompt = f"{system_instruction}\n\nArticle excerpt: {article_text[:600]}"
    r = requests.post(OLLAMA_URL, json={"model": OLLAMA_MODEL, "prompt": full_prompt, "stream": False})

    if r.status_code == 200:
        generated_desc = r.json().get('response', '').strip()

        return f"{generated_desc}, highly detailed, masterpiece, sharp focus, stunning visual composition"
    return "A professional editorial background related to the topic"
def generate_image_with_sd3(prompt_text):

    try:
        url = "https://api.stability.ai/v2beta/stable-image/generate/sd3"

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "accept": "image/*"
        }


        files = {
            "prompt": (None, prompt_text),
            "output_format": (None, "png"),
            "model": (None, "sd3"),
            "aspect_ratio": (None, "16:9")
        }

        response = requests.post(url, headers=headers, files=files)

        if response.status_code == 200:

            image_base64 = base64.b64encode(response.content).decode('utf-8')
            return image_base64
        else:
            print(f"Error from Stability API: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"Exception during image generation: {e}")
        return None

