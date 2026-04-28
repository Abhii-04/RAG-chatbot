const form = document.getElementById("chat-form");
const input = document.getElementById("question");
const messages = document.getElementById("messages");
const submitButton = form.querySelector("button");

const appendMessage = (role, text, extraClass = "") => {
  const article = document.createElement("article");
  article.className = `message ${role}${extraClass ? ` ${extraClass}` : ""}`;

  const paragraph = document.createElement("p");
  paragraph.textContent = text;
  article.appendChild(paragraph);

  messages.appendChild(article);
  messages.scrollTop = messages.scrollHeight;
  return article;
};

const resizeInput = () => {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 180)}px`;
};

input.addEventListener("input", resizeInput);

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const question = input.value.trim();
  if (!question) {
    return;
  }

  appendMessage("user", question);
  input.value = "";
  resizeInput();
  input.focus();

  submitButton.disabled = true;
  const loadingMessage = appendMessage("bot", "Thinking...", "loading");

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question }),
    });

    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }

    const data = await response.json();
    loadingMessage.remove();
    appendMessage("bot", data.answer || "No response received.");
  } catch (error) {
    loadingMessage.remove();
    appendMessage("bot", "Backend unavailable. Start the Flask server on port 8000.");
  } finally {
    submitButton.disabled = false;
  }
});

resizeInput();
