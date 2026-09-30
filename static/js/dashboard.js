document.addEventListener("DOMContentLoaded", () => {

    const sendBtn = document.getElementById("sendBtn");
    const input = document.getElementById("userQuestion");
    const chatBox = document.getElementById("chatMessages");

    function scrollBottom() {
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function createMessage(sender, message, type) {

        const div = document.createElement("div");

        div.className = `${type}-message`;

        div.innerHTML = `
            <strong>${sender}</strong><br><br>
            ${message.replace(/\n/g,"<br>")}
        `;

        chatBox.appendChild(div);

        scrollBottom();
    }

    function showTyping() {

        const typing = document.createElement("div");

        typing.className = "bot-message";

        typing.id = "typing";

        typing.innerHTML = `
            <strong>AI Assistant</strong><br><br>
            🤖 Thinking...
        `;

        chatBox.appendChild(typing);

        scrollBottom();
    }

    function removeTyping() {

        const typing = document.getElementById("typing");

        if (typing) {
            typing.remove();
        }

    }

    async function sendMessage() {

        const question = input.value.trim();

        if (question === "")
            return;

        createMessage(
            "You",
            question,
            "user"
        );

        input.value = "";

        input.disabled = true;
        sendBtn.disabled = true;

        showTyping();

        try {

            const response = await fetch("/api/chat", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    message: question
                })

            });
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const data = await response.json();

            removeTyping();

            createMessage(
                "AI Assistant",
                data.reply || "No response received.",
                "bot"
            );

        }

        catch (error) {

            removeTyping();

            createMessage(

                "AI Assistant",

                "❌ Unable to reach the AI service. Please try again.",

                "bot"

            );

            console.error("Chat API Error:", error);

        }

        finally {

            input.disabled = false;

            sendBtn.disabled = false;

            input.focus();

        }

    }

    sendBtn.addEventListener(
        "click",
        sendMessage
    );

    input.addEventListener(
        "keydown",
        function(e){

            if(e.key==="Enter"){

                e.preventDefault();

                sendMessage();

            }

        }
    );

});

