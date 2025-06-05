<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI角色對話系統</title>
    <style>
        :root {
            --bg-primary: #ffffff;
            --bg-secondary: #f8fafc;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --border-color: #e2e8f0;
            --accent-primary: #3b82f6;
            --accent-hover: #2563eb;
            --card-bg: #ffffff;
            --dot-color: rgba(148, 163, 184, 0.15);
            --role1-bg: #eff6ff;
            --role1-border: #3b82f6;
            --role2-bg: #f0fdf4;
            --role2-border: #22c55e;
        }

        [data-theme="dark"] {
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --border-color: #334155;
            --accent-primary: #60a5fa;
            --accent-hover: #3b82f6;
            --card-bg: #1e293b;
            --dot-color: rgba(100, 116, 139, 0.1);
            --role1-bg: #1e3a8a;
            --role1-border: #60a5fa;
            --role2-bg: #14532d;
            --role2-border: #4ade80;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
            position: relative;
            overflow-x: hidden;
        }

        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: radial-gradient(circle, var(--dot-color) 1px, transparent 1px);
            background-size: 30px 30px;
            background-position: 0 0, 15px 15px;
            pointer-events: none;
            z-index: -1;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            display: grid;
            grid-template-columns: 350px 1fr;
            gap: 24px;
            min-height: 100vh;
        }

        .control-panel {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 24px;
            height: fit-content;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        .chat-area {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            display: flex;
            flex-direction: column;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
        }

        h1 {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-primary);
        }

        .theme-toggle {
            background: var(--accent-primary);
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.2s;
        }

        .theme-toggle:hover {
            background: var(--accent-hover);
        }

        .form-group {
            margin-bottom: 20px;
        }

        label {
            display: block;
            margin-bottom: 6px;
            font-weight: 600;
            color: var(--text-primary);
            font-size: 14px;
        }

        input, textarea, select {
            width: 100%;
            padding: 12px;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            background: var(--bg-secondary);
            color: var(--text-primary);
            font-size: 14px;
            transition: border-color 0.2s, box-shadow 0.2s;
        }

        input:focus, textarea:focus, select:focus {
            outline: none;
            border-color: var(--accent-primary);
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }

        textarea {
            resize: vertical;
            min-height: 80px;
        }

        .settings-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }

        .start-btn {
            width: 100%;
            background: var(--accent-primary);
            color: white;
            border: none;
            padding: 14px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            font-size: 16px;
            transition: background-color 0.2s, transform 0.1s;
            margin-top: 20px;
        }

        .start-btn:hover {
            background: var(--accent-hover);
            transform: translateY(-1px);
        }

        .start-btn:disabled {
            background: var(--text-secondary);
            cursor: not-allowed;
            transform: none;
        }

        .chat-header {
            padding: 20px 24px;
            border-bottom: 1px solid var(--border-color);
            background: var(--bg-secondary);
        }

        .chat-title {
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 4px;
        }

        .chat-subtitle {
            color: var(--text-secondary);
            font-size: 14px;
        }

        .status-indicator {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 8px;
        }

        .status-connected {
            background: #22c55e;
        }

        .status-disconnected {
            background: #ef4444;
        }

        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            min-height: 400px;
            max-height: 600px;
        }

        .message {
            margin-bottom: 16px;
            padding: 16px;
            border-radius: 12px;
            position: relative;
            animation: fadeInUp 0.3s ease-out;
        }

        .message.role1 {
            background: var(--role1-bg);
            border-left: 4px solid var(--role1-border);
            margin-right: 40px;
        }

        .message.role2 {
            background: var(--role2-bg);
            border-left: 4px solid var(--role2-border);
            margin-left: 40px;
        }

        .message-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }

        .role-name {
            font-weight: 700;
            font-size: 14px;
        }

        .message.role1 .role-name {
            color: var(--role1-border);
        }

        .message.role2 .role-name {
            color: var(--role2-border);
        }

        .turn-number {
            font-size: 12px;
            color: var(--text-secondary);
            background: rgba(0, 0, 0, 0.05);
            padding: 2px 8px;
            border-radius: 12px;
        }

        .message-content {
            color: var(--text-primary);
            line-height: 1.6;
        }

        .loading-indicator {
            text-align: center;
            padding: 20px;
            color: var(--text-secondary);
        }

        .loading-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--accent-primary);
            margin: 0 2px;
            animation: loadingPulse 1.4s ease-in-out infinite both;
        }

        .loading-dot:nth-child(1) { animation-delay: -0.32s; }
        .loading-dot:nth-child(2) { animation-delay: -0.16s; }
        .loading-dot:nth-child(3) { animation-delay: 0s; }

        .progress-bar {
            height: 4px;
            background: var(--border-color);
            border-radius: 2px;
            overflow: hidden;
            margin: 16px 0;
        }

        .progress-fill {
            height: 100%;
            background: var(--accent-primary);
            border-radius: 2px;
            transition: width 0.3s ease;
        }

        .error-message {
            background: #fef2f2;
            border: 1px solid #fecaca;
            color: #dc2626;
            padding: 12px;
            border-radius: 8px;
            margin: 12px 0;
            text-align: center;
        }

        [data-theme="dark"] .error-message {
            background: #450a0a;
            border-color: #7f1d1d;
            color: #f87171;
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes loadingPulse {
            0%, 80%, 100% {
                transform: scale(0);
            }
            40% {
                transform: scale(1);
            }
        }

        @media (max-width: 768px) {
            .container {
                grid-template-columns: 1fr;
                gap: 16px;
                padding: 16px;
            }
            
            .control-panel {
                order: 2;
            }
            
            .chat-area {
                order: 1;
                min-height: 500px;
            }

            .message.role1 {
                margin-right: 20px;
            }

            .message.role2 {
                margin-left: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="control-panel">
            <div class="header">
                <h1>對話設定</h1>
                <button class="theme-toggle" onclick="toggleTheme()">切換模式</button>
            </div>

            <div class="form-group">
                <label for="role1">角色一名稱</label>
                <input type="text" id="role1" placeholder="例如：伊隆·馬斯克">
            </div>

            <div class="form-group">
                <label for="role2">角色二名稱</label>
                <input type="text" id="role2" placeholder="例如：馬克·祖克柏">
            </div>

            <div class="form-group">
                <label for="topic">對話話題</label>
                <textarea id="topic" placeholder="請輸入想要討論的話題..."></textarea>
            </div>

            <div class="settings-grid">
                <div class="form-group">
                    <label for="wordLimit">字數上限</label>
                    <select id="wordLimit">
                        <option value="100">100字</option>
                        <option value="150" selected>150字</option>
                        <option value="200">200字</option>
                        <option value="250">250字</option>
                    </select>
                </div>

                <div class="form-group">
                    <label for="rounds">對話輪次</label>
                    <select id="rounds">
                        <option value="5">5輪</option>
                        <option value="8" selected>8輪</option>
                        <option value="10">10輪</option>
                        <option value="15">15輪</option>
                    </select>
                </div>
            </div>

            <button id="startBtn" class="start-btn" onclick="startConversation()">開始對話</button>
        </div>

        <div class="chat-area">
            <div class="chat-header">
                <div class="chat-title">
                    <span class="status-indicator status-disconnected" id="statusIndicator"></span>
                    AI角色對話
                </div>
                <div class="chat-subtitle">設定完成後點擊開始對話</div>
            </div>

            <div class="chat-messages" id="chatMessages">
                <div style="text-align: center; color: var(--text-secondary); padding: 40px;">
                    請設定角色和話題後開始對話
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.js"></script>
    <script>
        let socket = null;
        let conversationState = {
            isRunning: false,
            currentRound: 0,
            totalRounds: 0,
            role1Name: '',
            role2Name: '',
            topic: '',
            wordLimit: 150,
            messages: [],
            totalMessages: 0
        };

        // 初始化 Socket.IO 連接
        function initSocket() {
            socket = io();
            
            socket.on('connect', function() {
                console.log('WebSocket 連接成功');
                updateConnectionStatus(true);
            });
            
            socket.on('disconnect', function() {
                console.log('WebSocket 連接斷開');
                updateConnectionStatus(false);
            });
            
            socket.on('show_loading', function(data) {
                showLoading(data.role);
            });
            
            socket.on('hide_loading', function() {
                hideLoading();
            });
            
            socket.on('new_message', function(data) {
                addMessage(data.role, data.content, data.is_role1, data.round);
                conversationState.totalMessages++;
                updateProgress();
            });
            
            socket.on('conversation_finished', function(data) {
                finishConversation(data.total_rounds);
            });
            
            socket.on('error', function(data) {
                showError(data.message);
                enableStartButton();
            });
        }

        function updateConnectionStatus(connected) {
            const indicator = document.getElementById('statusIndicator');
            if (connected) {
                indicator.className = 'status-indicator status-connected';
            } else {
                indicator.className = 'status-indicator status-disconnected';
            }
        }

        function toggleTheme() {
            const body = document.body;
            const currentTheme = body.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            body.setAttribute('data-theme', newTheme);
            
            const toggleBtn = document.querySelector('.theme-toggle');
            toggleBtn.textContent = newTheme === 'dark' ? '淺色模式' : '深色模式';
        }

        async function startConversation() {
            const role1 = document.getElementById('role1').value.trim();
            const role2 = document.getElementById('role2').value.trim();
            const topic = document.getElementById('topic').value.trim();
            const wordLimit = parseInt(document.getElementById('wordLimit').value);
            const rounds = parseInt(document.getElementById('rounds').value);

            if (!role1 || !role2 || !topic) {
                showError('請完整填寫角色名稱和對話話題');
                return;
            }

            if (!socket || !socket.connected) {
                showError('連接已斷開，請重新整理頁面');
                return;
            }

            conversationState = {
                isRunning: true,
                currentRound: 0,
                totalRounds: rounds,
                role1Name: role1,
                role2Name: role2,
                topic: topic,
                wordLimit: wordLimit,
                messages: [],
                totalMessages: 0
            };

            updateChatHeader();
            clearMessages();
            disableStartButton();
            
            try {
                const response = await fetch('/api/start-conversation', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        role1: role1,
                        role2: role2,
                        topic: topic,
                        wordLimit: wordLimit,
                        rounds: rounds
                    })
                });

                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || '開始對話失敗');
                }

                addProgressBar();
                
            } catch (error) {
                console.error('開始對話失敗:', error);
                showError('開始對話失敗：' + error.message);
                enableStartButton();
            }
        }

        function updateChatHeader() {
            const chatTitle = document.querySelector('.chat-title');
            const chatSubtitle = document.querySelector('.chat-subtitle');
            
            // 保留狀態指示器
            const statusIndicator = document.getElementById('statusIndicator');
            chatTitle.innerHTML = '';
            chatTitle.appendChild(statusIndicator);
            chatTitle.appendChild(document.createTextNode(`${conversationState.role1Name} vs ${conversationState.role2Name}`));
            
            chatSubtitle.textContent = `話題：${conversationState.topic} | ${conversationState.totalRounds}輪對話`;
        }

        function clearMessages() {
            const chatMessages = document.getElementById('chatMessages');
            chatMessages.innerHTML = '';
        }

        function addMessage(roleName, content, isRole1, turnNumber) {
            const chatMessages = document.getElementById('chatMessages');
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isRole1 ? 'role1' : 'role2'}`;
            
            messageDiv.innerHTML = `
                <div class="message-header">
                    <span class="role-name">${roleName}</span>
                    <span class="turn-number">第${turnNumber}輪</span>
                </div>
                <div class="message-content">${content}</div>
            `;
            
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function showLoading(roleName) {
            const chatMessages = document.getElementById('chatMessages');
            
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'loading-indicator';
            loadingDiv.id = 'loading';
            loadingDiv.innerHTML = `
                <div>${roleName} 正在思考中...</div>
                <div style="margin-top: 8px;">
                    <span class="loading-dot"></span>
                    <span class="loading-dot"></span>
                    <span class="loading-dot"></span>
                </div>
            `;
            
            chatMessages.appendChild(loadingDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function hideLoading() {
            const loading = document.getElementById('loading');
            if (loading) {
                loading.remove();
            }
        }