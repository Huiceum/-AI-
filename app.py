from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import google.generativeai as genai
import os
import time
import asyncio
from threading import Thread
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
socketio = SocketIO(app, cors_allowed_origins="*")

# 配置 Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY 環境變數未設置")
    raise ValueError("請設置 GEMINI_API_KEY 環境變數")

genai.configure(api_key=GEMINI_API_KEY)

class ConversationManager:
    def __init__(self):
        self.conversations = {}
        # 使用 Gemini 1.5 Flash 模型，針對速度進行優化
        self.model = genai.GenerativeModel('models/gemini-2.5-flash-preview-04-17-thinking') 
    
    def create_conversation(self, session_id, role1, role2, role1_description, role2_description, topic, word_limit, rounds, narrator_mode):
        """創建新的對話會話，新增 narrator_mode 參數"""
        self.conversations[session_id] = {
            'role1': role1,
            'role2': role2,
            'role1_description': role1_description,
            'role2_description': role2_description,
            'topic': topic,
            'word_limit': word_limit,
            'rounds': rounds,
            'current_round': 0,
            'messages': [], # 儲存實際對話和旁白訊息
            'conversation_history': [], # 僅儲存對話訊息，用於生成角色回應
            'story_outline': None,
            'narrator_mode': narrator_mode # NEW: 儲存旁白模式設定
        }
        return True
    
    async def generate_story_outline(self, session_id):
        """生成故事大綱"""
        try:
            conversation = self.conversations[session_id]
            
            outline_prompt = f"""
請根據以下設定，為一場對話生成一個詳細的故事大綱：
角色設定：
• {conversation['role1']}：{conversation['role1_description']}
• {conversation['role2']}：{conversation['role2_description']}
對話主題：{conversation['topic']}
對話輪數：{conversation['rounds']}輪
請生成一個完整的故事大綱，包含：
1. 故事背景和情境設定
2. 兩個角色在這個話題上的不同立場或觀點
3. 對話的發展脈絡（從開始到結束的情節走向）
4. 可能的衝突點和解決方向
5. 預期的對話結果或結論
6. 大綱的字數不超過200字，以摘要的方式呈現劇情走向就好了。
大綱要能引導{conversation['rounds']}輪的自然對話發展，每輪對話都要有意義和推進作用。
請直接回答故事大綱，不需要其他說明，也不要試圖使用加粗等文字格式：
"""
            
            # 使用 asyncio.to_thread 執行同步的 API 呼叫，避免阻塞
            response = await asyncio.to_thread(self.model.generate_content, outline_prompt)
            outline = response.text.strip()
            
            # 儲存故事大綱
            conversation['story_outline'] = outline
            
            return outline
            
        except Exception as e:
            logger.error(f"生成故事大綱時發生錯誤: {e}")
            return None
    
    def generate_character_prompt(self, character_name, character_description, topic, conversation_history, word_limit, story_outline, current_round, total_rounds):
        """生成角色專屬的提示詞，基於故事大綱"""
        
        # 構建對話歷史
        history_text = ""
        if conversation_history:
            history_text = "目前的對話內容：\n"
            for msg in conversation_history:
                history_text += f"{msg['role']}: {msg['content']}\n"
            history_text += "\n"
        
        # 計算對話進度，輔助 LLM 理解當前階段
        progress_info = f"目前進度：第{current_round}輪，共{total_rounds}輪"
        if current_round <= total_rounds // 3:
            stage = "對話初期，需要建立立場和觀點"
        elif current_round <= total_rounds * 2 // 3:
            stage = "對話中期，需要深入探討和交流意見"
        else:
            stage = "對話後期，需要總結或達成某種共識"
        
        prompt = f"""
你現在要扮演 {character_name}。
角色設定：
{character_description}
故事大綱：
{story_outline}
對話主題：{topic}
對話紀錄：{history_text}
非語言的資訊：{progress_info}
當前階段：{stage}
請以 {character_name} 的身份，根據故事大綱的發展脈絡，針對當前對話內容進行回應。
要求：
1. 嚴格按照角色設定的性格、背景和特點來回應
2. 回應要符合故事大綱的發展方向
3. 考慮當前對話階段，確保對話有意義的推進，不要重複上次的對話。
4. 與前面的對話內容相關聯，保持邏輯連貫性
5. 字數嚴格控制在五個字到 {word_limit} 個字
6. 展現角色獨特的觀點和立場
7. 推動對話向故事大綱的方向發展
8. 切勿與上一次的對話相同
請直接以 {character_name} 的身份回應，不要添加任何前綴或說明：
"""
        
        return prompt
    
    async def generate_response(self, session_id, current_role):
        """生成 AI 回應"""
        try:
            conversation = self.conversations[session_id]
            
            # 確定當前角色的描述
            if current_role == conversation['role1']:
                character_description = conversation['role1_description']
            else:
                character_description = conversation['role2_description']
            
            # 計算當前輪數（基於 conversation_history 的長度）
            current_round = len(conversation['conversation_history']) // 2 + 1
            
            prompt = self.generate_character_prompt(
                current_role,
                character_description,
                conversation['topic'],
                conversation['conversation_history'],
                conversation['word_limit'],
                conversation['story_outline'],
                current_round,
                conversation['rounds']
            )
            
            # 使用 asyncio.to_thread 執行同步的 API 呼叫
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"生成回應時發生錯誤: {e}")
            return f"抱歉，{current_role} 暫時無法回應，請稍後再試。"

    # NEW: 生成旁白描述的函數
    async def generate_narrator_description(self, session_id):
        """生成旁白描述"""
        try:
            conversation = self.conversations[session_id]
            
            # 獲取最近的對話內容作為旁白的上下文
            # 這裡我們使用 conversation['messages'] 因為它包含了所有已發送的內容
            # 但旁白的提示詞應只關注最近的對話 "實質內容"
            
            # 從 conversation_history 中獲取最新的兩則對話（如果存在）
            recent_dialogue = conversation['conversation_history'][-2:]
            
            recent_dialogue_text = ""
            if recent_dialogue:
                recent_dialogue_text = "最近對話內容：\n"
                for msg in recent_dialogue:
                    recent_dialogue_text += f"{msg['role']}: {msg['content']}\n"
            
            narrator_prompt = f"""
你是一位資深的小說旁白者，精於描繪場景、人物動作、內心狀態和氛圍，你的主要目的是要推進劇情。
當前故事背景：
主題：{conversation['topic']}
角色1: {conversation['role1']} ({conversation['role1_description']})
角色2: {conversation['role2']} ({conversation['role2_description']})
故事大綱：{conversation['story_outline']}
目前進度：第{conversation['current_round']}輪
{recent_dialogue_text}
請根據以上資訊和最新的對話內容，以客觀、生動的第三人稱視角，簡潔地描述當前場景的動作、非語言資訊、氛圍變化，以及角色可能展現出的情緒或反應。
請注意：
1. 描述內容應與對話進程和故事大綱保持一致。同時可適時的加入動作及角色非語言的互動好推進劇情
2. 字數請控制在5-30字之間。
3. 直接回答旁白內容，不要添加任何前綴、後綴或說明。
4. 切勿與上一次的對話相同
"""
            # 使用 asyncio.to_thread 執行同步的 API 呼叫
            response = await asyncio.to_thread(self.model.generate_content, narrator_prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"生成旁白描述時發生錯誤: {e}")
            return "（旁白描述生成失敗，請聯繫管理員。）" # 提供一個更友好的錯誤提示
    
    def add_message(self, session_id, msg_type, role=None, content=None, round_num=None, is_role1=None):
        """
        添加訊息到對話歷史 (統一處理對話和旁白訊息)。
        msg_type: 'dialogue' 或 'narrator'
        """
        if session_id in self.conversations:
            if msg_type == 'dialogue':
                message_obj = {
                    'type': 'dialogue',
                    'role': role,
                    'content': content,
                    'round': round_num,
                    'is_role1': is_role1
                }
                self.conversations[session_id]['messages'].append(message_obj)
                self.conversations[session_id]['conversation_history'].append({
                    'role': role,
                    'content': content
                }) # 只有對話內容才加入 conversation_history
            elif msg_type == 'narrator':
                message_obj = {
                    'type': 'narrator',
                    'content': content,
                    'round': round_num # 旁白也標註輪次
                }
                self.conversations[session_id]['messages'].append(message_obj)
            return True
        return False
    
    def get_conversation(self, session_id):
        """獲取對話資訊"""
        return self.conversations.get(session_id)

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
        session_id = request.sid if hasattr(request, 'sid') else str(time.time())
        
        role1 = data.get('role1', '').strip()
        role2 = data.get('role2', '').strip()
        role1_description = data.get('role1Description', '').strip()
        role2_description = data.get('role2Description', '').strip()
        topic = data.get('topic', '').strip()
        word_limit = int(data.get('wordLimit', 150))
        rounds = int(data.get('rounds', 8))
        narrator_mode = data.get('narratorMode', False) # NEW: 接收旁白模式設定
        
        if not all([role1, role2, topic]):
            return jsonify({'error': '請完整填寫所有必要資訊'}), 400
        
        # 創建對話會話，傳遞 narrator_mode
        conversation_manager.create_conversation(
            session_id, role1, role2, role1_description, role2_description, 
            topic, word_limit, rounds, narrator_mode
        )
        
        # 在背景開始對話（包含生成故事大綱）
        thread = Thread(target=run_conversation_background, args=(session_id,))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': '對話已開始'
        })
        
    except Exception as e:
        logger.error(f"開始對話時發生錯誤: {e}")
        return jsonify({'error': '開始對話失敗'}), 500

