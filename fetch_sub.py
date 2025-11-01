#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import base64
from pathlib import Path
import json # 导入json库以便在出错时打印

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
        """
        method = ss_conf.get('method', '')
        password = ss_conf.get('password', '')
        server = ss_conf.get('server', '')
        port = ss_conf.get('port', '')
        
        if not all([method, password, server, port]):
            print(f"  > 警告: 节点信息不完整，跳过生成。 {ss_conf}")
            return None

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
    
    def get_multiple_nodes_and_write_file(self):
        """
        核心功能：获取多个节点、生成SS链接、并写入txt文件
        """
        url = f"{self.base_url}/api/2/line/connectmultiple"
        
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
        print(f"正在从 {url} 获取多个节点...")
        
        try:
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
                    
                    node_list = data.get("configs", [])
                    
                    if not isinstance(node_list, list) or not node_list:
                        print(f"✗ 获取节点失败: 响应中的 'configs' 不是一个列表或为空。")
                        print(f"  响应数据: {json.dumps(data, indent=2)}")
                        return False
                    
                    print(f"✓ 成功获取到 {len(node_list)} 个节点配置，正在循环解析...")
                    
                    all_ss_links = []
                    
                    # 【重点】使用 enumerate 进行循环, 可以同时获取索引和内容
                    for i, node_config in enumerate(node_list):
                        ss_conf = node_config.get("SSConf", {})
                        label = ss_conf.get("server", f"Unknown-Label-{i+1}") 
                        
                        if ss_conf:
                            # 【新】增加了更清晰的打印，证明在处理多个节点
                            print(f"  > [正在处理第 {i+1} / {len(node_list)} 个节点] 服务器: {ss_conf.get('server')}")
                            ss_link = self.generate_ss_link(ss_conf, label)
                            if ss_link:
                                all_ss_links.append(ss_link)
                        else:
                            print(f"  > 警告: 列表中的一个项目缺少 'SSConf'。")

                    if not all_ss_links:
                        print("✗ 解析失败：未能在任何节点配置中找到有效的 'SSConf'。")
                        return False

                    # 将所有链接用换行符连接成一个字符串
                    content = "\n".join(all_ss_links)
                    
                    out_path = Path("docs/sub.txt")
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    out_path.write_text(content, encoding="utf-8")
                    
                    print(f"\n✓✓✓ 订阅文件已成功生成! ✓✓✓")
                    print(f"   文件路径: {out_path.resolve()}")
                    print(f"   文件内容 (共 {len(all_ss_links)} 个节点):")
                    print(content) # 打印出所有链接
                    return True
                
                else:
                    print(f"✗ API返回错误: {data.get('status', 'N/A')}")
                    print(f"  响应数据: {json.dumps(data, indent=2)}")
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
    if not HTTP2_AVAILABLE:
        print("警告: 推荐安装 'httpx[http2]' 以获得更好的性能。")
        print("   pip install httpx[http2]")
        
    tester = NodeTester()
    success = tester.get_multiple_nodes_and_write_file()
    
    if not success:
        print("流程执行失败。")
        exit(1)
