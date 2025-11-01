#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import json
import time
import base64
from datetime import datetime
from pathlib import Path

# 禁用SSL警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class GoatVPNSimulator:
    def __init__(self):
        # 基础配置
        self.base_url = "https://abscf2.fobwifi.com"
        self.token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwNzczODI1NTQsImlhdCI6MTc2MjAyMjU1NCwia2V5IjoiMUYyRTA2MUNCNjZDRTAwMFB0eHAwZk1pcVtxNDZzNzgxMjU5UFBzRnljRU1QMDZHMjdQMDcwTTU1Nzc0QjBbVyIsIm9yZyI6InRyYW5zb2Nrc19taXgiLCJ1c2VyIjp7ImlkIjoxOTM2NzUxMX19.o6U0NTej1-GNb8wPEQ5TmyXltr1yjOU2e-HFPS5Ed_o"
        
        # 设备参数（从抓包数据中提取）
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
        
        # 存储节点信息
        self.ss_configs = []
    
    def generate_ss_link(self, ss_conf, label):
        """生成标准的 SS 链接
        
        Args:
            ss_conf: 节点配置信息
            label: 节点标签
            
        Returns:
            完整的 SS 链接字符串
        """
        method = ss_conf.get('method', '')
        password = ss_conf.get('password', '')
        server = ss_conf.get('server', '')
        port = ss_conf.get('port', '')
        
        if not all([method, password, server, port]):
            print(f"  > 警告: 节点信息不完整，跳过生成。 {ss_conf}")
            return None
        
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
    
    def step1_get_line_nodes(self):
        """第一步：获取线路节点"""
        print("\n" + "="*60)
        print("第一步：获取线路节点")
        print("="*60)
        
        url = f"{self.base_url}/api/2/line/connectmultiple"
        
        # 构造请求体
        payload = {
            "available_proto": ["SS", "Trojan", "GTS"],
            "lineCount": 5,
            "methods": ["chacha20-ietf-poly1305"],
            "proto": "SS"
        }
        payload.update(self.device_params)
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, verify=False)
            print(f"请求URL: {url}")
            print(f"请求体: {json.dumps(payload, indent=2, ensure_ascii=False)}")
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
                
                if data.get("code") == 0 and data.get("status") == "ok":
                    self.ss_configs = data.get("configs", [])
                    print(f"\n✓ 成功获取 {len(self.ss_configs)} 个SS节点:")
                    for idx, config in enumerate(self.ss_configs):
                        ss_conf = config.get("SSConf", {})
                        print(f"\n  节点 {idx+1}:")
                        print(f"    服务器: {ss_conf.get('server')}")
                        print(f"    端口: {ss_conf.get('port')}")
                        print(f"    密码: {ss_conf.get('password')}")
                        print(f"    加密方式: {ss_conf.get('method')}")
                    return True
                else:
                    print(f"✗ 获取节点失败: {data}")
                    return False
            else:
                print(f"✗ 请求失败，状态码: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ 异常: {str(e)}")
            return False
    
    def run(self):
        """执行完整流程"""
        print("\n" + "★"*60)
        print("★"*60)
        print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 第一步：获取线路节点
        if not self.step1_get_line_nodes():
            print("\n✗ 流程终止：线路节点获取失败")
            return False
        
        if not self.ss_configs:
            print("\n✗ 流程终止：没有可用的SS节点")
            return False
        
        time.sleep(1)
        
        # 生成所有节点的SS链接
        print("\n" + "="*60)
        print("生成SS链接")
        print("="*60)
        
        all_ss_links = []
        
        for idx, config in enumerate(self.ss_configs):
            ss_conf = config.get("SSConf", {})
            
            print(f"\n[节点 {idx+1}/{len(self.ss_configs)}]")
            print(f"  服务器: {ss_conf.get('server')}")
            print(f"  端口: {ss_conf.get('port')}")
            print(f"  加密方式: {ss_conf.get('method')}")
            
            # 生成SS链接
            label = f"VIP{idx+1}"
            ss_link = self.generate_ss_link(ss_conf, label)
            if ss_link:
                print(f"  SS链接: {ss_link}")
                all_ss_links.append(ss_link)
        
        # 写入订阅文件
        if all_ss_links:
            content = "\n".join(all_ss_links)
            
            out_path = Path("docs/sub.txt")
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(content, encoding="utf-8")
            
            print(f"\n✓✓✓ 订阅文件已成功生成! ✓✓✓")
            print(f"   文件路径: {out_path.resolve()}")
            print(f"   文件内容 (共 {len(all_ss_links)} 个节点):")
            print(content)
        else:
            print("\n✗ 未能生成任何SS链接")
        
        print("\n" + "★"*60)
        print("完整流程执行完毕！")
        print("★"*60)
        return True


if __name__ == "__main__":
    simulator = GoatVPNSimulator()
    simulator.run()

