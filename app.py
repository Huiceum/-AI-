from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import google.generativeai as genai
import os
import time
import asyncio
from threading import Thread
import logging
from concurrent.futures import ThreadPoolExecutor

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')

# 修正 SocketIO 配置，適配 Render 部署環境
socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    async_mode='threading',  # 使用 threading 模式
    logger=True,
    engineio_logger=True
)

# 配置 Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY 環境變數未設置")
    raise ValueError("請設置 GEMINI_API_KEY 環境變數")

genai.configure(api_key=GEMINI_API_KEY)

class ConversationManager:
    def __init__(self):
        self.conversations = {}
        self.model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp')
        self.executor = ThreadPoolExecutor(max_workers=4)  # 線程池執行器
    
    def create_conversation(self, session_id, role1, role2, topic, word_limit, rounds):
        """創建新的對話會話"""
        self.conversations[session_id] = {
            'role1': role1,
            'role2': role2,
            'topic': topic,
            'word_limit': word_limit,
            'rounds': rounds,
            'current_round': 0,
            'messages': [],
            'conversation_history': []
        }
        return True
    
    def generate_character_prompt(self, character_name, topic, conversation_history, word_limit):
        """生成角色專屬的提示詞"""
        history_text = ""
        if conversation_history:
            history_text = "前面的對話內容：\n"
            for msg in conversation_history[-6:]:  # 只取最近6條對話
                history_text += f"{msg['role']}: {msg['content']}\n"
            history_text += "\n"
        
        prompt = f"""你現在要扮演 {character_name}。請根據這個角色的特點、說話方式和觀點來回應。

對話主題：{topic}

{history_text}請以 {character_name} 的身份，針對目前的對話內容進行回應。

要求：
1. 保持角色一致性，符合 {character_name} 的特點和說話風格
2. 回應要自然流暢，與前面的對話內容相關
3. 字數控制在 {word_limit} 字以內
4. 不要重複前面已經說過的內容
5. 展現這個角色獨特的觀點和個性

請直接回應，不要加任何前綴或說明："""
        
        return prompt
    
    def generate_response_sync(self, session_id, current_role):
        """同步生成 AI 回應"""
        try:
            conversation = self.conversations[session_id]
            
            prompt = self.generate_character_prompt(
                current_role,
                conversation['topic'],
                conversation['conversation_history'],
                conversation['word_limit']
            )
            
            # 添加重試機制
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.model.generate_content(prompt)
                    if response.text:
                        return response.text.strip()
                except Exception as e:
                    logger.warning(f"生成回應嘗試 {attempt + 1} 失敗: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(1)  # 等待後重試
                    else:
                        raise e
                        
        except Exception as e:
            logger.error(f"生成回應時發生錯誤: {e}")
            return f"抱歉，{current_role} 暫時無法回應，請稍後再試。"
    
    def add_message(self, session_id, role, content, round_num):
        """添加消息到對話歷史"""
        if session_id in self.conversations:
            message = {
                'role': role,
                'content': content,
                'round': round_num
            }
            self.conversations[session_id]['messages'].append(message)
            self.conversations[session_id]['conversation_history'].append(message)
            return True
        return False

conversation_manager = ConversationManager()

@app.route('/')
def index():
    """主頁面"""
    return render_template('index.html')

@app.route('/api/start-conversation', methods=['POST'])
def start_conversation():
    """開始對話的 API 端點"""
    try:
        data = request.json
        # 生成唯一的 session_id
        session_id = f"session_{int(time.time() * 1000)}"
        
        role1 = data.get('role1', '').strip()
        role2 = data.get('role2', '').strip()
        topic = data.get('topic', '').strip()
        word_limit = int(data.get('wordLimit', 150))
        rounds = int(data.get('rounds', 8))
        
        if not all([role1, role2, topic]):
            return jsonify({'error': '請完整填寫所有必要資訊'}), 400
        
        if word_limit < 50 or word_limit > 500:
            return jsonify({'error': '字數限制應在 50-500 之間'}), 400
            
        if rounds < 1 or rounds > 20:
            return jsonify({'error': '對話輪數應在 1-20 之間'}), 400
        
        # 創建對話會話
        conversation_manager.create_conversation(
            session_id, role1, role2, topic, word_limit, rounds
        )
        
        # 在背景開始對話
        thread = Thread(target=run_conversation_background, args=(session_id,))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': '對話已開始'
        })
        
    except ValueError as e:
        logger.error(f"輸入驗證錯誤: {e}")
        return jsonify({'error': '輸入格式錯誤'}), 400
    except Exception as e:
        logger.error(f"開始對話時發生錯誤: {e}")
        return jsonify({'error': '開始對話失敗，請稍後再試'}), 500

