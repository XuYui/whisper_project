import socket
import threading
import struct
import json

# 全局变量：存储所有已连接的客户端
clients = []
clients_lock = threading.Lock() # 互斥锁

def receive_all(conn, count):
    buf = b"" #只支持ASCII
    while count:
        newbuf = conn.recv(count) # recv返回的一定是bytes
        if not newbuf:
            return None
        buf += newbuf
        count -= len(newbuf)
    return buf

def broadcast(msg_bytes, sender_conn):
    """广播消息给除了发送者以外的所有人"""
    with clients_lock:
        clients_copy = clients[:] 
    # 拿锁，快照后马上放回，减少锁的持有时间

    for client in clients_copy:
        if client != sender_conn:
            try:
                header = struct.pack("i", len(msg_bytes))
                client.sendall(header + msg_bytes)
            except (BrokenPipeError, ConnectionResetError, OSError):
                # 按照快照发送，可能会出现想要发送的客户端已经断开了连接的情况。捕获异常，跳过这个客户端
                print("发现一个幽灵客户端，发送失败，跳过。")
                continue

def handle_client(conn, addr):
    print(f"[系统] {addr} 已连接")

    with clients_lock:
        clients.append(conn) # 拿锁，修改列表，放锁

    try:
        while True:

            header_data = receive_all(conn, 4)
            if not header_data:
                break
            
            length = struct.unpack("i", header_data)[0]#返回的是一个元组，第一个元素是长度
            
            # 接收
            data = receive_all(conn, length)
            if not data:
                break
            
            # decode：字节转字符串
            # json.loads：字符串转字典
            msg_obj = json.loads(data.decode('utf-8'))
            print(f"[{msg_obj['ID']}]: {msg_obj['content']}")
            
            broadcast(data, conn)
            
    except Exception as e:
        print(f"[错误] {addr}: {e}")

    finally: # 如果客户端不断开连接，就不会出try里的循环。进入到finally时，说明客户端断开了连接。执行清理工作
        with clients_lock:
            if conn in clients:
                clients.remove(conn)
        conn.close()
        print(f"[系统] {addr} 已断开")


"""
主线程：负责监听新连接
"""

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # 允许重启后立即绑定端口

s.bind(("127.0.0.1", 8888))
s.listen(5)

print("服务器启动，等待连接...")

while True:
    conn, addr = s.accept()
    t = threading.Thread(target=handle_client, args=(conn, addr))
    t.start()