#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import base64
from pathlib import Path  # 修正：添加缺失的导入

# 禁用SSL警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 尝试导入httpx以支持HTTP/2
try:
    import httpx
    HTTP2_AVAILABLE = True
except ImportError:
    HTTP2_AVAILABLE = False
    print("⚠ 警告: httpx未安装，将使用HTTP/1.1")
    print("  在GitHub Actions中, 请确保 requirements.txt 包含 httpx[http2]")


class NodeTester:
    def __init__(self):
        # 基础配置 (不可更改)
        self.base_url = "https://abscf2.fobwifi.com"
        self.token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwNzczMDE5NzUsImlhdCI6MTc2MTk0MTk3NSwia2V5IjoiMUYyQ0QyQkEyRTkyOTAwMFl3bzFcXFM0UzJZaXhwNTRhQ3I5cTM4emlHN3h0QW1RWkE5aFo4OVQ1VjlbenJjYnciLCJvcmciOiJ0cmFuc29ja3NfbWl4IiwidXNlciI6eyJpZCI6MTk4MjQ5MTJ9fQ.OYB_OY7vbbNarMgi5LcvHKi03SPhSrHwzoYD0rOK8kU"
        
        # HTTP/2客户端
        if HTTP2_AVAILABLE:
            self.http2_client = httpx.Client(http2=True, verify=False)
        else:
            self.http2_client = None
        
        # 请求头 (不可更改)
        self.headers = {
            "Host": "abscf2.fobwifi.com",
            "authorization": f"Bearer {self.token}",
            "content-type": "application/json; charset=UTF-8",
            "accept-encoding": "gzip",
            "user-agent": "okhttp/4.11.0"
        }
    
    def generate_ss_link(self, ss_conf, label):
        """
        生成标准的 SS 链接
        (保留, 核心功能需要)
        """
        method = ss_conf.get('method', '')
        password = ss_conf.get('password', '')
        server = ss_conf.get('server', '')
        port = ss_conf.get('port', '')
        
        auth_string = f"{method}:{password}"
        
        auth_bytes = auth_string.encode('utf-8')
        base64_encoded = base64.urlsafe_b64encode(auth_bytes).decode('utf-8')
        base64_encoded = base64_encoded.rstrip('=')
        
        ss_link = f"ss://{base64_encoded}@{server}:{port}#{label}"
        
        return ss_link
    
    def __del__(self):
        """清理HTTP/2客户端"""
        if hasattr(self, 'http2_client') and self.http2_client:
            self.http2_client.close()
    
    def get_node_and_write_file(self, line_id=925):
        """
        核心功能：获取节点、生成SS链接、并写入txt文件
        (此函数合并了原版的 get_node_post 和文件写入逻辑)
        """
        url = f"{self.base_url}/api/2/line/connect/{line_id}"
        
        # 请求体 (不可更改, 与原版一致)
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
        
        print("="*60)
        print(f"正在获取线路 {line_id} 的节点...")
        
        try:
            # 使用HTTP/2客户端 (如果可用)
            if self.http2_client:
                response = self.http2_client.post(url, headers=self.headers, json=payload)
                print(f"✓ 使用HTTP/2协议 (POST {url})")
            else:
                response = requests.post(url, headers=self.headers, json=payload, verify=False)
                print(f"✓ 使用HTTP/1.1协议 (POST {url})")
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("code") == 0 and data.get("status") == "ok":
                    config = data.get("config", {})
                    ss_conf = config.get("SSConf", {})
                    
                    if ss_conf:
                        print(f"✓ 成功获取节点信息 (Server: {ss_conf.get('server')})")
                        
                        # 1. 生成 SS 链接
                        ss_link = self.generate_ss_link(ss_conf, line_id)
                        
                        # 2. 将SS链接本身进行Base64编码 (作为订阅内容)
                        content = base64.b64encode(ss_link.encode('utf-8')).decode('utf-8')
                        
                        # 3. 写入文件
                        out_path = Path("docs/sub.txt")
                        out_path.parent.mkdir(parents=True, exist_ok=True)
                        out_path.write_text(content, encoding="utf-8")
                        
                        print(f"\n✓✓✓ 订阅文件已成功生成! ✓✓✓")
                        print(f"   文件路径: {out_path.resolve()}")
                        return True
                    else:
                        print(f"✗ 获取节点失败: 响应中未包含 'SSConf'。")
                        print(f"  响应数据: {data}")
                        return False
                else:
                    print(f"✗ API返回错误: {data.get('status', 'N/A')}")
                    print(f"  响应数据: {data}")
                    return False
            else:
                print(f"✗ POST请求失败")
                print(f"  响应内容: {response.text}")
                return False
        
        except Exception as e:
            print(f"✗ 请求发生异常: {str(e)}")
            return False
        finally:
            print("="*60)


if __name__ == "__main__":
    # 确保 httpx 已安装 (在GitHub Actions中需要)
    if not HTTP2_AVAILABLE:
        print("错误: 核心依赖 'httpx' 未安装。")
        print("请在 requirements.txt 或 workflow 中添加 'httpx[http2]'。")
        exit(1) # 在CI环境中以失败退出
        
    tester = NodeTester()
    
    # 直接调用核心函数
    success = tester.get_node_and_write_file(line_id=925)
    
    if not success:
        print("流程执行失败。")
        # 在 CI/CD 环境中，用非0退出码表示失败
        exit(1)