def run_conversation_background(session_id):
    """在背景執行對話流程"""
    try:
        if session_id not in conversation_manager.conversations:
            logger.error(f"找不到會話: {session_id}")
            return
            
        conversation = conversation_manager.conversations[session_id]
        
        for round_num in range(1, conversation['rounds'] + 1):
            try:
                # 角色1發言
                socketio.emit('show_loading', {
                    'role': conversation['role1'],
                    'session_id': session_id
                })
                
                time.sleep(2)  # 模擬思考時間
                
                response1 = conversation_manager.generate_response_sync(
                    session_id, conversation['role1']
                )
                
                conversation_manager.add_message(
                    session_id, conversation['role1'], response1, round_num
                )
                
                socketio.emit('hide_loading', {'session_id': session_id})
                socketio.emit('new_message', {
                    'role': conversation['role1'],
                    'content': response1,
                    'round': round_num,
                    'is_role1': True,
                    'session_id': session_id
                })
                
                time.sleep(1)
                
                # 角色2發言
                socketio.emit('show_loading', {
                    'role': conversation['role2'],
                    'session_id': session_id
                })
                
                time.sleep(2)  # 模擬思考時間
                
                response2 = conversation_manager.generate_response_sync(
                    session_id, conversation['role2']
                )
                
                conversation_manager.add_message(
                    session_id, conversation['role2'], response2, round_num
                )
                
                socketio.emit('hide_loading', {'session_id': session_id})
                socketio.emit('new_message', {
                    'role': conversation['role2'],
                    'content': response2,
                    'round': round_num,
                    'is_role1': False,
                    'session_id': session_id
                })
                
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"第 {round_num} 輪對話錯誤: {e}")
                socketio.emit('error', {
                    'message': f'第 {round_num} 輪對話發生錯誤',
                    'session_id': session_id
                })
                break
        
        # 對話完成
        socketio.emit('conversation_finished', {
            'total_rounds': conversation['rounds'],
            'session_id': session_id
        })
        
        # 清理會話數據（可選）
        # del conversation_manager.conversations[session_id]
        
    except Exception as e:
        logger.error(f"背景對話執行錯誤: {e}")
        socketio.emit('error', {
            'message': '對話過程中發生錯誤',
            'session_id': session_id
        })

@socketio.on('connect')
def handle_connect():
    """WebSocket 連接處理"""
    logger.info('客戶端已連接')
    emit('connected', {'message': '連接成功'})

@socketio.on('disconnect')
def handle_disconnect():
    """WebSocket 斷線處理"""
    logger.info('客戶端已斷線')

@socketio.on('join_session')
def handle_join_session(data):
    """處理客戶端加入會話"""
    session_id = data.get('session_id')
    if session_id:
        logger.info(f'客戶端加入會話: {session_id}')
        emit('joined_session', {'session_id': session_id})

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': '頁面不存在'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"伺服器錯誤: {error}")
    return jsonify({'error': '伺服器內部錯誤'}), 500

# 健康檢查端點
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': time.time()})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    socketio.run(app, host='0.0.0.0', port=port, debug=debug_mode)