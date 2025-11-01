#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精简版节点获取与测试
直接请求指定线路节点并进行测试
"""

import requests
import json
import time
import socket
import urllib.parse
import base64
from datetime import datetime

# 禁用SSL警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 剪贴板操作
try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False
    print("⚠ 警告: pyperclip未安装，无法写入剪贴板")
    print("   安装命令: pip install pyperclip")

# 尝试导入httpx以支持HTTP/2
try:
    import httpx
    HTTP2_AVAILABLE = True
except ImportError:
    HTTP2_AVAILABLE = False
    print("⚠ 警告: httpx未安装，将使用HTTP/1.1")
    print("   安装命令: pip install httpx[http2]")


class NodeTester:
    def __init__(self):
        # 基础配置
        self.base_url = "https://abscf2.fobwifi.com"
        self.token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwNzczMDE5NzUsImlhdCI6MTc2MTk0MTk3NSwia2V5IjoiMUYyQ0QyQkEyRTkyOTAwMFl3bzFcXFM0UzJZaXhwNTRhQ3I5cTM4emlHN3h0QW1RWkE5aFo4OVQ1VjlbenJjYnciLCJvcmciOiJ0cmFuc29ja3NfbWl4IiwidXNlciI6eyJpZCI6MTk4MjQ5MTJ9fQ.OYB_OY7vbbNarMgi5LcvHKi03SPhSrHwzoYD0rOK8kU"
        
        # HTTP/2客户端
        if HTTP2_AVAILABLE:
            self.http2_client = httpx.Client(http2=True, verify=False)
        else:
            self.http2_client = None
        
        # 本地固定的用户信息（从用户信息/response_body.json获取）
        self.user_info = {
            "code": 0,
            "status": "ok",
            "user_id": 19367511,
            "expired": False,
            "expire_at": "2038-09-05 00:00:00",
            "expire_at_time": 1757001600,
            "is_realname": True,
            "ads_free_before": "3470-01-01 08:00:01",
            "ads_free_before_time": 0,
            "is_device_login": True,
            "email": "",
            "google_subscription_status": 0,
            "huawei_subscription_status": 1,
            "apple_subscription_status": 1,
            "realname_grace_state": 1,
            "password_setup": True,
            "transocks_id": 19467511,
            "ads_free": True,
            "email_verified": False,
            "phone": "",
            "is_pro_user": True,
            "is_new_user": False,
            "is_today_new_user": False,
            "nick": "穿梭 19467511",
            "cc": "",
            "remaining_days": 0,
            "remaining_seconds": 0,
            "ads_remaining_days": 0,
            "default_protocol": "ss",
            "is_need_gps_dialog": False,
            "purchased": True,
            "is_face_verification": True
        }
        
        # 设备参数
        self.device_params = {
            "app_version": "4.3.2",
            "channel": "google",
            "device": "Android",
            "langue": "zh",
            "mac": "ffffffff-af0e-5497-ffff-ffffef05ac4a",
            "model": "MI 8 UD",
            "org": "transocks_mix",
            "package_name": "com.fobwifi.normal",
            "realname": True,
            "uuid": "d701807ce7cf744b05c2746acb40d1d6",
            "width_height": "1080x2115"
        }
        
        # 请求头
        self.headers = {
            "Host": "abscf2.fobwifi.com",
            "authorization": f"Bearer {self.token}",
            "content-type": "application/json; charset=UTF-8",
            "accept-encoding": "gzip",
            "user-agent": "okhttp/4.11.0"
        }
    
    def show_local_user_info(self):
        """显示本地用户信息"""
        print("="*60)
        print("本地用户信息")
        print("="*60)
        print(f"用户ID: {self.user_info['user_id']}")
        print(f"用户昵称: {self.user_info['nick']}")
        print(f"是否Pro用户: {self.user_info['is_pro_user']}")
        print(f"默认协议: {self.user_info['default_protocol']}")
        print(f"账号状态: {'正常' if not self.user_info['expired'] else '已过期'}")
        print(f"过期时间: {self.user_info['expire_at']}")
        print(f"是否已购买: {self.user_info['purchased']}")
        print(f"免广告: {self.user_info['ads_free']}")
        print("="*60)
    
    def generate_ss_link(self, ss_conf, label):
        """生成标准的 SS 链接
        
        Args:
            ss_conf: 节点配置信息
            label: 节点标签（数字）
            
        Returns:
            完整的 SS 链接字符串
        """
        method = ss_conf.get('method', '')
        password = ss_conf.get('password', '')
        server = ss_conf.get('server', '')
        port = ss_conf.get('port', '')
        
        # 拼接加密方式和密码
        auth_string = f"{method}:{password}"
        
        # 进行 URL-safe Base64 编码（不带换行）
        auth_bytes = auth_string.encode('utf-8')
        base64_encoded = base64.urlsafe_b64encode(auth_bytes).decode('utf-8')
        # 移除可能的填充符（某些实现不需要）
        base64_encoded = base64_encoded.rstrip('=')
        
        # 拼接完整的 SS 链接
        ss_link = f"ss://{base64_encoded}@{server}:{port}#{label}"
        
        return ss_link
    
    def __del__(self):
        """清理HTTP/2客户端"""
        if hasattr(self, 'http2_client') and self.http2_client:
            self.http2_client.close()
    
    def get_node(self, line_id=925):
        """获取指定线路的节点信息"""
        print("="*60)
        print(f"正在获取线路节点 (ID: {line_id})")
        print("="*60)
        
        # 直接使用POST请求
        return self.get_node_post(line_id)
    
    def get_node_post(self, line_id=925):
        """使用POST方式获取节点"""
        url = f"{self.base_url}/api/2/line/connect/{line_id}"
        
        # 构造请求体（与抓包数据完全一致）
        payload = {
            "available_proto": ["SS", "Trojan", "GTS"],
            "methods": ["chacha20-ietf-poly1305"],
            "proto": "SS",
            "app_version": "4.3.2",
            "channel": "google",
            "device": "Android",
            "langue": "zh",
            "mac": "ffffffff-af0e-5497-ffff-ffffef05ac4a",
            "model": "MI 8 UD",
            "org": "transocks_mix",
            "package_name": "com.fobwifi.normal",
            "realname": True,
            "uuid": "d701807ce7cf744b05c2746acb40d1d6",
            "width_height": "1080x2115"
        }
        
        try:
            # 打印请求头和请求体
            print("\n请求头:")
            print(json.dumps(self.headers, indent=2, ensure_ascii=False))
            print("\n请求体:")
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            
            # 使用HTTP/2客户端
            if self.http2_client:
                response = self.http2_client.post(url, headers=self.headers, json=payload)
                print(f"\n✓ 使用HTTP/2协议")
            else:
                response = requests.post(url, headers=self.headers, json=payload, verify=False)
                print(f"\n⚠ 使用HTTP/1.1协议")
            print(f"POST请求URL: {url}")
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
                
                if data.get("code") == 0 and data.get("status") == "ok":
                    config = data.get("config", {})
                    ss_conf = config.get("SSConf", {})
                    
                    if ss_conf:
                        print(f"\n✓ 成功获取节点信息:")
                        print(f"  服务器: {ss_conf.get('server')}")
                        print(f"  端口: {ss_conf.get('port')}")
                        print(f"  密码: {ss_conf.get('password')}")
                        print(f"  加密方式: {ss_conf.get('method')}")
                        
                        # 生成 SS 链接
                        ss_link = self.generate_ss_link(ss_conf, line_id)
                        print(f"\n✓ SS链接已生成:")
                        print(f"  {ss_link}")
                        
                        # 写入剪贴板
                        if CLIPBOARD_AVAILABLE:
                            try:
                                pyperclip.copy(ss_link)
                                print(f"\n✓ SS链接已复制到剪贴板")
                            except Exception as e:
                                print(f"\n✗ 复制到剪贴板失败: {str(e)}")
                        
                        return ss_conf
                
                print(f"✗ 获取节点失败: {data}")
                return None
            else:
                print(f"✗ POST请求失败，状态码: {response.status_code}")
                print(f"响应内容: {response.text}")
                return None
                
        except Exception as e:
            print(f"✗ POST异常: {str(e)}")
            return None
    
    def test_node(self, ss_conf):
        """测试节点连接"""
        print("\n" + "="*60)
        print("开始测试节点")
        print("="*60)
        
        server = ss_conf.get("server")
        port = ss_conf.get("port")
        password = ss_conf.get("password")
        method = ss_conf.get("method")
        
        print(f"节点信息: {server}:{port}")
        print(f"加密方式: {method}")
        
        start_time = time.time()
        
        # 1. DNS解析测试
        print("\n[1] DNS解析测试...")
        dns_start = time.time()
        try:
            ip = socket.gethostbyname(server)
            dns_duration = int((time.time() - dns_start) * 1000)
            print(f"✓ DNS解析成功: {server} -> {ip}")
            print(f"✓ DNS耗时: {dns_duration}ms")
            dns_success = True
        except Exception as e:
            dns_duration = int((time.time() - dns_start) * 1000)
            print(f"✗ DNS解析失败: {str(e)}")
            dns_success = False
        
        # 2. TCP连接测试
        print("\n[2] TCP连接测试...")
        tcp_start = time.time()
        tcp_success = False
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex((server, port))
            tcp_duration = int((time.time() - tcp_start) * 1000)
            sock.close()
            
            if result == 0:
                print(f"✓ TCP连接成功: {server}:{port}")
                print(f"✓ 连接耗时: {tcp_duration}ms")
                tcp_success = True
            else:
                print(f"✗ TCP连接失败: 错误码 {result}")
        except Exception as e:
            tcp_duration = int((time.time() - tcp_start) * 1000)
            print(f"✗ TCP连接异常: {str(e)}")
        
        # 3. 总结
        total_duration = int((time.time() - start_time) * 1000)
        print(f"\n总测试耗时: {total_duration}ms")
        
        if dns_success and tcp_success:
            print("\n✓ 节点测试通过，节点可用！")
            return True
        else:
            print("\n✗ 节点测试失败，节点可能不可用")
            return False
    
    def run(self, line_id=925):
        """执行完整流程"""
        print("\n" + "★"*60)
        print("节点获取与测试")
        print("★"*60)
        print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # 第一步：显示本地用户信息
        self.show_local_user_info()
        
        time.sleep(0.5)
        
        # 第二步：获取节点
        print("\n")
        ss_conf = self.get_node(line_id)
        
        if not ss_conf:
            print("\n✗ 流程终止：节点获取失败")
            return False
        
        time.sleep(1)
        
        # 测试节点
        success = self.test_node(ss_conf)
        
        print("\n" + "★"*60)
        print("流程执行完毕！")
        print("★"*60)
        
        return success


if __name__ == "__main__":
    tester = NodeTester()
    tester.run(line_id=925)