def run_conversation_background(session_id):
    """在背景執行對話流程，新增旁白生成"""
    try:
        conversation = conversation_manager.conversations[session_id]
        
        # 首先生成故事大綱
        logger.info(f"開始生成故事大綱 - Session: {session_id}")
        story_outline = asyncio.run(conversation_manager.generate_story_outline(session_id))
        
        if story_outline:
            socketio.emit('story_outline_generated', {
                'outline': story_outline
            })
            logger.info(f"故事大綱生成完成 - Session: {session_id}")
        else:
            socketio.emit('story_outline_error', {
                'message': '故事大綱生成失敗'
            })
            logger.error(f"故事大綱生成失敗 - Session: {session_id}")
        
        # 等待一下再開始對話
        time.sleep(2)
        
        # 開始對話循環
        for round_num in range(1, conversation['rounds'] + 1):
            conversation['current_round'] = round_num # 更新當前輪數
            logger.info(f"開始第 {round_num} 輪對話 - Session: {session_id}")
            
            # 角色1發言
            socketio.emit('show_loading', {
                'role': conversation['role1']
            })
            
            time.sleep(1)  # 模擬思考時間
            
            response1 = asyncio.run(conversation_manager.generate_response(
                session_id, conversation['role1']
            ))
            
            conversation_manager.add_message(
                session_id, 'dialogue', role=conversation['role1'], content=response1, 
                round_num=round_num, is_role1=True
            )
            
            socketio.emit('hide_loading')
            socketio.emit('new_message', {
                'role': conversation['role1'],
                'content': response1,
                'round': round_num,
                'is_role1': True
            })
            
            logger.info(f"角色1({conversation['role1']})發言完成 - 第{round_num}輪")
            time.sleep(1)
            
            # 角色2發言
            socketio.emit('show_loading', {
                'role': conversation['role2']
            })
            
            time.sleep(1)  # 模擬思考時間
            
            response2 = asyncio.run(conversation_manager.generate_response(
                session_id, conversation['role2']
            ))
            
            conversation_manager.add_message(
                session_id, 'dialogue', role=conversation['role2'], content=response2, 
                round_num=round_num, is_role1=False
            )
            
            socketio.emit('hide_loading')
            socketio.emit('new_message', {
                'role': conversation['role2'],
                'content': response2,
                'round': round_num,
                'is_role1': False
            })
            
            logger.info(f"角色2({conversation['role2']})發言完成 - 第{round_num}輪")
            time.sleep(1)

            # NEW: 旁白發言 (在每輪對話結束後)
            if conversation['narrator_mode']:
                logger.info(f"開始生成旁白描述 - 第{round_num}輪")
                socketio.emit('show_loading', {'role': '旁白'})
                time.sleep(1) # 模擬思考時間
                
                narrator_content = asyncio.run(conversation_manager.generate_narrator_description(session_id))
                
                conversation_manager.add_message(
                    session_id, 'narrator', content=narrator_content, round_num=round_num
                )
                
                socketio.emit('hide_loading')
                socketio.emit('new_narrator_message', { # 發送新的旁白事件
                    'content': narrator_content
                })
                logger.info(f"旁白發言完成 - 第{round_num}輪")
                time.sleep(1) # 旁白和下一輪開始之間也休息一下
        
        # 對話完成
        socketio.emit('conversation_finished', {
            'total_rounds': conversation['rounds']
        })
        
        logger.info(f"對話完成 - Session: {session_id}, 總輪數: {conversation['rounds']}")
        
    except Exception as e:
        logger.error(f"背景對話執行錯誤 - Session: {session_id}, Error: {e}")
        socketio.emit('error', {'message': '對話過程中發生錯誤'})

