document.addEventListener("DOMContentLoaded", function() {
    // Smooth scroll to login section when clicking scroll down
    const scrollDown = document.querySelector(".scroll-down");
    if (scrollDown) {
        scrollDown.addEventListener("click", function() {
            document.getElementById("login").scrollIntoView({ 
                behavior: "smooth" 
            });
        });
    }

    // Handle scroll events for section transitions
    let isScrolling;
    window.addEventListener('scroll', function() {
        window.clearTimeout(isScrolling);
        
        isScrolling = setTimeout(function() {
            const introSection = document.getElementById('intro');
            const loginSection = document.getElementById('login');
            const scrollPosition = window.scrollY;
            const windowHeight = window.innerHeight;

            // Add/remove active class based on scroll position
            if (scrollPosition < windowHeight * 0.5) {
                introSection.classList.add('active');
                loginSection.classList.remove('active');
            } else {
                introSection.classList.remove('active');
                loginSection.classList.add('active');
            }
        }, 100);
    });

    // Initialize scroll position
    window.dispatchEvent(new Event('scroll'));

    // Function to handle API call with streaming response
    async function callMistralAPI(prompt) {
        const responseContainer = document.getElementById('chat-content');
        
        // Add user message to chat
        responseContainer.innerHTML += `<div class="user-message">${prompt}</div>`;
        
        // Create AI message container with typing indicator
        const aiMessageId = "ai-message-" + Date.now();
        responseContainer.innerHTML += `
            <div id="${aiMessageId}" class="ai-message">
                <span class="typing-content"></span>
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        responseContainer.scrollTop = responseContainer.scrollHeight;
        
        // Set up event source for streaming
        const eventSource = new EventSource(`/api/mistral?prompt=${encodeURIComponent(prompt)}`);
        let responseText = '';
        
        eventSource.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                
                if (data.error) {
                    document.getElementById(aiMessageId).innerHTML = `<div class="error">Error: ${data.error}</div>`;
                    eventSource.close();
                    return;
                }
                
                if (data.type === 'done') {
                    // Remove typing indicator when done
                    const typingIndicator = document.querySelector(`#${aiMessageId} .typing-indicator`);
                    if (typingIndicator) {
                        typingIndicator.remove();
                    }
                    eventSource.close();
                    return;
                }
                
                if (data.token) {
                    responseText += data.token;
                    // Update the content with the new text
                    document.querySelector(`#${aiMessageId} .typing-content`).innerHTML = formatResponse(responseText);
                    responseContainer.scrollTop = responseContainer.scrollHeight;
                }
            } catch (e) {
                console.error('Error parsing SSE data:', e);
            }
        };
        
        eventSource.onerror = function(error) {
            console.error('SSE Error:', error);
            document.getElementById(aiMessageId).innerHTML = `<div class="error">Error: Connection failed. Please try again.</div>`;
            eventSource.close();
        };
    }
    
    // Helper function to format response text
    function formatResponse(text) {
        // Convert markdown to HTML if needed
        return text.replace(/\n/g, '<br>');
    }

    // Event listener for the send button
    const sendButton = document.getElementById('send-btn');
    if (sendButton) {
        sendButton.addEventListener('click', function() {
            const userInput = document.getElementById('user-query').value;
            if (userInput.trim()) {
                callMistralAPI(userInput);
                document.getElementById('user-query').value = ''; // Clear input field
            }
        });
    }
    
    // Handle Enter key press in the input field
    const userInput = document.getElementById('user-query');
    if (userInput) {
        userInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                const userInput = this.value.trim();
                if (userInput) {
                    callMistralAPI(userInput);
                    this.value = ''; // Clear input field
                }
            }
        });
    }
    
    // Add CSS for typing effect
    const style = document.createElement('style');
    style.textContent = `
        .typing-content {
            white-space: pre-wrap;
            word-break: break-word;
        }
        
        .typing-indicator {
            display: inline-flex;
            margin-left: 4px;
        }
        
        .typing-indicator span {
            height: 8px;
            width: 8px;
            background-color: #888;
            border-radius: 50%;
            display: inline-block;
            margin: 0 2px;
            animation: bounce 1.5s infinite ease-in-out;
        }
        
        .typing-indicator span:nth-child(2) {
            animation-delay: 0.2s;
        }
        
        .typing-indicator span:nth-child(3) {
            animation-delay: 0.4s;
        }
        
        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-5px); }
        }
    `;
    document.head.appendChild(style);
});