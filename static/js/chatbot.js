async function sendMessage() {
    const input = document.getElementById('humanInput');
    const message = input.value.trim();

    if (!message) return;

    // 1. إضافة رسالة المستخدم
    addMessage(message, 'humanMessage');
    input.value = '';

    const button = document.getElementById('sendButton');
    button.disabled = true;

    const messageList = document.getElementById('messageList');

    // 2. إنشاء فقاعة البوت مع تأثير "جاري التفكير" (النقاط المتحركة)
    const botMessageDiv = document.createElement('div');
    botMessageDiv.className = 'botMessage typing-animation';
    botMessageDiv.innerHTML = '<span class="dot">.</span><span class="dot">.</span><span class="dot">.</span>';
    messageList.appendChild(botMessageDiv);

    // التمرير للأسفل
    messageList.scrollTop = messageList.scrollHeight;

    try {
        const response = await fetch('/api/chatbot-stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        });

        if (!response.ok) throw new Error('Network response was not ok');

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let botFullResponse = '';
        let isFirstChunk = true;

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
                            // إزالة تأثير النقاط عند وصول أول كلمة من الرد
                            if (isFirstChunk) {
                                botMessageDiv.innerHTML = '';
                                botMessageDiv.classList.remove('typing-animation');
                                isFirstChunk = false;
                            }
                            botFullResponse += data.chunk;
                            botMessageDiv.textContent = botFullResponse;
                            messageList.scrollTop = messageList.scrollHeight;
                        }
                    } catch (e) {
                        console.error('JSON Parse Error', e);
                    }
                }
            }
        }
    } catch (error) {
        console.error('Error:', error);
        botMessageDiv.innerHTML = '<span style="color: red;">عذراً، حدث خطأ في الاتصال.</span>';
    } finally {
        button.disabled = false;
        input.focus();
    }
}

// دالة إضافة الرسالة (يجب أن تكون خارج sendMessage)
function addMessage(text, className) {
    const messageList = document.getElementById('messageList');
    const messageDiv = document.createElement('div');
    messageDiv.className = className;
    messageDiv.textContent = text;
    messageList.appendChild(messageDiv);
    messageList.scrollTop = messageList.scrollHeight;
}

// تشغيل عند الضغط على Enter
document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('humanInput');
    if (input) {
        input.addEventListener('keypress', function(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        });
    }
});