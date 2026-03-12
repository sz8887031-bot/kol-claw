#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书权限设置 - 使用URL参数方式
"""

import requests
import json
import os
from feishu_config import get_feishu_config


class FeishuPermissionFixer:
    """飞书权限修复器"""

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

    def add_member_with_params(self, token, member_id, member_type="userid", perm="edit"):
        """
        使用URL参数添加协作者
        """
        if not self.tenant_access_token:
            if not self.get_tenant_access_token():
                return False

        # 尝试在URL中指定type参数
        url = f"https://open.feishu.cn/open-apis/drive/v1/permissions/{token}/members?type=user"
        headers = {
            "Authorization": f"Bearer {self.tenant_access_token}",
            "Content-Type": "application/json"
        }

        data = {
            "member_type": member_type,
            "member_id": member_id,
            "perm": perm
        }

        print(f"\n📤 方法1: URL参数方式")
        print(f"   URL: {url}")
        print(f"   数据: {json.dumps(data, ensure_ascii=False, indent=2)}")

        response = requests.post(url, headers=headers, json=data)
        result = response.json()

        print(f"\n📥 响应: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get('code') == 0:
            print(f"\n✅ 成功!")
            return True
        else:
            print(f"\n❌ 失败: {result.get('msg')}")
            return False

    def add_member_openid(self, token, open_id, perm="edit"):
        """
        使用open_id添加协作者
        """
        if not self.tenant_access_token:
            if not self.get_tenant_access_token():
                return False

        url = f"https://open.feishu.cn/open-apis/drive/v1/permissions/{token}/members?type=user"
        headers = {
            "Authorization": f"Bearer {self.tenant_access_token}",
            "Content-Type": "application/json"
        }

        data = {
            "member_type": "openid",
            "member_id": open_id,
            "perm": perm
        }

        print(f"\n📤 方法2: 使用OpenID")
        print(f"   URL: {url}")
        print(f"   数据: {json.dumps(data, ensure_ascii=False, indent=2)}")

        response = requests.post(url, headers=headers, json=data)
        result = response.json()

        print(f"\n📥 响应: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get('code') == 0:
            print(f"\n✅ 成功!")
            return True
        else:
            print(f"\n❌ 失败: {result.get('msg')}")
            return False

    def set_public_link(self, token):
        """
        设置公开链接权限
        """
        if not self.tenant_access_token:
            if not self.get_tenant_access_token():
                return False

        url = f"https://open.feishu.cn/open-apis/drive/v1/permissions/{token}/public?type=bitable"
        headers = {
            "Authorization": f"Bearer {self.tenant_access_token}",
            "Content-Type": "application/json"
        }

        # 设置为租户内可编辑
        data = {
            "link_share_entity": "tenant_editable",
            "external_access": False
        }

        print(f"\n📤 方法3: 设置公开链接")
        print(f"   URL: {url}")
        print(f"   数据: {json.dumps(data, ensure_ascii=False, indent=2)}")

        response = requests.patch(url, headers=headers, json=data)
        result = response.json()

        print(f"\n📥 响应: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get('code') == 0:
            print(f"\n✅ 成功! 租户内所有人都可以编辑")
            return True
        else:
            print(f"\n❌ 失败: {result.get('msg')}")
            return False


def main():
    """主函数"""
    print("=" * 80)
    print("飞书多维表格权限设置 - 多种方法尝试")
    print("=" * 80)

    app_token = "J4O0b6cGVa3ZqGsx33pcV3zNnAb"
    user_id = "your_feishu_user_id"
    open_id = "ou_a6d73265a107cda9463a5e8b06edac46"
    email = "yuan.zhang@hiretool.cn"

    manager = FeishuPermissionFixer()

    print(f"\n📊 多维表格: {app_token}")
    print(f"👤 用户信息:")
    print(f"   user_id: {user_id}")
    print(f"   open_id: {open_id}")
    print(f"   email: {email}")

    print("\n" + "=" * 80)
    print("尝试不同的方法添加权限")
    print("=" * 80)

    # 方法1: 使用userid + URL参数
    success1 = manager.add_member_with_params(app_token, user_id, "userid", "edit")

    # 方法2: 使用openid
    if not success1:
        success2 = manager.add_member_openid(app_token, open_id, "edit")

    # 方法3: 设置为租户内可编辑
    success3 = manager.set_public_link(app_token)

    print("\n" + "=" * 80)
    print("结果汇总")
    print("=" * 80)

    if success1 or success3:
        print("\n✅ 权限设置成功!")
        print(f"\n📊 访问链接: https://bytedance.larkoffice.com/base/{app_token}")
        print("\n💡 你现在应该可以访问和编辑这个表格了")
    else:
        print("\n⚠️  API方式设置权限遇到困难")
        print("\n备选方案:")
        print("1. 我可以创建一个新的多维表格，并立即设置为公开")
        print("2. 或者使用Excel导入方式")


if __name__ == '__main__':
    main()
