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
        self.configs = []
    
    # -------------------------
    # Shadowsocks (SS) 生成
    # -------------------------
    def generate_ss_link(self, ss_conf, label):
        """
        生成标准 SS 链接（兼容主流客户端）
        - 正确：整体对 method:password@host:port 做标准 Base64（保留=）
        - 格式：ss://BASE64(method:password@host:port)#TAG
        """
        method = ss_conf.get('method', '')
        password = ss_conf.get('password', '')
        server = ss_conf.get('server', '')
        port = ss_conf.get('port', '')

        if not all([method, password, server, port]):
            print(f"  > 警告: SS 节点信息不完整，跳过生成。 {ss_conf}")
            return None

        auth_string = f"{method}:{password}@{server}:{port}"
        base64_encoded = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
        return f"ss://{base64_encoded}#{label}"

    # -------------------------
    # VMess 生成
    # -------------------------
    def generate_vmess_link(self, vmess_conf, label):
        """
        生成 VMess 链接（vmess:// BASE64(JSON)）
        预期字段示例：
        {
            "server": "host",
            "port": 443,
            "id": "uuid",
            "aid": 0,
            "scy": "auto",
            "net": "ws",
            "type": "none",
            "host": "sni.or.ws-host",
            "path": "/path",
            "tls": "tls" 或 "",
            "sni": "sni.domain"
        }
        """
        server = vmess_conf.get('server')
        port = vmess_conf.get('port')
        uuid = vmess_conf.get('id') or vmess_conf.get('uuid')
        aid = vmess_conf.get('aid', 0)
        scy = vmess_conf.get('scy', 'auto')
        net = vmess_conf.get('net', 'tcp')
        type_ = vmess_conf.get('type', 'none')
        host = vmess_conf.get('host', '')
        path = vmess_conf.get('path', '')
        tls = vmess_conf.get('tls', '')
        sni = vmess_conf.get('sni', '')

        if not all([server, port, uuid]):
            print(f"  > 警告: VMess 节点信息不完整，跳过生成。 {vmess_conf}")
            return None

        vmess_json = {
            "v": "2",
            "ps": label,
            "add": server,
            "port": str(port),
            "id": uuid,
            "aid": str(aid),
            "scy": scy,
            "net": net,
            "type": type_,
            "host": host,
            "path": path,
            "tls": "tls" if str(tls).lower() in ["tls", "true", "1"] else "",
            "sni": sni
        }
        encoded = base64.b64encode(json.dumps(vmess_json, separators=(',', ':')).encode('utf-8')).decode('utf-8')
        return f"vmess://{encoded}"

    # -------------------------
    # VLESS 生成
    # -------------------------
    def generate_vless_link(self, vless_conf, label):
        """
        生成 VLESS 链接（URL 格式）
        格式：vless://uuid@host:port?encryption=none&security=tls&sni=xxx&fp=chrome&type=ws&host=xxx&path=/xxx#TAG
        """
        server = vless_conf.get('server')
        port = vless_conf.get('port')
        uuid = vless_conf.get('id') or vless_conf.get('uuid')
        flow = vless_conf.get('flow', '')
        net = vless_conf.get('net', 'tcp')
        host = vless_conf.get('host', '')
        path = vless_conf.get('path', '')
        tls = vless_conf.get('tls', '')
        sni = vless_conf.get('sni', '')
        fp = vless_conf.get('fp', '')
        alpn = vless_conf.get('alpn', '')

        if not all([server, port, uuid]):
            print(f"  > 警告: VLESS 节点信息不完整，跳过生成。 {vless_conf}")
            return None

        params = []
        params.append("encryption=none")
        if flow:
            params.append(f"flow={flow}")
        if str(tls).lower() in ["tls", "true", "1"]:
            params.append("security=tls")
            if sni:
                params.append(f"sni={sni}")
            if fp:
                params.append(f"fp={fp}")
            if alpn:
                params.append(f"alpn={alpn}")
        else:
            params.append("security=none")

        # 传输层
        if net in ["ws", "grpc", "tcp", "http"]:
            params.append(f"type={net}")
        if host:
            params.append(f"host={host}")
        if path:
            params.append(f"path={path}")

        query = "&".join(params)
        return f"vless://{uuid}@{server}:{port}?{query}#{label}"

    # -------------------------
    # Trojan 生成
    # -------------------------
    def generate_trojan_link(self, trojan_conf, label):
        """
        生成 Trojan 链接
        格式：trojan://password@host:port?security=tls&sni=xxx#TAG
        """
        server = trojan_conf.get('server')
        port = trojan_conf.get('port')
        password = trojan_conf.get('password')
        sni = trojan_conf.get('sni', '')
        tls = trojan_conf.get('tls', 'tls')

        if not all([server, port, password]):
            print(f"  > 警告: Trojan 节点信息不完整，跳过生成。 {trojan_conf}")
            return None

        params = []
        if str(tls).lower() in ["tls", "true", "1"]:
            params.append("security=tls")
        else:
            params.append("security=none")
        if sni:
            params.append(f"sni={sni}")

        query = "&".join(params) if params else ""
        suffix = f"?{query}" if query else ""
        return f"trojan://{password}@{server}:{port}{suffix}#{label}"

    # -------------------------
    # Clash/Mihomo 生成
    # -------------------------
    def to_clash_proxy(self, proto, conf, name):
        """
        生成 Clash 代理条目（尽量匹配字段）
        """
        if proto == "SS":
            return {
                "name": name,
                "type": "ss",
                "server": conf.get("server"),
                "port": int(conf.get("port")),
                "cipher": conf.get("method"),
                "password": conf.get("password")
            }
        if proto == "VMess":
            tls = str(conf.get("tls", "")).lower() in ["tls", "true", "1"]
            entry = {
                "name": name,
                "type": "vmess",
                "server": conf.get("server"),
                "port": int(conf.get("port")),
                "uuid": conf.get("id") or conf.get("uuid"),
                "alterId": int(conf.get("aid", 0)),
                "cipher": conf.get("scy", "auto"),
                "tls": tls
            }
            net = conf.get("net", "tcp")
            entry["network"] = net
            if net == "ws":
                entry["ws-opts"] = {
                    "path": conf.get("path", ""),
                    "headers": {"Host": conf.get("host", "")} if conf.get("host") else {}
                }
            if conf.get("sni"):
                entry["servername"] = conf.get("sni")
            return entry
        if proto == "VLESS":
            tls = str(conf.get("tls", "")).lower() in ["tls", "true", "1"]
            entry = {
                "name": name,
                "type": "vless",
                "server": conf.get("server"),
                "port": int(conf.get("port")),
                "uuid": conf.get("id") or conf.get("uuid"),
                "tls": tls,
                "udp": True
            }
            net = conf.get("net", "tcp")
            entry["network"] = net
            if net == "ws":
                entry["ws-opts"] = {
                    "path": conf.get("path", ""),
                    "headers": {"Host": conf.get("host", "")} if conf.get("host") else {}
                }
            if conf.get("sni"):
                entry["servername"] = conf.get("sni")
            return entry
        if proto == "Trojan":
            tls = str(conf.get("tls", "tls")).lower() in ["tls", "true", "1"]
            entry = {
                "name": name,
                "type": "trojan",
                "server": conf.get("server"),
                "port": int(conf.get("port")),
                "password": conf.get("password"),
                "tls": tls
            }
            if conf.get("sni"):
                entry["sni"] = conf.get("sni")
            return entry
        return None

    # -------------------------
    # 获取节点
    # -------------------------
    def step1_get_line_nodes(self):
        print("\n" + "="*60)
        print("第一步：获取线路节点")
        print("="*60)
        
        url = f"{self.base_url}/api/2/line/connectmultiple"
        
        payload = {
            "available_proto": ["SS", "Trojan", "GTS", "VMess", "VLESS"],
            "lineCount": 2,
            "methods": ["chacha20-ietf-poly1305", "aes-256-gcm"],
            "proto": "SS"  # 只是默认，不限制返回
        }
        payload.update(self.device_params)
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, verify=False, timeout=15)
            print(f"请求URL: {url}")
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"响应数据结构预览 keys: {list(data.keys())}")
                
                if data.get("code") == 0 and data.get("status", "").lower() == "ok":
                    self.configs = data.get("configs", [])
                    print(f"\n✓ 成功获取 {len(self.configs)} 个节点配置")
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

    # -------------------------
    # 主流程
    # -------------------------
    def run(self):
        print("\n" + "★"*60)
        print("★"*60)
        print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if not self.step1_get_line_nodes():
            print("\n✗ 流程终止：线路节点获取失败")
            return False
        
        if not self.configs:
            print("\n✗ 流程终止：没有可用的节点")
            return False
        
        time.sleep(1)
        
        print("\n" + "="*60)
        print("生成多协议订阅链接")
        print("="*60)
        
        all_links = []
        clash_proxies = []

        # 遍历配置，识别不同协议
        for idx, config in enumerate(self.configs):
            label = f"VIP{idx+1}"
            print(f"\n[节点 {idx+1}/{len(self.configs)}] 标记: {label}")

            # SS
            if "SSConf" in config and isinstance(config["SSConf"], dict):
                ss_link = self.generate_ss_link(config["SSConf"], label)
                if ss_link:
                    print(f"  SS: {ss_link}")
                    all_links.append(ss_link)
                    cp = self.to_clash_proxy("SS", config["SSConf"], f"{label}-SS")
                    if cp: clash_proxies.append(cp)

            # VMess
            if "VMessConf" in config and isinstance(config["VMessConf"], dict):
                vmess_link = self.generate_vmess_link(config["VMessConf"], label)
                if vmess_link:
                    print(f"  VMess: {vmess_link}")
                    all_links.append(vmess_link)
                    cp = self.to_clash_proxy("VMess", config["VMessConf"], f"{label}-VMess")
                    if cp: clash_proxies.append(cp)

            # VLESS
            if "VLESSConf" in config and isinstance(config["VLESSConf"], dict):
                vless_link = self.generate_vless_link(config["VLESSConf"], label)
                if vless_link:
                    print(f"  VLESS: {vless_link}")
                    all_links.append(vless_link)
                    cp = self.to_clash_proxy("VLESS", config["VLESSConf"], f"{label}-VLESS")
                    if cp: clash_proxies.append(cp)

            # Trojan
            if "TrojanConf" in config and isinstance(config["TrojanConf"], dict):
                trojan_link = self.generate_trojan_link(config["TrojanConf"], label)
                if trojan_link:
                    print(f"  Trojan: {trojan_link}")
                    all_links.append(trojan_link)
                    cp = self.to_clash_proxy("Trojan", config["TrojanConf"], f"{label}-Trojan")
                    if cp: clash_proxies.append(cp)

        # 输出文件
        out_dir = Path("docs")
        out_dir.mkdir(parents=True, exist_ok=True)

        # 1) 纯文本订阅
        plain_path = out_dir / "sub.txt"
        plain_content = "\n".join(all_links) + ("\n" if all_links else "")
        plain_path.write_text(plain_content, encoding="utf-8")
        print(f"\n✓ 纯文本订阅生成: {plain_path.resolve()}  共 {len(all_links)} 条")

        # 2) 整体 Base64 订阅（兼容部分安卓客户端）
        b64_path = out_dir / "sub_base64.txt"
        b64_content = base64.b64encode(plain_content.encode("utf-8")).decode("utf-8")
        b64_path.write_text(b64_content, encoding="utf-8")
        print(f"✓ Base64 订阅生成: {b64_path.resolve()}")

        # 3) Clash/Mihomo 订阅（proxies 列表）
        clash_path = out_dir / "clash.yaml"
        clash_yaml = self.render_clash_yaml(clash_proxies)
        clash_path.write_text(clash_yaml, encoding="utf-8")
        print(f"✓ Clash 配置生成: {clash_path.resolve()}  共 {len(clash_proxies)} 条代理")

        print("\n" + "★"*60)
        print("完整流程执行完毕！")
        print("★"*60)
        return True

    # -------------------------
    # 生成简单的 Clash YAML
    # -------------------------
    def render_clash_yaml(self, proxies):
        """
        仅生成 proxies + 一个基本的 proxy-group，便于快速导入
        """
        # 简单 YAML 序列化（避免额外依赖）
        lines = []
        lines.append("proxies:")
        for p in proxies:
            lines.append(f"  - name: {p['name']}")
            lines.append(f"    type: {p['type']}")
            lines.append(f"    server: {p['server']}")
            lines.append(f"    port: {p['port']}")
            if p["type"] == "ss":
                lines.append(f"    cipher: {p['cipher']}")
                lines.append(f"    password: {p['password']}")
            elif p["type"] == "vmess":
                lines.append(f"    uuid: {p['uuid']}")
                lines.append(f"    alterId: {p.get('alterId', 0)}")
                lines.append(f"    cipher: {p.get('cipher', 'auto')}")
                lines.append(f"    tls: {str(p.get('tls', False)).lower()}")
                lines.append(f"    network: {p.get('network', 'tcp')}")
                if p.get("servername"):
                    lines.append(f"    servername: {p['servername']}")
                if p.get("network") == "ws" and p.get("ws-opts"):
                    ws = p["ws-opts"]
                    lines.append(f"    ws-opts:")
                    if ws.get("path"):
                        lines.append(f"      path: {ws['path']}")
                    if ws.get("headers"):
                        lines.append(f"      headers:")
                        for hk, hv in ws["headers"].items():
                            lines.append(f"        {hk}: {hv}")
            elif p["type"] == "vless":
                lines.append(f"    uuid: {p['uuid']}")
                lines.append(f"    tls: {str(p.get('tls', True)).lower()}")
                lines.append(f"    udp: {str(p.get('udp', True)).lower()}")
                lines.append(f"    network: {p.get('network', 'tcp')}")
                if p.get("servername"):
                    lines.append(f"    servername: {p['servername']}")
                if p.get("network") == "ws" and p.get("ws-opts"):
                    ws = p["ws-opts"]
                    lines.append(f"    ws-opts:")
                    if ws.get("path"):
                        lines.append(f"      path: {ws['path']}")
                    if ws.get("headers"):
                        lines.append(f"      headers:")
                        for hk, hv in ws["headers"].items():
                            lines.append(f"        {hk}: {hv}")
            elif p["type"] == "trojan":
                lines.append(f"    password: {p['password']}")
                lines.append(f"    tls: {str(p.get('tls', True)).lower()}")
                if p.get("sni"):
                    lines.append(f"    sni: {p['sni']}")

        # 一个基础的组，包含所有代理
        lines.append("")
        lines.append("proxy-groups:")
        lines.append("  - name: AUTO")
        lines.append("    type: select")
        lines.append("    proxies:")
        for p in proxies:
            lines.append(f"      - {p['name']}")

        # 基本的规则区（留空由用户自行补充）
        lines.append("")
        lines.append("rules:")
        lines.append("  - MATCH, AUTO")

        return "\n".join(lines)


if __name__ == "__main__":
    simulator = GoatVPNSimulator()
    simulator.run()
