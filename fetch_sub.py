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
        self.token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwNzc0OTQ3NTIsImlhdCI6MTc2MjEzNDc1Miwia2V5IjoiMUYyRkIyMUNBMThFODAwMDM3Y0FyODFscl1SQUx5VHZBOF1OXzJXM2hzRzFyNmtyOXZCSDlvQXhsYVRpOG1QNiIsIm9yZyI6InRyYW5zb2Nrc19taXgiLCJ1c2VyIjp7ImlkIjoxOTgzMzk4OX19.gIt9CjQuz6NIBDLTkS3DfhSUGC9LreVceglU9FTIYLM"
        
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
        """生成标准的 SS 链接"""
        method = ss_conf.get('method', '')
        password = ss_conf.get('password', '')
        server = ss_conf.get('server', '')
        port = ss_conf.get('port', '')
        
        if not all([method, password, server, port]):
            print(f"  > 警告: 节点信息不完整，跳过生成。 {ss_conf}")
            return None
        
        # 拼接加密方式和密码
        auth_string = f"{method}:{password}"
        
        # 使用标准 Base64 编码（保留填充符）
        auth_bytes = auth_string.encode('utf-8')
        base64_encoded = base64.b64encode(auth_bytes).decode('utf-8')
        
        # 拼接完整的 SS 链接
        ss_link = f"ss://{base64_encoded}@{server}:{port}#{label}"
        
        return ss_link
    
    def step1_get_line_nodes(self):
        """第一步：获取线路节点"""
        print("\n" + "="*60)
        print("第一步：获取线路节点")
        print("="*60)
        
        url = f"{self.base_url}/api/2/line/connectmultiple"
        
        payload = {
            "available_proto": ["SS", "Trojan", "GTS"],
            "lineCount": 2,
            "methods": ["chacha20-ietf-poly1305"],
            "proto": "SS"
        }
        payload.update(self.device_params)
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, verify=False)
            print(f"请求URL: {url}")
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 0 and data.get("status") == "ok":
                    self.ss_configs = data.get("configs", [])
                    print(f"\n✓ 成功获取 {len(self.ss_configs)} 个SS节点")
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
        
        if not self.step1_get_line_nodes():
            print("\n✗ 流程终止：线路节点获取失败")
            return False
        
        if not self.ss_configs:
            print("\n✗ 流程终止：没有可用的SS节点")
            return False
        
        time.sleep(1)
        
        print("\n" + "="*60)
        print("生成SS链接")
        print("="*60)
        
        all_ss_links = []
        all_json_nodes = []
        
        for idx, config in enumerate(self.ss_configs):
            ss_conf = config.get("SSConf", {})
            label = f"VIP{idx+1}"
            ss_link = self.generate_ss_link(ss_conf, label)
            if ss_link:
                print(f"  SS链接: {ss_link}")
                all_ss_links.append(ss_link)
                # 保存为 JSON 节点
                node_info = {
                    "server": ss_conf.get("server"),
                    "port": ss_conf.get("port"),
                    "method": ss_conf.get("method"),
                    "password": ss_conf.get("password"),
                    "label": label,
                    "link": ss_link
                }
                all_json_nodes.append(node_info)
        
        # 写入订阅文件
        out_dir = Path("docs")
        out_dir.mkdir(parents=True, exist_ok=True)
        
        if all_ss_links:
            # 纯文本
            out_path_txt = out_dir / "sub.txt"
            out_path_txt.write_text("\n".join(all_ss_links), encoding="utf-8")
            print(f"\n✓ 订阅文件已生成: {out_path_txt.resolve()}")
            
            # JSON 文件
            out_path_json = out_dir / "sub.json"
            out_path_json.write_text(json.dumps(all_json_nodes, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"✓ JSON 文件已生成: {out_path_json.resolve()}")
        else:
            print("\n✗ 未能生成任何SS链接")
        
        print("\n" + "★"*60)
        print("完整流程执行完毕！")
        print("★"*60)
        return True


if __name__ == "__main__":
    simulator = GoatVPNSimulator()
    simulator.run()