@app.route('/api/conversation/<session_id>', methods=['GET'])
def get_conversation_info(session_id):
    """獲取對話資訊的 API"""
    try:
        conversation = conversation_manager.get_conversation(session_id)
        if not conversation:
            return jsonify({'error': '找不到對話記錄'}), 404
        
        return jsonify({
            'success': True,
            'conversation': {
                'role1': conversation['role1'],
                'role2': conversation['role2'],
                'role1_description': conversation['role1_description'],
                'role2_description': conversation['role2_description'],
                'topic': conversation['topic'],
                'word_limit': conversation['word_limit'],
                'rounds': conversation['rounds'],
                'current_round': conversation['current_round'],
                'story_outline': conversation['story_outline'],
                'narrator_mode': conversation['narrator_mode'], # NEW: 返回旁白模式狀態
                'messages': conversation['messages']
            }
        })
        
    except Exception as e:
        logger.error(f"獲取對話資訊錯誤: {e}")
        return jsonify({'error': '獲取對話資訊失敗'}), 500

@socketio.on('connect')
def handle_connect():
    """WebSocket 連接處理"""
    logger.info(f'客戶端已連接 - Session: {request.sid}')
    emit('connected', {'message': '連接成功'})

@socketio.on('disconnect')
def handle_disconnect():
    """WebSocket 斷線處理"""
    logger.info(f'客戶端已斷線 - Session: {request.sid}')
    
    # 清理對話資料
    if request.sid in conversation_manager.conversations:
        del conversation_manager.conversations[request.sid]
        logger.info(f'已清理對話資料 - Session: {request.sid}')

@socketio.on('get_story_outline')
def handle_get_story_outline(data):
    """處理獲取故事大綱的請求"""
    try:
        session_id = data.get('session_id', request.sid)
        conversation = conversation_manager.get_conversation(session_id)
        
        if conversation and conversation.get('story_outline'):
            emit('story_outline_generated', {
                'outline': conversation['story_outline']
            })
        else:
            emit('story_outline_error', {
                'message': '找不到故事大綱'
            })
            
    except Exception as e:
        logger.error(f"獲取故事大綱錯誤: {e}")
        emit('story_outline_error', {
            'message': '獲取故事大綱失敗'
        })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': '頁面不存在'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"伺服器內部錯誤: {error}")
    return jsonify({'error': '伺服器內部錯誤'}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    logger.info(f"啟動伺服器，Port: {port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=False)