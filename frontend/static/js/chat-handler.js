class ChatHandler {
    constructor(options = {}) {
      console.log("ChatHandler initialized");
      
      // Store selectors
      this.messageContainerSelector = options.messageContainer || '#chat-content';
      this.userInputFieldSelector = options.userInputField || '#user-query';
      this.sendButtonSelector = options.sendButton || '#send-btn';
      this.typingIndicatorSelector = options.typingIndicator || '#loading-indicator';
      this.apiEndpoint = options.apiEndpoint || '/api/query';
      
      // Try to find elements
      this.messageContainer = document.querySelector(this.messageContainerSelector);
      this.userInputField = document.querySelector(this.userInputFieldSelector);
      this.sendButton = document.querySelector(this.sendButtonSelector);
      this.typingIndicator = document.querySelector(this.typingIndicatorSelector);
      
      // Log which elements were found
      console.log("Elements found:", {
        messageContainer: Boolean(this.messageContainer),
        userInputField: Boolean(this.userInputField),
        sendButton: Boolean(this.sendButton),
        typingIndicator: Boolean(this.typingIndicator)
      });
      
      this.messageHistory = [];
      this.isStreaming = false;
      
      this.init();
    }
    
    init() {
      if (this.sendButton) {
        this.sendButton.addEventListener('click', () => {
          this.sendMessage();
        });
      }
      
      if (this.userInputField) {
        this.userInputField.addEventListener('keypress', (e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.sendMessage();
          }
        });
      }
    }
    
    addUserMessage(content) {
      if (!this.messageContainer) return;
      
      const messageElement = document.createElement('div');
      messageElement.className = 'user-message';
      messageElement.innerHTML = `<p>${this.escapeHTML(content)}</p>`;
      this.messageContainer.appendChild(messageElement);
      this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
      
      this.messageHistory.push({ role: 'user', content });
    }
    
    createAssistantMessageContainer() {
      if (!this.messageContainer) return null;
      
      const messageElement = document.createElement('div');
      messageElement.className = 'assistant-message';
      messageElement.innerHTML = '<p></p>';
      this.messageContainer.appendChild(messageElement);
      return messageElement.querySelector('p');
    }
    
    updateAssistantMessage(element, content) {
      if (!element) return;
      
      element.innerHTML = this.formatMessage(content);
      if (this.messageContainer) {
        this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
      }
    }
    
    formatMessage(text) {
      let formatted = this.escapeHTML(text);
      formatted = formatted.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
      formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
      formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
      formatted = formatted.replace(/\*([^*]+)\*/g, '<em>$1</em>');
      formatted = formatted.replace(/\n/g, '<br>');
      return formatted;
    }
    
    escapeHTML(text) {
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    }
    
    async sendMessage() {
      if (!this.userInputField) return;
      
      const userInput = this.userInputField.value.trim();
      if (userInput === '' || this.isStreaming) return;
      
      this.userInputField.value = '';
      this.addUserMessage(userInput);
      
      // Handle typing indicator safely
      if (this.typingIndicator) {
        this.typingIndicator.style.display = 'block';
      }
      
      // Create assistant message container
      const assistantMessageElement = this.createAssistantMessageContainer();
      if (!assistantMessageElement) {
        console.error("Could not create assistant message container");
        return;
      }
      
      try {
        this.isStreaming = true;
        
        const requestData = {
          messages: [...this.messageHistory],
          stream: true
        };
        
        console.log("Sending request to API:", requestData);
        
        const response = await fetch(this.apiEndpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let assistantResponse = '';
        
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          const chunk = decoder.decode(value, { stream: true });
          console.log("Received chunk:", chunk);
          
          const processedChunk = this.processChunk(chunk);
          
          assistantResponse += processedChunk;
          this.updateAssistantMessage(assistantMessageElement, assistantResponse);
        }
        
        this.messageHistory.push({ role: 'assistant', content: assistantResponse });
        
      } catch (error) {
        console.error('Error:', error);
        this.updateAssistantMessage(assistantMessageElement, 'Sorry, an error occurred while processing your request.');
      } finally {
        this.isStreaming = false;
        
        // Handle typing indicator safely
        if (this.typingIndicator) {
          this.typingIndicator.style.display = 'none';
        }
      }
    }
    
    processChunk(chunk) {
      try {
        return chunk.split('\n')
          .filter(line => line.trim() !== '')
          .map(line => {
            const jsonStr = line.startsWith('data: ') ? line.slice(6) : line;
            try {
              const data = JSON.parse(jsonStr);
              return data.content || data.chunk || data.text || '';
            } catch (e) {
              return jsonStr;
            }
          })
          .join('');
      } catch (e) {
        return chunk;
      }
    }
  }
  
  // Expose the ChatHandler globally for debugging
  window.ChatHandler = ChatHandler;
  
  // Initialize when DOM is ready
  document.addEventListener('DOMContentLoaded', () => {
    try {
      window.chatHandler = new ChatHandler({
        messageContainer: '#chat-content',
        userInputField: '#user-query', 
        sendButton: '#send-btn',
        typingIndicator: '#loading-indicator',
        apiEndpoint: '/api/query'
      });
      
      console.log("ChatHandler initialized successfully");
    } catch (e) {
      console.error("Error initializing ChatHandler:", e);
    }
  });class ChatHandler {
    constructor(options = {}) {
      console.log("ChatHandler initialized");
      
      // Store selectors
      this.messageContainerSelector = options.messageContainer || '#chat-content';
      this.userInputFieldSelector = options.userInputField || '#user-query';
      this.sendButtonSelector = options.sendButton || '#send-btn';
      this.typingIndicatorSelector = options.typingIndicator || '#loading-indicator';
      this.apiEndpoint = options.apiEndpoint || '/api/query';
      
      // Try to find elements
      this.messageContainer = document.querySelector(this.messageContainerSelector);
      this.userInputField = document.querySelector(this.userInputFieldSelector);
      this.sendButton = document.querySelector(this.sendButtonSelector);
      this.typingIndicator = document.querySelector(this.typingIndicatorSelector);
      
      // Log which elements were found
      console.log("Elements found:", {
        messageContainer: Boolean(this.messageContainer),
        userInputField: Boolean(this.userInputField),
        sendButton: Boolean(this.sendButton),
        typingIndicator: Boolean(this.typingIndicator)
      });
      
      this.messageHistory = [];
      this.isStreaming = false;
      
      this.init();
    }
    
    init() {
      if (this.sendButton) {
        this.sendButton.addEventListener('click', () => {
          this.sendMessage();
        });
      }
      
      if (this.userInputField) {
        this.userInputField.addEventListener('keypress', (e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.sendMessage();
          }
        });
      }
    }
    
    addUserMessage(content) {
      if (!this.messageContainer) return;
      
      const messageElement = document.createElement('div');
      messageElement.className = 'user-message';
      messageElement.innerHTML = `<p>${this.escapeHTML(content)}</p>`;
      this.messageContainer.appendChild(messageElement);
      this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
      
      this.messageHistory.push({ role: 'user', content });
    }
    
    createAssistantMessageContainer() {
      if (!this.messageContainer) return null;
      
      const messageElement = document.createElement('div');
      messageElement.className = 'assistant-message';
      messageElement.innerHTML = '<p></p>';
      this.messageContainer.appendChild(messageElement);
      return messageElement.querySelector('p');
    }
    
    updateAssistantMessage(element, content) {
      if (!element) return;
      
      element.innerHTML = this.formatMessage(content);
      if (this.messageContainer) {
        this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
      }
    }
    
    formatMessage(text) {
      let formatted = this.escapeHTML(text);
      formatted = formatted.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
      formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
      formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
      formatted = formatted.replace(/\*([^*]+)\*/g, '<em>$1</em>');
      formatted = formatted.replace(/\n/g, '<br>');
      return formatted;
    }
    
    escapeHTML(text) {
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    }
    
    async sendMessage() {
      if (!this.userInputField) return;
      
      const userInput = this.userInputField.value.trim();
      if (userInput === '' || this.isStreaming) return;
      
      this.userInputField.value = '';
      this.addUserMessage(userInput);
      
      // Handle typing indicator safely
      if (this.typingIndicator) {
        this.typingIndicator.style.display = 'block';
      }
      
      // Create assistant message container
      const assistantMessageElement = this.createAssistantMessageContainer();
      if (!assistantMessageElement) {
        console.error("Could not create assistant message container");
        return;
      }
      
      try {
        this.isStreaming = true;
        
        const requestData = {
          messages: [...this.messageHistory],
          stream: true
        };
        
        console.log("Sending request to API:", requestData);
        
        const response = await fetch(this.apiEndpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let assistantResponse = '';
        
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          const chunk = decoder.decode(value, { stream: true });
          console.log("Received chunk:", chunk);
          
          const processedChunk = this.processChunk(chunk);
          
          assistantResponse += processedChunk;
          this.updateAssistantMessage(assistantMessageElement, assistantResponse);
        }
        
        this.messageHistory.push({ role: 'assistant', content: assistantResponse });
        
      } catch (error) {
        console.error('Error:', error);
        this.updateAssistantMessage(assistantMessageElement, 'Sorry, an error occurred while processing your request.');
      } finally {
        this.isStreaming = false;
        
        // Handle typing indicator safely
        if (this.typingIndicator) {
          this.typingIndicator.style.display = 'none';
        }
      }
    }
    
    processChunk(chunk) {
      try {
        return chunk.split('\n')
          .filter(line => line.trim() !== '')
          .map(line => {
            const jsonStr = line.startsWith('data: ') ? line.slice(6) : line;
            try {
              const data = JSON.parse(jsonStr);
              return data.content || data.chunk || data.text || '';
            } catch (e) {
              return jsonStr;
            }
          })
          .join('');
      } catch (e) {
        return chunk;
      }
    }
    
    async handleTypingIndicator() {
      if (this.typingIndicator) {
        this.typingIndicator.style.display = 'block';
        await new Promise(resolve => setTimeout(resolve, 3000));
        this.typingIndicator.style.display = 'none';
      }
    }
    
    async handleAssistantResponse(response) {
      const assistantMessageElement = this.createAssistantMessageContainer();
      if (!assistantMessageElement) {
        console.error("Could not create assistant message container");
        return;
      }
      
      this.updateAssistantMessage(assistantMessageElement, response);
    }
  }
  
  // Expose the ChatHandler globally for debugging
  window.ChatHandler = ChatHandler;
  
  // Initialize when DOM is ready
  document.addEventListener('DOMContentLoaded', () => {
    try {
      window.chatHandler = new ChatHandler({
        messageContainer: '#chat-content',
        userInputField: '#user-query', 
        sendButton: '#send-btn',
        typingIndicator: '#loading-indicator',
        apiEndpoint: '/api/query'
      });
      
      console.log("ChatHandler initialized successfully");
    } catch (e) {
      console.error("Error initializing ChatHandler:", e);
    }
  });class ChatHandler {
    constructor(options = {}) {
      console.log("ChatHandler initialized");
      
      // Store selectors
      this.messageContainerSelector = options.messageContainer || '#chat-content';
      this.userInputFieldSelector = options.userInputField || '#user-query';
      this.sendButtonSelector = options.sendButton || '#send-btn';
      this.typingIndicatorSelector = options.typingIndicator || '#loading-indicator';
      this.apiEndpoint = options.apiEndpoint || '/api/query';
      
      // Try to find elements
      this.messageContainer = document.querySelector(this.messageContainerSelector);
      this.userInputField = document.querySelector(this.userInputFieldSelector);
      this.sendButton = document.querySelector(this.sendButtonSelector);
      this.typingIndicator = document.querySelector(this.typingIndicatorSelector);
      
      // Log which elements were found
      console.log("Elements found:", {
        messageContainer: Boolean(this.messageContainer),
        userInputField: Boolean(this.userInputField),
        sendButton: Boolean(this.sendButton),
        typingIndicator: Boolean(this.typingIndicator)
      });
      
      this.messageHistory = [];
      this.isStreaming = false;
      
      this.init();
    }
    
    init() {
      if (this.sendButton) {
        this.sendButton.addEventListener('click', () => {
          this.sendMessage();
        });
      }
      
      if (this.userInputField) {
        this.userInputField.addEventListener('keypress', (e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.sendMessage();
          }
        });
      }
    }
    
    addUserMessage(content) {
      if (!this.messageContainer) return;
      
      const messageElement = document.createElement('div');
      messageElement.className = 'user-message';
      messageElement.innerHTML = `<p>${this.escapeHTML(content)}</p>`;
      this.messageContainer.appendChild(messageElement);
      this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
      
      this.messageHistory.push({ role: 'user', content });
    }
    
    createAssistantMessageContainer() {
      if (!this.messageContainer) return null;
      
      const messageElement = document.createElement('div');
      messageElement.className = 'assistant-message';
      messageElement.innerHTML = '<p></p>';
      this.messageContainer.appendChild(messageElement);
      return messageElement.querySelector('p');
    }
    
    updateAssistantMessage(element, content) {
      if (!element) return;
      
      element.innerHTML = this.formatMessage(content);
      if (this.messageContainer) {
        this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
      }
    }
    
    formatMessage(text) {
      let formatted = this.escapeHTML(text);
      formatted = formatted.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
      formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
      formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
      formatted = formatted.replace(/\*([^*]+)\*/g, '<em>$1</em>');
      formatted = formatted.replace(/\n/g, '<br>');
      return formatted;
    }
    
    escapeHTML(text) {
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    }
    
    async sendMessage() {
      if (!this.userInputField) return;
      
      const userInput = this.userInputField.value.trim();
      if (userInput === '' || this.isStreaming) return;
      
      this.userInputField.value = '';
      this.addUserMessage(userInput);
      
      // Handle typing indicator safely
      if (this.typingIndicator) {
        this.typingIndicator.style.display = 'block';
      }
      
      // Create assistant message container
      const assistantMessageElement = this.createAssistantMessageContainer();
      if (!assistantMessageElement) {
        console.error("Could not create assistant message container");
        return;
      }
      
      try {
        this.isStreaming = true;
        
        const requestData = {
          messages: [...this.messageHistory],
          stream: true
        };
        
        console.log("Sending request to API:", requestData);
        
        const response = await fetch(this.apiEndpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let assistantResponse = '';
        
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          const chunk = decoder.decode(value, { stream: true });
          console.log("Received chunk:", chunk);
          
          const processedChunk = this.processChunk(chunk);
          
          assistantResponse += processedChunk;
          this.updateAssistantMessage(assistantMessageElement, assistantResponse);
        }
        
        this.messageHistory.push({ role: 'assistant', content: assistantResponse });
        
      } catch (error) {
        console.error('Error:', error);
        this.updateAssistantMessage(assistantMessageElement, 'Sorry, an error occurred while processing your request.');
      } finally {
        this.isStreaming = false;
        
        // Handle typing indicator safely
        if (this.typingIndicator) {
          this.typingIndicator.style.display = 'none';
        }
      }
    }
    
    processChunk(chunk) {
      try {
        return chunk.split('\n')
          .filter(line => line.trim() !== '')
          .map(line => {
            const jsonStr = line.startsWith('data: ') ? line.slice(6) : line;
            try {
              const data = JSON.parse(jsonStr);
              return data.content || data.chunk || data.text || '';
            } catch (e) {
              return jsonStr;
            }
          })
          .join('');
      } catch (e) {
        return chunk;
      }
    }
    
    async handleTypingIndicator() {
      if (this.typingIndicator) {
        this.typingIndicator.style.display = 'block';
        await new Promise(resolve => setTimeout(resolve, 3000));
        this.typingIndicator.style.display = 'none';
      }
    }
    
    async handleAssistantResponse(response) {
      const assistantMessageElement = this.createAssistantMessageContainer();
      if (!assistantMessageElement) {
        console.error("Could not create assistant message container");
        return;
      }
      
      this.updateAssistantMessage(assistantMessageElement, response);
    }
    
    async sendFile(file) {
      if (!this.userInputField) return;
      
      const fileInput = new FormData();
      fileInput.append('file', file);
      
      try {
        const response = await fetch(this.apiEndpoint, {
          method: 'POST',
          body: fileInput
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        this.messageHistory.push({ role: 'assistant', content: data.content });
        
        const assistantMessageElement = this.createAssistantMessageContainer();
        if (!assistantMessageElement) {
          console.error("Could not create assistant message container");
          return;
        }
        
        this.updateAssistantMessage(assistantMessageElement, data.content);
        
      } catch (error) {
        console.error('Error:', error);
        this.updateAssistantMessage(assistantMessageElement, 'Sorry, an error occurred while processing your request.');
      }
    }
  }
  
  // Expose the ChatHandler globally for debugging
  window.ChatHandler = ChatHandler;
  
  // Initialize when DOM is ready
  document.addEventListener('DOMContentLoaded', () => {
    try {
      window.chatHandler = new ChatHandler({
        messageContainer: '#chat-content',
        userInputField: '#user-query', 
        sendButton: '#send-btn',
        typingIndicator: '#loading-indicator',
        apiEndpoint: '/api/query'
      });
      
      console.log("ChatHandler initialized successfully");
    } catch (e) {
      console.error("Error initializing ChatHandler:", e);
    }
  });class ChatHandler {
    constructor(options = {}) {
      console.log("ChatHandler initialized");
      
      // Store selectors
      this.messageContainerSelector = options.messageContainer || '#chat-content';
      this.userInputFieldSelector = options.userInputField || '#user-query';
      this.sendButtonSelector = options.sendButton || '#send-btn';
      this.typingIndicatorSelector = options.typingIndicator || '#loading-indicator';
      this.apiEndpoint = options.apiEndpoint || '/api/query';
      this.fileInputSelector = options.fileInput || '#file-input';
      
      // Try to find elements
      this.messageContainer = document.querySelector(this.messageContainerSelector);
      this.userInputField = document.querySelector(this.userInputFieldSelector);
      this.sendButton = document.querySelector(this.sendButtonSelector);
      this.typingIndicator = document.querySelector(this.typingIndicatorSelector);
      this.fileInput = document.querySelector(this.fileInputSelector);
      
      // Log which elements were found
      console.log("Elements found:", {
        messageContainer: Boolean(this.messageContainer),
        userInputField: Boolean(this.userInputField),
        sendButton: Boolean(this.sendButton),
        typingIndicator: Boolean(this.typingIndicator),
        fileInput: Boolean(this.fileInput)
      });
      
      this.messageHistory = [];
      this.isStreaming = false;
      
      this.init();
    }
    
    init() {
      if (this.sendButton) {
        this.sendButton.addEventListener('click', () => {
          this.sendMessage();
        });
      }
      
      if (this.userInputField) {
        this.userInputField.addEventListener('keypress', (e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.sendMessage();
          }
        });
      }
      
      if (this.fileInput) {
        this.fileInput.addEventListener('change', (e) => {
          this.sendFile(e.target.files[0]);
        });
      }
    }
    
    addUserMessage(content) {
      if (!this.messageContainer) return;
      
      const messageElement = document.createElement('div');
      messageElement.className = 'user-message';
      messageElement.innerHTML = `<p>${this.escapeHTML(content)}</p>`;
      this.messageContainer.appendChild(messageElement);
      this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
      
      this.messageHistory.push({ role: 'user', content });
    }
    
    createAssistantMessageContainer() {
      if (!this.messageContainer) return null;
      
      const messageElement = document.createElement('div');
      messageElement.className = 'assistant-message';
      messageElement.innerHTML = '<p></p>';
      this.messageContainer.appendChild(messageElement);
      return messageElement.querySelector('p');
    }
    
    updateAssistantMessage(element, content) {
      if (!element) return;
      
      element.innerHTML = this.formatMessage(content);
      if (this.messageContainer) {
        this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
      }
    }
    
    formatMessage(text) {
      let formatted = this.escapeHTML(text);
      formatted = formatted.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
      formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
      formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
      formatted = formatted.replace(/\*([^*]+)\*/g, '<em>$1</em>');
      formatted = formatted.replace(/\n/g, '<br>');
      return formatted;
    }
    
    escapeHTML(text) {
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    }
    
    async sendMessage() {
      if (!this.userInputField) return;
      
      const userInput = this.userInputField.value.trim();
      if (userInput === '' || this.isStreaming) return;
      
      this.userInputField.value = '';
      this.addUserMessage(userInput);
      
      // Handle typing indicator safely
      if (this.typingIndicator) {
        this.typingIndicator.style.display = 'block';
      }
      
      // Create assistant message container
      const assistantMessageElement = this.createAssistantMessageContainer();
      if (!assistantMessageElement) {
        console.error("Could not create assistant message container");
        return;
      }
      
      try {
        this.isStreaming = true;
        
        const requestData = {
          messages: [...this.messageHistory],
          stream: true
        };
        
        console.log("Sending request to API:", requestData);
        
        const response = await fetch(this.apiEndpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let assistantResponse = '';
        
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          const chunk = decoder.decode(value, { stream: true });
          console.log("Received chunk:", chunk);
          
          const processedChunk = this.processChunk(chunk);
          
          assistantResponse += processedChunk;
          this.updateAssistantMessage(assistantMessageElement, assistantResponse);
        }
        
        this.messageHistory.push({ role: 'assistant', content: assistantResponse });
        
      } catch (error) {
        console.error('Error:', error);
        this.updateAssistantMessage(assistantMessageElement, 'Sorry, an error occurred while processing your request.');
      } finally {
        this.isStreaming = false;
        
        // Handle typing indicator safely
        if (this.typingIndicator) {
          this.typingIndicator.style.display = 'none';
        }
      }
    }
    
    processChunk(chunk) {
      try {
        return chunk.split('\n')
          .filter(line => line.trim() !== '')
          .map(line => {
            const jsonStr = line.startsWith('data: ') ? line.slice(6) : line;
            try {
              const data = JSON.parse(jsonStr);
              return data.content || data.chunk || data.text || '';
            } catch (e) {
              return jsonStr;
            }
          })
          .join('');
      } catch (e) {
        return chunk;
      }
    }
    
    async handleTypingIndicator() {
      if (this.typingIndicator) {
        this.typingIndicator.style.display = 'block';
        await new Promise(resolve => setTimeout(resolve, 3000));
        this.typingIndicator.style.display = 'none';
      }
    }
    
    async handleAssistantResponse(response) {
      const assistantMessageElement = this.createAssistantMessageContainer();
      if (!assistantMessageElement) {
        console.error("Could not create assistant message container");
        return;
      }
      
      this.updateAssistantMessage(assistantMessageElement, response);
    }
    
    async sendFile(file) {
      if (!this.userInputField) return;
      
      const fileInput = new FormData();
      fileInput.append('file', file);
      
      try {
        const response = await fetch(this.apiEndpoint, {
          method: 'POST',
          body: fileInput
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        this.messageHistory.push({ role: 'assistant', content: data.content });
        
        const assistantMessageElement = this.createAssistantMessageContainer();
        if (!assistantMessageElement) {
          console.error("Could not create assistant message container");
          return;
        }
        
        this.updateAssistantMessage(assistantMessageElement, data.content);
        
      } catch (error) {
        console.error('Error:', error);
        this.updateAssistantMessage(assistantMessageElement, 'Sorry, an error occurred while processing your request.');
      }
    }
  }
  
  // Expose the ChatHandler globally for debugging
  window.ChatHandler = ChatHandler;
  
  // Initialize when DOM is ready
  document.addEventListener('DOMContentLoaded', () => {
    try {
      window.chatHandler = new ChatHandler({
        messageContainer: '#chat-content',
        userInputField: '#user-query', 
        sendButton: '#send-btn',
        typingIndicator: '#loading-indicator',
        apiEndpoint: '/api/query',
        fileInput: '#file-input'
      });
      
      console.log("ChatHandler initialized successfully");
    } catch (e) {
      console.error("Error initializing ChatHandler:", e);
    }
  });