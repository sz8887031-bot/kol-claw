#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书权限管理 - 正确的API调用方式
参考飞书官方文档
"""

import requests
import json
import os
from feishu_config import get_feishu_config


class FeishuPermissionManager:
    """飞书权限管理器"""

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
        data = {"app_id": self.app_id, "app_secret": self.app_secret}

        response = requests.post(url, headers=headers, json=data)
        result = response.json()

        if result.get('code') == 0:
            self.tenant_access_token = result['tenant_access_token']
            return True
        return False

    def add_member_v2(self, token, member_id, member_type="userid", perm="edit"):
        """
        添加协作者 - 使用正确的API参数

        参数:
        - token: 文档/多维表格的token
        - member_id: 成员ID (根据member_type不同而不同)
        - member_type: 成员类型
          * userid: 用户ID
          * openid: Open ID
          * email: 邮箱
          * openchat: 群聊ID
        - perm: 权限
          * view: 可阅读
          * edit: 可编辑
          * full_access: 完全访问
        """
        if not self.tenant_access_token:
            if not self.get_tenant_access_token():
                return False

        url = f"https://open.feishu.cn/open-apis/drive/v1/permissions/{token}/members"
        headers = {
            "Authorization": f"Bearer {self.tenant_access_token}",
            "Content-Type": "application/json"
        }

        # 根据飞书文档，正确的参数格式
        # type表示成员类型，不是文档类型
        data = {
            "member_type": member_type,
            "member_id": member_id,
            "perm": perm,
            "type": "user"  # 成员类型：user, chat, department, group等
        }

        print(f"\n📤 发送请求:")
        print(f"   URL: {url}")
        print(f"   数据: {json.dumps(data, ensure_ascii=False, indent=2)}")

        response = requests.post(url, headers=headers, json=data)
        result = response.json()

        print(f"\n📥 响应结果:")
        print(f"   {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get('code') == 0:
            print(f"\n✅ 成功添加协作者!")
            print(f"   成员: {member_id}")
            print(f"   权限: {perm}")
            return True
        else:
            print(f"\n❌ 添加失败")
            print(f"   错误码: {result.get('code')}")
            print(f"   错误信息: {result.get('msg')}")
            if 'error' in result:
                print(f"   详细错误: {result['error']}")
            return False

    def transfer_owner(self, token, new_owner_id, member_type="userid"):
        """
        转移所有者
        """
        if not self.tenant_access_token:
            if not self.get_tenant_access_token():
                return False

        url = f"https://open.feishu.cn/open-apis/drive/v1/permissions/{token}/members/transfer_owner"
        headers = {
            "Authorization": f"Bearer {self.tenant_access_token}",
            "Content-Type": "application/json"
        }

        data = {
            "member_type": member_type,
            "member_id": new_owner_id,
            "type": "user"
        }

        print(f"\n📤 转移所有者:")
        print(f"   新所有者: {new_owner_id}")

        response = requests.post(url, headers=headers, json=data)
        result = response.json()

        print(f"\n📥 响应: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get('code') == 0:
            print(f"✅ 所有者转移成功!")
            return True
        else:
            print(f"❌ 转移失败: {result.get('msg')}")
            return False


def main():
    """主函数"""
    print("=" * 80)
    print("飞书多维表格权限设置")
    print("=" * 80)

    # 多维表格token
    app_token = "J4O0b6cGVa3ZqGsx33pcV3zNnAb"

    # 用户信息
    user_id = "your_feishu_user_id"  # 张远的user_id
    user_email = "yuan.zhang@hiretool.cn"

    manager = FeishuPermissionManager()

    print(f"\n📊 多维表格: {app_token}")
    print(f"👤 目标用户: {user_id} ({user_email})")

    print("\n" + "=" * 80)
    print("方案1: 添加为编辑者 (使用user_id)")
    print("=" * 80)
    manager.add_member_v2(app_token, user_id, "userid", "edit")

    print("\n" + "=" * 80)
    print("方案2: 添加为编辑者 (使用email)")
    print("=" * 80)
    manager.add_member_v2(app_token, user_email, "email", "edit")

    print("\n" + "=" * 80)
    print("方案3: 转移所有者")
    print("=" * 80)
    manager.transfer_owner(app_token, user_id, "userid")

    print("\n" + "=" * 80)
    print("完成")
    print("=" * 80)


if __name__ == '__main__':
    main()
