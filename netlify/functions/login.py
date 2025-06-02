import json
import os
from urllib.parse import parse_qs

def handler(event, context):
    """
    Netlify Functions 登入處理函數
    """
    
    # 設定 CORS 標頭
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Content-Type': 'application/json'
    }
    
    # 處理 OPTIONS 請求（CORS 預檢）
    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    # 只接受 POST 請求
    if event['httpMethod'] != 'POST':
        return {
            'statusCode': 405,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'message': '只接受 POST 請求'
            })
        }
    
    try:
        # 解析請求內容
        if event.get('body'):
            # 如果是 JSON 格式
            if event.get('headers', {}).get('content-type', '').startswith('application/json'):
                data = json.loads(event['body'])
            else:
                # 如果是表單格式
                parsed_data = parse_qs(event['body'])
                data = {key: value[0] if value else '' for key, value in parsed_data.items()}
        else:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'message': '缺少請求內容'
                })
            }
        
        # 獲取提交的姓名和學號
        user_name = data.get('userName', '').strip()
        student_id = data.get('studentId', '').strip()
        
        # 驗證輸入
        if not user_name or not student_id:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'message': '請填寫完整的姓名和學號'
                })
            }
        
        # 從環境變數獲取有效的登入資訊
        # 您需要在 Netlify 後台設定這些環境變數
        valid_users = get_valid_users()
        
        # 驗證登入資訊
        user_key = f"{user_name}_{student_id}"
        if user_key in valid_users:
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'success': True,
                    'message': f'歡迎 {user_name}！擴充功能已解鎖',
                    'user': {
                        'name': user_name,
                        'studentId': student_id,
                        'permissions': {
                            'maxWords': 150,
                            'maxRounds': 15
                        }
                    }
                })
            }
        else:
            return {
                'statusCode': 401,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'message': '姓名或學號不正確，請檢查後重試'
                })
            }
    
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'message': '請求格式錯誤'
            })
        }
    
    except Exception as e:
        # 記錄錯誤（在生產環境中，不要暴露詳細錯誤訊息）
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'message': '伺服器內部錯誤'
            })
        }

def get_valid_users():
    """
    從環境變數獲取有效用戶列表
    環境變數格式：USER_1=姓名_學號,USER_2=姓名_學號,...
    """
    valid_users = set()
    
    # 方法1: 單獨的環境變數
    # 例如：VALID_USER_1=張三_12345678
    i = 1
    while True:
        user_env = os.environ.get(f'VALID_USER_{i}')
        if not user_env:
            break
        valid_users.add(user_env.strip())
        i += 1
    
    # 方法2: 逗號分隔的環境變數
    # 例如：VALID_USERS=張三_12345678,李四_87654321
    users_env = os.environ.get('VALID_USERS', '')
    if users_env:
        for user in users_env.split(','):
            if user.strip():
                valid_users.add(user.strip())
    
    # 如果沒有設定環境變數，返回測試用戶（僅用於開發）
    if not valid_users:
        print("警告: 未設定有效用戶環境變數，使用測試數據")
        valid_users = {
            '測試用戶_12345678',
            '張三_11111111'
        }
    
    return valid_users