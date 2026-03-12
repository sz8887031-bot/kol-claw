#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看飞书多维表格结构
"""
import requests
import json
import os
from feishu_config import get_feishu_config

class FeishuBitableChecker:
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

    def get_tables(self, app_token):
        """获取多维表格中的所有表"""
        if not self.tenant_access_token:
            if not self.get_tenant_access_token():
                return None

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables"
        headers = {
            "Authorization": f"Bearer {self.tenant_access_token}"
        }

        response = requests.get(url, headers=headers)
        result = response.json()

        if result.get('code') == 0:
            return result['data']['items']
        else:
            print(f"❌ 获取表格列表失败: {result}")
            return None

    def get_fields(self, app_token, table_id):
        """获取表格的字段信息"""
        if not self.tenant_access_token:
            return None

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
        headers = {
            "Authorization": f"Bearer {self.tenant_access_token}"
        }

        response = requests.get(url, headers=headers)
        result = response.json()

        if result.get('code') == 0:
            return result['data']['items']
        else:
            print(f"❌ 获取字段失败: {result}")
            return None

    def get_records(self, app_token, table_id, page_size=10):
        """获取表格的记录（示例）"""
        if not self.tenant_access_token:
            return None

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
        headers = {
            "Authorization": f"Bearer {self.tenant_access_token}"
        }
        params = {"page_size": page_size}

        response = requests.get(url, headers=headers, params=params)
        result = response.json()

        if result.get('code') == 0:
            return result['data']
        else:
            print(f"❌ 获取记录失败: {result}")
            return None

    def check_structure(self, app_token):
        """检查多维表格结构"""
        print("=" * 80)
        print(f"检查飞书多维表格结构")
        print("=" * 80)
        print(f"\nApp Token: {app_token}\n")

        # 获取所有表
        tables = self.get_tables(app_token)
        if not tables:
            return

        print(f"✅ 找到 {len(tables)} 个表:\n")

        for idx, table in enumerate(tables, 1):
            table_id = table['table_id']
            table_name = table['name']

            print(f"{idx}. 表名: {table_name}")
            print(f"   Table ID: {table_id}")

            # 获取字段
            fields = self.get_fields(app_token, table_id)
            if fields:
                print(f"   字段数: {len(fields)}")
                print(f"   字段列表:")
                for field in fields:
                    field_name = field['field_name']
                    field_type = field['type']
                    print(f"      - {field_name} (类型: {field_type})")

            # 获取记录数
            records_data = self.get_records(app_token, table_id, page_size=1)
            if records_data:
                total = records_data.get('total', 0)
                print(f"   记录数: {total}")

            print()

        return tables


def main():
    app_token = "your_app_token_here"

    checker = FeishuBitableChecker()
    tables = checker.check_structure(app_token)

    if tables:
        print("\n" + "=" * 80)
        print("✅ 检查完成")
        print("=" * 80)


if __name__ == '__main__':
    main()
