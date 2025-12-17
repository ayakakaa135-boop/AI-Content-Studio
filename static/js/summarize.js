async function summarizeArticle() {
    const articleText = document.getElementById('toSummarize').value;
    const outputDiv = document.getElementById('maqal');
    const titleInput = document.getElementById('title');
    const keywordsArea = document.getElementById('keywords');

    if (!articleText.trim()) {
        alert('الرجاء إدخال نص المقال');
        return;
    }

    // تهيئة الواجهة
    outputDiv.innerHTML = '<p class="text-muted">جاري معالجة النص وبناء الملخص...</p>';
    if(titleInput) titleInput.value = '';
    if(keywordsArea) keywordsArea.value = '';

    try {
        const response = await fetch('/api/summarize-stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ article: articleText })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullMarkdown = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.substring(6));

                        if (data.chunk) {
                            fullMarkdown += data.chunk;
                            // تحويل Markdown إلى HTML منسق فوراً
                            outputDiv.innerHTML = marked.parse(fullMarkdown);
                            outputDiv.scrollTop = outputDiv.scrollHeight;
                        }

                        if (data.done) {
                            if (data.title) titleInput.value = data.title;
                            if (data.keywords) keywordsArea.value = data.keywords;
                        }
                    } catch (e) { console.error("Error parsing JSON", e); }
                }
            }
        }
    } catch (error) {
        outputDiv.innerHTML = '<span class="text-danger">حدث خطأ أثناء الاتصال بالخادم</span>';
    }
}