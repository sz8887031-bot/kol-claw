#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书多维表格权限管理
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

    def add_member(self, app_token, member_id, role="edit"):
        """添加协作成员"""
        if not self.tenant_access_token:
            if not self.get_tenant_access_token():
                return False

        url = f"https://open.feishu.cn/open-apis/drive/v1/permissions/{app_token}/members"
        headers = {
            "Authorization": f"Bearer {self.tenant_access_token}",
            "Content-Type": "application/json"
        }

        # role: full_access(所有者), edit(编辑者), view(查看者)
        data = {
            "member_type": "userid",
            "member_id": member_id,
            "perm": role,
            "type": "user"
        }

        response = requests.post(url, headers=headers, json=data)
        result = response.json()

        if result.get('code') == 0:
            print(f"✅ 成功添加成员: {member_id} (权限: {role})")
            return True
        else:
            print(f"❌ 添加成员失败: {result}")
            return False

    def set_public_permission(self, app_token, permission="tenant_readable"):
        """设置公开权限"""
        if not self.tenant_access_token:
            if not self.get_tenant_access_token():
                return False

        url = f"https://open.feishu.cn/open-apis/drive/v1/permissions/{app_token}/public"
        headers = {
            "Authorization": f"Bearer {self.tenant_access_token}",
            "Content-Type": "application/json"
        }

        # 根据权限类型设置参数
        data = {
            "type": "bitable",
            "link_share_entity": permission,  # tenant_readable, tenant_editable, anyone_readable, anyone_editable
            "external_access": permission.startswith("anyone"),
            "invite_external": permission.startswith("anyone")
        }

        response = requests.patch(url, headers=headers, json=data)
        result = response.json()

        if result.get('code') == 0:
            print(f"✅ 成功设置公开权限: {permission}")
            return True
        else:
            print(f"❌ 设置权限失败: {result}")
            return False

    def get_share_link(self, app_token):
        """获取分享链接"""
        # 飞书多维表格的分享链接格式
        return f"https://bytedance.larkoffice.com/base/{app_token}"


def main():
    """主函数"""
    print("=" * 80)
    print("飞书多维表格权限管理")
    print("=" * 80)

    # 最新创建的多维表格ID
    app_token = "J4O0b6cGVa3ZqGsx33pcV3zNnAb"

    manager = FeishuPermissionManager()

    print(f"\n📊 多维表格ID: {app_token}")
    print(f"🔗 访问链接: {manager.get_share_link(app_token)}")

    print("\n" + "=" * 80)
    print("权限设置选项:")
    print("=" * 80)
    print("\n1. 添加协作成员")
    print("   示例: manager.add_member(app_token, 'your_feishu_user_id', 'edit')")
    print("   权限类型: full_access(所有者), edit(编辑者), view(查看者)")

    print("\n2. 设置公开权限")
    print("   - tenant_readable: 租户内可见（推荐）")
    print("   - tenant_editable: 租户内可编辑")
    print("   - anyone_readable: 互联网可见")
    print("   - anyone_editable: 互联网可编辑")

    print("\n" + "=" * 80)
    print("快速操作:")
    print("=" * 80)

    # 自动添加当前用户为编辑者
    print("\n🔧 正在添加你为协作成员...")
    user_id = "your_feishu_user_id"  # 张远的user_id
    if manager.add_member(app_token, user_id, "edit"):
        print(f"✅ 你现在可以编辑这个多维表格了")

    # 设置为租户内可见
    print("\n🔧 正在设置为租户内可见...")
    if manager.set_public_permission(app_token, "tenant_readable"):
        print(f"✅ 租户内所有人都可以查看这个表格")

    print("\n" + "=" * 80)
    print("✅ 权限设置完成！")
    print("=" * 80)
    print(f"\n📊 访问链接: {manager.get_share_link(app_token)}")
    print("\n💡 提示: 在飞书中打开链接即可查看和编辑表格")


if __name__ == '__main__':
    main()
