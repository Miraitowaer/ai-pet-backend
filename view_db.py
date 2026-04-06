import sqlite3
import datetime

def view_messages():
    # 连接到 SQLite 数据库文件
    conn = sqlite3.connect('pet_memory.db')
    cursor = conn.cursor()
    
    print("====== 🗄️ 数据库中的记忆内容 🗄️ ======")
    try:
        # 查询 chat_messages 表
        cursor.execute("SELECT id, role, created_at, content FROM chat_messages ORDER BY id ASC")
        rows = cursor.fetchall()
        
        for row in rows:
            msg_id, role, created_at, content = row
            # 格式化输出，截断过长的内容
            display_content = content if content else "[No Content/Tool Action]"
            if len(display_content) > 50:
                display_content = display_content[:50] + "......"
                
            print(f"[{created_at[:19]}] {role.upper():<10} (ID:{msg_id}) -> {display_content}")
            
    except Exception as e:
        print(f"查询失败，确保表已建立: {e}")
    finally:
        print("=========================================")
        conn.close()

if __name__ == "__main__":
    view_messages()
