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
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    # 只接受 POST 請求
    if event.get('httpMethod') != 'POST':
        return {
            'statusCode': 405,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'message': '只接受 POST 請求'
            }, ensure_ascii=False)
        }
    
    try:
        # 解析請求內容
        body = event.get('body', '')
        if not body:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'message': '缺少請求內容'
                }, ensure_ascii=False)
            }
        
        # 檢查 Content-Type
        content_type = event.get('headers', {}).get('content-type', '') or \
                      event.get('headers', {}).get('Content-Type', '')
        
        if 'application/json' in content_type:
            data = json.loads(body)
        else:
            # 處理表單格式
            parsed_data = parse_qs(body)
            data = {key: value[0] if value else '' for key, value in parsed_data.items()}
        
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
                }, ensure_ascii=False)
            }
        
        # 從環境變數獲取有效的登入資訊
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
                }, ensure_ascii=False)
            }
        else:
            return {
                'statusCode': 401,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'message': '姓名或學號不正確，請檢查後重試'
                }, ensure_ascii=False)
            }
    
    except json.JSONDecodeError as e:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'message': '請求格式錯誤'
            }, ensure_ascii=False)
        }
    
    except Exception as e:
        # 在開發階段可以打印錯誤，生產環境建議移除
        print(f"Error in login function: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'message': '伺服器內部錯誤'
            }, ensure_ascii=False)
        }

def get_valid_users():
    """
    從環境變數獲取有效用戶列表
    """
    valid_users = set()
    
    # 方法1: 單獨的環境變數
    i = 1
    while True:
        user_env = os.environ.get(f'VALID_USER_{i}')
        if not user_env:
            break
        valid_users.add(user_env.strip())
        i += 1
    
    # 方法2: 逗號分隔的環境變數
    users_env = os.environ.get('VALID_USERS', '')
    if users_env:
        for user in users_env.split(','):
            if user.strip():
                valid_users.add(user.strip())
    
    # 測試環境變數（僅用於開發測試）
    if not valid_users:
        print("警告: 未設定有效用戶環境變數，使用測試數據")
        valid_users = {
            '測試用戶_12345678',
            '張三_11111111'
        }
    
    return valid_users