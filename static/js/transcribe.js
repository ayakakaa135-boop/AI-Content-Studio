async function transcribeFunction() {
    // ... كود fetch السابق ...
    const data = await response.json();

    if (data.success) {
        const target = document.getElementById('toSummarize');
        let text = data.transcription;
        let i = 0;
        target.value = ""; // تفريغ المربع للبدء بالتأثير

        // محاكاة البث: كتابة النص حرفاً بحرف
        const typewriter = setInterval(() => {
            if (i < text.length) {
                target.value += text.charAt(i);
                i++;
                target.scrollTop = target.scrollHeight; // التمرير التلقائي لأسفل
            } else {
                clearInterval(typewriter);
                document.getElementById('keywords').value = data.keywords;
            }
        }, 15); // سرعة الكتابة
    }
}