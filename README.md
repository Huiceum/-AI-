# AI 角色對話系統

一個基於 Flask 和 Google Gemini API 的智能對話系統，讓使用者可以設定兩個 AI 角色進行自動對話。

## 功能特色

✨ **角色設定**：自訂兩個 AI 角色名稱和特性  
🎯 **話題設定**：設定對話的初始話題  
🤖 **自動對話**：AI 角色會根據設定自動進行對話  
⚙️ **參數控制**：可調整字數限制和對話輪次  
🎨 **即時顯示**：對話內容即時顯示，支援深淺色主題  
📱 **響應式設計**：支援桌面和行動裝置

## 技術架構

- **後端**：Flask + Flask-SocketIO
- **前端**：HTML5 + CSS3 + JavaScript + Socket.IO
- **AI 引擎**：Google Gemini Pro API
- **部署平台**：Render.com

## 快速開始

### 1. 本地開發

```bash
# 克隆專案
git clone <your-repo-url>
cd ai-dialogue-system

# 安裝依賴
pip install -r requirements.txt

# 設置環境變數
cp .env.example .env
# 編輯 .env 檔案，填入你的 GEMINI_API_KEY

# 啟動應用
python app.py
```

### 2. 獲取 Gemini API 金鑰

1. 前往 [Google AI Studio](https://makersuite.google.com/app/apikey)
2. 登入你的 Google 帳戶
3. 點擊 "Create API Key"
4. 複製生成的 API 金鑰

### 3. 部署到 Render

#### 方法一：使用 GitHub 連接

1. 將專案推送到 GitHub
2. 登入 [Render.com](https://render.com)
3. 點擊 "New" → "Web Service"
4. 連接你的 GitHub 倉庫
5. 設置以下環境變數：
   - `GEMINI_API_KEY`: 你的 Gemini API 金鑰
   - `SECRET_KEY`: 隨機生成的密鑰（可選）

#### 方法二：使用 render.yaml 自動部署

1. 確保專案根目錄有 `render.yaml` 檔案
2. 在 Render 控制台手動設置 `GEMINI_API_KEY` 環境變數
3. 部署會自動開始

## 使用說明

### 基本操作

1. **設定角色**：在左側面板輸入兩個角色的名稱
2. **設定話題**：輸入想要討論的話題
3. **調整參數**：
   - 字數上限：每次回應的最大字數
   - 對話輪次：總共進行的對話輪數
4. **開始對話**：點擊「開始對話」按鈕
5. **觀看對話**：系統會自動生成對話內容

### 角色設定技巧

- 使用具體的人物名稱（如：伊隆·馬斯克、比爾·蓋茲）
- 也可以使用虛構角色（如：樂觀的創業家、謹慎的投資者）
- 角色特性會影響對話風格和觀點

### 話題建議

- **科技話題**：人工智慧、區塊鏈、元宇宙
- **商業話題**：創業、投資、市場趨勢
- **社會話題**：教育、環保、未來發展
- **哲學話題**：人生意義、道德倫理、社會責任

## 專案結構

```
ai-dialogue-system/
├── app.py                 # Flask 主應用程式
├── requirements.txt       # Python 依賴套件
├── Dockerfile            # Docker 容器設定
├── render.yaml           # Render 部署設定
├── .env.example          # 環境變數範例
├── templates/
│   └── index.html        # 前端頁面
└── README.md             # 專案說明
```

## API 端點

### HTTP 端點

- `GET /` - 主頁面
- `POST /api/start-conversation` - 開始對話

### WebSocket 事件

#### 客戶端接收事件

- `connect` - 連接成功
- `show_loading` - 顯示載入狀態
- `hide_loading` - 隱藏載入狀態
- `new_message` - 新訊息
- `conversation_finished` - 對話完成
- `error` - 錯誤訊息

## 環境變數

| 變數名稱 | 必要性 | 說明 |
|---------|--------|------|
| `GEMINI_API_KEY` | 必要 | Google Gemini API 金鑰 |
| `SECRET_KEY` | 可選 | Flask 會話密鑰 |
| `PORT` | 可選 | 應用程式端口（預設：5000） |

## 故障排除

### 常見問題

1. **API 金鑰錯誤**
   - 確認 `GEMINI_API_KEY` 設置正確
   - 檢查 API 金鑰是否有效且有足夠配額

2. **連接問題**
   - 檢查網路連接
   - 確認 WebSocket 連接正常

3. **對話無法開始**
   - 確認所有必要欄位都已填寫
   - 檢查瀏覽器控制台是否有錯誤訊息

### 日誌查看

```bash
# 本地開發
python app.py

# Render 部署
# 在 Render 控制台查看應用程式日誌
```

## 開發指南

### 本地開發環境

1. 安裝 Python 3.11+
2. 創建虛擬環境：`python -m venv venv`
3. 啟動虛擬環境：`source venv/bin/activate` (Linux/Mac) 或 `venv\Scripts\activate` (Windows)
4. 安裝依賴：`pip install -r requirements.txt`

### 自訂功能

- **修改 AI 提示詞**：編輯 `app.py` 中的 `generate_character_prompt` 方法
- **調整介面樣式**：修改 `templates/index.html` 中的 CSS
- **添加新功能**：擴展 Flask 路由和 WebSocket 事件處理

## 授權條款

本專案採用 MIT 授權條款。請參閱 LICENSE 檔案了解詳情。

## 貢獻指南

歡迎提交 Issue 和 Pull Request！

1. Fork 本專案
2. 創建功能分支：`git checkout -b feature/amazing-feature`
3. 提交變更：`git commit -m 'Add amazing feature'`
4. 推送分支：`git push origin feature/amazing-feature`
5. 提交 Pull Request

## 支援

如果您在使用過程中遇到問題，請：

1. 查看本 README 的故障排除章節
2. 檢查 [GitHub Issues](your-repo-url/issues)
3. 提交新的 Issue 描述問題

---

**注意**：本專案需要 Google Gemini API 金鑰才能正常運作。請確保你有有效的 API 金鑰並已正確設置環境變數。