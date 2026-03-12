#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将达人跟进表创建为飞书文档
"""

import requests
import json
import os
from feishu_config import get_feishu_config
import pandas as pd
from datetime import datetime


class FeishuDocCreator:
    """飞书文档创建器"""

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

    def create_doc(self, title):
        """创建飞书文档"""
        if not self.tenant_access_token:
            if not self.get_tenant_access_token():
                return None

        url = "https://open.feishu.cn/open-apis/docx/v1/documents"
        headers = {
            "Authorization": f"Bearer {self.tenant_access_token}",
            "Content-Type": "application/json"
        }
        data = {
            "title": title
        }

        response = requests.post(url, headers=headers, json=data)
        result = response.json()

        if result.get('code') == 0:
            return result['data']['document']['document_id']
        else:
            print(f"❌ 创建文档失败: {result}")
            return None

    def add_table_to_doc(self, doc_id, df):
        """向文档添加表格（使用多维表格）"""
        if not self.tenant_access_token:
            if not self.get_tenant_access_token():
                return False

        # 使用飞书多维表格API创建表格
        # 1. 创建多维表格
        url = "https://open.feishu.cn/open-apis/bitable/v1/apps"
        headers = {
            "Authorization": f"Bearer {self.tenant_access_token}",
            "Content-Type": "application/json"
        }

        data = {
            "name": f"达人跟进表 - {datetime.now().strftime('%Y年%m月%d日')}"
        }

        response = requests.post(url, headers=headers, json=data)
        result = response.json()

        if result.get('code') != 0:
            print(f"⚠️  创建多维表格失败: {result}")
            print("   文档已创建，但无法添加表格内容")
            print("   请手动在飞书中打开文档并添加内容")
            return False

        app_token = result['data']['app']['app_token']
        print(f"   多维表格ID: {app_token}")

        # 2. 获取默认表格
        tables_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables"
        tables_response = requests.get(tables_url, headers=headers)
        tables_result = tables_response.json()

        if tables_result.get('code') != 0:
            print(f"⚠️  获取表格失败: {tables_result}")
            return False

        table_id = tables_result['data']['items'][0]['table_id']

        # 3. 添加字段（列）
        fields_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields"

        # 只添加主要字段
        main_columns = ['抖音号', '粉丝数', '播放1', '报价', '建联状态', '确定合作', '达人级别', '备注']

        for col in main_columns:
            if col in df.columns:
                field_data = {
                    "field_name": col,
                    "type": 1  # 文本类型
                }
                requests.post(fields_url, headers=headers, json=field_data)

        # 4. 添加数据（前50行）
        records_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create"

        records = []
        for idx, row in df.head(50).iterrows():
            record = {"fields": {}}
            for col in main_columns:
                if col in df.columns:
                    val = row[col]
                    if pd.notna(val):
                        record["fields"][col] = str(val)
            records.append(record)

        # 分批添加（每次最多500条）
        batch_size = 100
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            batch_data = {"records": batch}
            requests.post(records_url, headers=headers, json=batch_data)

        # 生成多维表格链接
        bitable_url = f"https://bytedance.larkoffice.com/base/{app_token}"
        print(f"\n📊 多维表格链接: {bitable_url}")

        return True

    def create_doc_from_csv(self, csv_path, doc_title):
        """从CSV创建飞书多维表格"""
        print("=" * 80)
        print(f"创建飞书多维表格: {doc_title}")
        print("=" * 80)

        # 读取CSV
        print("\n1. 读取CSV文件...")
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
        print(f"✅ 读取成功，共 {len(df)} 条数据")

        # 统计信息
        total = len(df)
        contacted = len(df[df['建联状态'].notna() & (df['建联状态'] != '未建联')])
        confirmed = len(df[df['确定合作'].notna() & (df['确定合作'] == '确定合作')])
        print(f"   总达人: {total} | 已建联: {contacted} | 确定合作: {confirmed}")

        # 创建多维表格
        print("\n2. 创建飞书多维表格...")
        result = self.add_table_to_doc(None, df)

        return result


def main():
    """主函数"""
    csv_path = "data/达人跟进表.csv"
    doc_title = f"达人跟进表 - {datetime.now().strftime('%Y年%m月%d日')}"

    creator = FeishuDocCreator()
    success = creator.create_doc_from_csv(csv_path, doc_title)

    if success:
        print("\n" + "=" * 80)
        print("✅ 飞书多维表格创建完成！")
        print("=" * 80)
        print("\n💡 提示: 请在飞书中查看多维表格")
    else:
        print("\n❌ 创建失败")


if __name__ == '__main__':
    main()
