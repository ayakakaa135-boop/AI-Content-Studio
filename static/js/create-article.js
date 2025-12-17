async function writeArticle() {
    const titleInput = document.getElementById('articleTitle');
    const title = titleInput ? titleInput.value : '';

    if (!title.trim()) {
        alert('الرجاء إدخال عنوان للمقال أولاً');
        return;
    }

    // تهيئة العناصر والتأكد من وجودها
    const maqalDiv = document.getElementById('maqal');
    const keywordsText = document.getElementById('keywords');
    const progress = document.getElementById('progress-container');
    const btnSpinner = document.getElementById('write-btn-spinner');
    const btnText = document.getElementById('write-btn-text');

    if (maqalDiv) maqalDiv.innerHTML = '';
    if (keywordsText) keywordsText.value = '';
    if (progress) progress.style.display = 'block';
    if (btnSpinner) btnSpinner.style.display = 'inline-block';
    if (btnText) btnText.textContent = 'جاري الكتابة...';

    let fullMarkdownText = '';

    try {
        const response = await fetch('/api/write-article-stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: title })
        });

        if (!response.ok) throw new Error(`Server Error: ${response.status}`);

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const jsonStr = line.substring(6).trim();
                        if (!jsonStr) continue;

                        const data = JSON.parse(jsonStr);

                        if (data.chunk && maqalDiv) {
                            fullMarkdownText += data.chunk;
                            // التأكد من أن مكتبة marked محملة
                            if (typeof marked !== 'undefined') {
                                maqalDiv.innerHTML = marked.parse(fullMarkdownText);
                            } else {
                                maqalDiv.innerText = fullMarkdownText;
                            }
                            updateWordCount(fullMarkdownText);
                        }

                        if (data.done && data.keywords && keywordsText) {
                            keywordsText.value = data.keywords;
                        }
                    } catch (e) {
                        console.warn("خطأ بسيط في تحليل جزء من البيانات:", e);
                    }
                }
            }
        }
    } catch (error) {
        console.error('Connection Error:', error);
        alert('فشل الاتصال بالخادم. تأكد من تشغيل تطبيق البايثون (Flask).');
    } finally {
        if (progress) progress.style.display = 'none';
        if (btnSpinner) btnSpinner.style.display = 'none';
        if (btnText) btnText.textContent = 'اكتب المقال المنسق';
    }
}

async function generateImage() {
    const maqalDiv = document.getElementById('maqal');
    if (!maqalDiv) return;

    const articleText = maqalDiv.innerText;

    if (!articleText.trim() || articleText.length < 10) {
        alert('يجب كتابة المقال أولاً');
        return;
    }

    const button = document.getElementById('drawButton');
    const outputImage = document.getElementById('outputImage');
    if (!button || !outputImage) return;

    const originalText = button.innerText;
    button.innerText = 'جاري الرسم...';
    button.disabled = true;

    try {
        const response = await fetch('/api/generate-full-image', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ article: articleText })
        });

        const data = await response.json();

        if (data.success) {
            outputImage.src = data.image_data;
            outputImage.style.display = 'block';
        } else {
            alert('فشل توليد الصورة: ' + (data.error || 'خطأ غير معروف'));
        }
    } catch (error) {
        alert('خطأ في الاتصال أثناء توليد الصورة');
    } finally {
        button.innerText = originalText;
        button.disabled = false;
    }
}

function updateWordCount(text) {
    const wordCountEl = document.getElementById('word-count');
    if (wordCountEl) {
        const count = text.trim() ? text.trim().split(/\s+/).length : 0;
        wordCountEl.textContent = count + ' كلمة';
    }
}