require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const path = require('path');
const { GoogleGenerativeAI } = require('@google/generative-ai');

const app = express();
const PORT = process.env.PORT || 3000;

// 初始化 Gemini AI
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

// 中間件配置
app.use(helmet({
    contentSecurityPolicy: {
        directives: {
            defaultSrc: ["'self'"],
            styleSrc: ["'self'", "'unsafe-inline'"],
            scriptSrc: ["'self'", "'unsafe-inline'"],
            imgSrc: ["'self'", "data:", "https:"],
        },
    },
}));

app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(express.static('public'));

// 速率限制
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 分鐘
    max: 100, // 每個IP最多100次請求
    message: {
        error: '請求過於頻繁，請稍後再試'
    }
});
app.use('/api/', limiter);

// 對話限制（更嚴格）
const conversationLimiter = rateLimit({
    windowMs: 5 * 60 * 1000, // 5 分鐘
    max: 3, // 每個IP最多3次對話
    message: {
        error: '對話請求過於頻繁，請稍後再試'
    }
});

// 角色對話類
class RoleConversation {
    constructor(role1, role2, topic, wordLimit, rounds) {
        this.role1 = role1;
        this.role2 = role2;
        this.topic = topic;
        this.wordLimit = wordLimit;
        this.rounds = rounds;
        this.conversationHistory = [];
        this.currentRound = 0;
    }

    // 生成角色提示詞
    generateRolePrompt(roleName, isFirst = false, previousMessage = '') {
        let basePrompt = `你現在要扮演 ${roleName}。請完全以 ${roleName} 的身份、語調、專業背景和個性特點來回應。`;
        
        if (isFirst) {
            basePrompt += `\n\n請針對以下話題表達你的觀點：「${this.topic}」`;
        } else {
            basePrompt += `\n\n對方剛才說：「${previousMessage}」\n\n請以 ${roleName} 的身份回應對方的觀點。`;
        }
        
        basePrompt += `\n\n回應要求：
1. 完全符合 ${roleName} 的身份和特色
2. 字數控制在 ${this.wordLimit} 字以內
3. 語調要自然，像真正的對話
4. 不要在回應前後加任何說明文字
5. 直接以第一人稱身份發言`;

        return basePrompt;
    }

    // 調用 Gemini API
    async generateResponse(prompt) {
        try {
            const model = genAI.getGenerativeModel({ model: "gemini-pro" });
            
            const result = await model.generateContent(prompt);
            const response = await result.response;
            let text = response.text();
            
            // 清理回應文本
            text = text.trim();
            text = text.replace(/^「|」$/g, ''); // 移除可能的引號
            text = text.replace(/^我是.*?[：。]/, ''); // 移除可能的身份聲明
            
            // 確保字數限制
            if (text.length > this.wordLimit) {
                text = text.substring(0, this.wordLimit - 3) + '...';
            }
            
            return text;
        } catch (error) {
            console.error('Gemini API 調用失敗:', error);
            throw new Error('AI 回應生成失敗，請稍後再試');
        }
    }

    // 執行完整對話
    async *runConversation() {
        try {
            for (let round = 1; round <= this.rounds; round++) {
                this.currentRound = round;
                
                // 角色1發言
                yield { type: 'loading', role: this.role1, round };
                
                const isFirstRole1 = round === 1;
                const previousMessage = this.conversationHistory.length > 0 
                    ? this.conversationHistory[this.conversationHistory.length - 1].content 
                    : '';
                
                const role1Prompt = this.generateRolePrompt(this.role1, isFirstRole1, previousMessage);
                const role1Response = await this.generateResponse(role1Prompt);
                
                this.conversationHistory.push({
                    role: this.role1,
                    content: role1Response,
                    round: round
                });
                
                yield { 
                    type: 'message', 
                    role: this.role1, 
                    content: role1Response, 
                    round: round,
                    isRole1: true
                };
                
                // 添加延遲，避免API調用過快
                await new Promise(resolve => setTimeout(resolve, 1000));
                
                // 角色2發言
                yield { type: 'loading', role: this.role2, round };
                
                const role2Prompt = this.generateRolePrompt(this.role2, false, role1Response);
                const role2Response = await this.generateResponse(role2Prompt);
                
                this.conversationHistory.push({
                    role: this.role2,
                    content: role2Response,
                    round: round
                });
                
                yield { 
                    type: 'message', 
                    role: this.role2, 
                    content: role2Response, 
                    round: round,
                    isRole1: false
                };
                
                // 添加延遲，避免API調用過快
                if (round < this.rounds) {
                    await new Promise(resolve => setTimeout(resolve, 1000));
                }
            }
            
            yield { type: 'complete', totalRounds: this.rounds };
            
        } catch (error) {
            yield { type: 'error', message: error.message };
        }
    }
}

// API 路由

// 開始對話
app.get('/api/start-conversation', conversationLimiter, async (req, res) => {
    try {
        const { role1, role2, topic, wordLimit, rounds } = req.query;
        
        // 驗證輸入
        if (!role1 || !role2 || !topic) {
            return res.status(400).json({
                error: '請提供完整的角色名稱和話題'
            });
        }
        
        if (parseInt(wordLimit) < 50 || parseInt(wordLimit) > 500) {
            return res.status(400).json({
                error: '字數限制必須在50-500字之間'
            });
        }
        
        if (parseInt(rounds) < 1 || parseInt(rounds) > 20) {
            return res.status(400).json({
                error: '對話輪次必須在1-20輪之間'
            });
        }
        
        // 設置SSE
        res.writeHead(200, {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        });
        
        const conversation = new RoleConversation(role1, role2, topic, parseInt(wordLimit), parseInt(rounds));
        
        // 執行對話並發送事件
        for await (const event of conversation.runConversation()) {
            res.write(`data: ${JSON.stringify(event)}\n\n`);
        }
        
        res.end();
        
    } catch (error) {
        console.error('對話處理失敗:', error);
        res.write(`data: ${JSON.stringify({ 
            type: 'error', 
            message: '系統錯誤，請稍後再試' 
        })}\n\n`);
        res.end();
    }
});

// 健康檢查
app.get('/api/health', (req, res) => {
    res.json({ 
        status: 'ok', 
        timestamp: new Date().toISOString(),
        env: process.env.NODE_ENV || 'development'
    });
});

// 提供前端頁面
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// 錯誤處理中間件
app.use((error, req, res, next) => {
    console.error('伺服器錯誤:', error);
    res.status(500).json({
        error: '內部伺服器錯誤'
    });
});

// 404 處理
app.use((req, res) => {
    res.status(404).json({
        error: '找不到請求的資源'
    });
});

// 啟動伺服器
app.listen(PORT, () => {
    console.log(`伺服器運行在 http://localhost:${PORT}`);
    console.log(`環境: ${process.env.NODE_ENV || 'development'}`);
    
    if (!process.env.GEMINI_API_KEY) {
        console.warn('⚠️  警告: 未設定 GEMINI_API_KEY 環境變數');
    }
});

// 優雅關閉
process.on('SIGTERM', () => {
    console.log('收到 SIGTERM 信號，正在關閉伺服器...');
    process.exit(0);
});

process.on('SIGINT', () => {
    console.log('收到 SIGINT 信號，正在關閉伺服器...');
    process.exit(0);
});