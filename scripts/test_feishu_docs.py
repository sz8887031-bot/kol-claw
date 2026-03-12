#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书文档管理功能测试
测试飞书API的文档相关功能
"""

import requests
import json
import os
from feishu_config import get_feishu_config

class FeishuDocManager:
    """飞书文档管理器"""

    def __init__(self):
        # 从项目配置加载
        config = get_feishu_config()
        self.app_id = config.app_id
        self.app_secret = config.app_secret
        self.tenant_access_token = None

    def get_tenant_access_token(self):
        """获取tenant_access_token"""
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json"}
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }

        response = requests.post(url, headers=headers, json=data)
        result = response.json()

        if result.get('code') == 0:
            self.tenant_access_token = result['tenant_access_token']
            return True
        else:
            print(f"❌ 获取token失败: {result}")
            return False

    def search_user(self, query):
        """搜索用户"""
        if not self.tenant_access_token:
            if not self.get_tenant_access_token():
                return None

        url = "https://open.feishu.cn/open-apis/contact/v3/users/batch_get_id"
        headers = {
            "Authorization": f"Bearer {self.tenant_access_token}",
            "Content-Type": "application/json"
        }
        params = {
            "user_id_type": "user_id",
            "emails": query if '@' in query else None,
            "mobiles": query if query.startswith('+') else None
        }

        response = requests.get(url, headers=headers, params=params)
        return response.json()

    def list_docs(self, folder_token=None):
        """列出文档"""
        if not self.tenant_access_token:
            if not self.get_tenant_access_token():
                return None

        url = "https://open.feishu.cn/open-apis/drive/v1/files"
        headers = {
            "Authorization": f"Bearer {self.tenant_access_token}"
        }
        params = {
            "page_size": 10,
            "folder_token": folder_token
        }

        response = requests.get(url, headers=headers, params=params)
        return response.json()

    def get_doc_content(self, doc_token):
        """获取文档内容"""
        if not self.tenant_access_token:
            if not self.get_tenant_access_token():
                return None

        url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/raw_content"
        headers = {
            "Authorization": f"Bearer {self.tenant_access_token}"
        }

        response = requests.get(url, headers=headers)
        return response.json()

    def send_message(self, user_id, content):
        """发送消息"""
        if not self.tenant_access_token:
            if not self.get_tenant_access_token():
                return None

        url = "https://open.feishu.cn/open-apis/im/v1/messages"
        headers = {
            "Authorization": f"Bearer {self.tenant_access_token}",
            "Content-Type": "application/json"
        }
        params = {
            "receive_id_type": "user_id"
        }
        data = {
            "receive_id": user_id,
            "msg_type": "text",
            "content": json.dumps({"text": content})
        }

        response = requests.post(url, headers=headers, params=params, json=data)
        return response.json()


def main():
    """测试飞书文档管理功能"""
    print("=" * 80)
    print("飞书文档管理功能测试")
    print("=" * 80)

    manager = FeishuDocManager()

    # 1. 测试获取token
    print("\n1. 测试获取tenant_access_token...")
    if manager.get_tenant_access_token():
        print(f"✅ Token获取成功: {manager.tenant_access_token[:20]}...")
    else:
        print("❌ Token获取失败")
        return

    # 2. 测试搜索用户
    print("\n2. 测试搜索用户...")
    result = manager.search_user("yuan.zhang@hiretool.cn")
    if result and result.get('code') == 0:
        print("✅ 用户搜索成功")
        print(f"   结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
    else:
        print(f"⚠️  用户搜索返回: {result}")

    # 3. 测试列出文档
    print("\n3. 测试列出文档...")
    result = manager.list_docs()
    if result and result.get('code') == 0:
        print("✅ 文档列表获取成功")
        files = result.get('data', {}).get('files', [])
        print(f"   找到 {len(files)} 个文件/文件夹")
        for file in files[:3]:
            print(f"   - {file.get('name')} ({file.get('type')})")
    else:
        print(f"⚠️  文档列表返回: {result}")

    # 4. 测试发送消息（可选，注释掉避免打扰）
    print("\n4. 测试发送消息...")
    print("   (已跳过，避免发送测试消息)")
    # result = manager.send_message("your_feishu_user_id", "这是一条测试消息")
    # if result and result.get('code') == 0:
    #     print("✅ 消息发送成功")
    # else:
    #     print(f"❌ 消息发送失败: {result}")

    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == '__main__':
    main()
