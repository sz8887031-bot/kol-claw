#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成飞书多维表格的公开分享链接
"""

import requests
import json
import os
from feishu_config import get_feishu_config


class FeishuShareManager:
    """飞书分享管理器"""

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

    def get_bitable_info(self, app_token):
        """获取多维表格信息"""
        if not self.tenant_access_token:
            if not self.get_tenant_access_token():
                return None

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}"
        headers = {
            "Authorization": f"Bearer {self.tenant_access_token}"
        }

        response = requests.get(url, headers=headers)
        result = response.json()

        return result


def main():
    """主函数"""
    print("=" * 80)
    print("飞书多维表格信息")
    print("=" * 80)

    app_token = os.environ.get('FEISHU_APP_TOKEN', '')
    if not app_token:
        print("❌ 请设置环境变量 FEISHU_APP_TOKEN")
        return

    manager = FeishuShareManager()

    print(f"\n📊 多维表格Token: {app_token}")
    print(f"🔗 访问链接: https://bytedance.larkoffice.com/base/{app_token}")

    print("\n获取表格信息...")
    info = manager.get_bitable_info(app_token)

    if info:
        print(f"\n📋 表格详情:")
        print(json.dumps(info, ensure_ascii=False, indent=2))

    print("\n" + "=" * 80)
    print("💡 解决方案")
    print("=" * 80)
    print("\n由于API权限限制，最佳方案是:")
    print("\n1. ✅ 使用已导出的Excel文件")
    print("   文件: data/达人跟进表_20260307_1544.xlsx")
    print("   在飞书中导入此文件，你将成为所有者")
    print("\n2. 或者在飞书中手动添加协作者")
    print("   - 打开多维表格")
    print("   - 点击右上角「分享」")
    print("   - 添加你的飞书账号为协作者")
    print("\n3. 联系飞书管理员")
    print("   - 请管理员将表格所有权转移给你")


if __name__ == '__main__':
    main()
