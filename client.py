import socket
import struct
import json
import threading

def receive_msgs(s):
    """专门负责接收服务器广播的消息"""
    while True:
        try:
            header_data = s.recv(4)
            if not header_data:
                break

            length = struct.unpack("i", header_data)[0]

            data = s.recv(length)# 有可能阻塞；如果服务器断开连接，recv接收并返回bytes，此时data就是b''
            if not data:
                break

            msg_obj = json.loads(data.decode('utf-8'))
            print(f"\n[{msg_obj['ID']}]: {msg_obj['content']}")
            print("输入消息: ", end="") # 重新提示输入
        except:
            break

ID = input("请输入你的昵称: ")
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("127.0.0.1", 8888))

"""
主线程
"""

# 启动接收线程
threading.Thread(target=receive_msgs, args=(s,), daemon=True).start()
# daemon=True 表示这个线程是一个守护线程，主线程退出时，守护线程会自动被杀死
# 防止recv一直阻塞，导致程序无法退出

while True:
    content = input()
    if content == "quit":
        break
    
    msg_dict = {"ID": ID, "content": content}
    # 发送消息时，先把字典转换成 JSON 字符串，再编码成 bytes
    msg_bytes = json.dumps(msg_dict).encode('utf-8')
    
    header = struct.pack("i", len(msg_bytes))
    s.sendall(header + msg_bytes)

s.close()