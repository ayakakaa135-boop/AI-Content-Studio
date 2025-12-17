from flask import Flask, render_template, request, jsonify, Response, stream_with_context

from utils import (
    summarize_article,
    summarize_article_stream,
    generate_title,
    generate_keywords,
    write_article,
    write_article_stream,
    extend_article,
    extend_article_stream,
    generate_image_prompt,
    transcribe_audio,
    chat_stream
)
import os
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)



@app.route('/')
def index():
    return render_template('index.html')


@app.route('/create-article')
def create_article():
    return render_template('create-article.html')


@app.route('/summarize-article')
def summarize_article_page():
    return render_template('summarize-article.html')


@app.route('/transcribe')
def transcribe():
    return render_template('transcribe.html')


@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')


# ============== API Endpoints ==============


@app.route('/api/write-article-stream', methods=['POST'])
def api_write_article_stream():
    try:
        data = request.get_json()
        title = data.get('title', '')
        if not title: return jsonify({'error': 'العنوان مطلوب'}), 400

        def generate():
            try:
                full_text = ""
                for chunk in write_article_stream(title):
                    if chunk:
                        full_text += chunk
                        yield f"data: {json.dumps({'chunk': chunk, 'done': False})}\n\n"

                keywords = generate_keywords(full_text)
                yield f"data: {json.dumps({'done': True, 'keywords': keywords})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return Response(stream_with_context(generate()), mimetype='text/event-stream')
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/api/extend-article-stream', methods=['POST'])
def api_extend_article_stream():
    try:
        data = request.get_json()
        current_article = data.get('article', '')
        if not current_article: return jsonify({'error': 'المقال الحالي مطلوب'}), 400

        def generate():
            try:
                for chunk in extend_article_stream(current_article):
                    if chunk:
                        yield f"data: {json.dumps({'chunk': chunk, 'done': False})}\n\n"
                yield f"data: {json.dumps({'done': True})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return Response(stream_with_context(generate()), mimetype='text/event-stream')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/summarize-stream', methods=['POST'])
def api_summarize_stream():
    try:
        data = request.get_json()
        # الجافاسكريبت يرسل النص تحت مفتاح 'article'
        article_text = data.get('article', '')

        if not article_text:
            return jsonify({'error': 'نص المقال مطلوب'}), 400

        def generate():
            try:
                full_summary = ""
                # البدء بالبث
                for chunk in summarize_article_stream(article_text):
                    if chunk:
                        full_summary += chunk
                        # إرسال البيانات بتنسيق JSON داخل SSE
                        yield f"data: {json.dumps({'chunk': chunk})}\n\n"

                # بعد انتهاء التلخيص، نرسل العنوان والكلمات المفتاحية
                g_title = generate_title(full_summary)
                g_keywords = generate_keywords(full_summary)
                yield f"data: {json.dumps({'done': True, 'title': g_title, 'keywords': g_keywords})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return Response(stream_with_context(generate()), mimetype='text/event-stream')
    except Exception as e:
        return jsonify({'error': str(e)}), 500
# ============== ا API الشات بوت مع Streaming ==============
@app.route('/api/chatbot-stream', methods=['POST'])
def api_chatbot():
    try:
        from utils import call_ollama_stream
        data = request.get_json()
        message = data.get('message', '')

        if not message:
            return jsonify({'error': 'الرسالة مطلوبة'}), 400

        def generate():
            try:
                for chunk in call_ollama_stream(message): # استخدام الـ stream
                    if chunk:
                        yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return Response(stream_with_context(generate()), mimetype='text/event-stream')

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate-full-image', methods=['POST'])
def api_generate_full_image():
    try:
        from utils import generate_image_prompt, generate_image_with_sd3  # استدعاء الدالة الجديدة
        data = request.get_json()
        article_text = data.get('article', '')

        if not article_text:
            return jsonify({'error': 'نص المقال فارغ'}), 400

        # 1. توليد الوصف بالإنجليزية من المقال
        image_prompt = generate_image_prompt(article_text)

        # 2. توليد الصورة الفعلية باستخدام SD3
        image_data = generate_image_with_sd3(image_prompt)

        if image_data:
            return jsonify({
                'success': True,
                'image_data': f"data:image/png;base64,{image_data}",
                'prompt': image_prompt
            })
        else:
            return jsonify({'error': 'فشل في توليد الصورة، تأكد من رصيد API والمفتاح'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/transcribe', methods=['POST'])
def api_transcribe():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'لم يتم رفع ملف'}), 400  #

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'لم يتم اختيار ملف'}), 400  #

        if file:
            filename = secure_filename(file.filename)  #
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)  #
            file.save(filepath)  #

            # استدعاء الدالة التي عدلناها في utils.py
            transcription = transcribe_audio(filepath)  #

            # توليد كلمات مفتاحية للنص المفرغ باستخدام Ollama
            keywords = generate_keywords(transcription) if transcription else ""  #

            # حذف الملف بعد الانتهاء لتوفير المساحة
            if os.path.exists(filepath):
                os.remove(filepath)  #

            return jsonify({
                'success': True,
                'transcription': transcription,
                'keywords': keywords
            })  #
    except Exception as e:
        return jsonify({'error': str(e)}), 500  #


if __name__ == '__main__':
    # التأكد من وجود مجلد الرفع قبل البدء
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    print("السيرفر يعمل الآن على: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)