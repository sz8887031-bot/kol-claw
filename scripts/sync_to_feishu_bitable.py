#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将达人跟进表同步到飞书多维表格（完整版）
支持所有字段和完整数据
"""

import requests
import json
import os
from feishu_config import get_feishu_config
import pandas as pd
from datetime import datetime


class FeishuBitableSync:
    """飞书多维表格同步器"""

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

    def create_bitable(self, name):
        """创建多维表格"""
        if not self.tenant_access_token:
            if not self.get_tenant_access_token():
                return None

        url = "https://open.feishu.cn/open-apis/bitable/v1/apps"
        headers = {
            "Authorization": f"Bearer {self.tenant_access_token}",
            "Content-Type": "application/json"
        }

        data = {"name": name}

        response = requests.post(url, headers=headers, json=data)
        result = response.json()

        if result.get('code') == 0:
            return result['data']['app']['app_token']
        else:
            print(f"❌ 创建多维表格失败: {result}")
            return None

    def get_default_table(self, app_token):
        """获取默认表格ID"""
        if not self.tenant_access_token:
            return None

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables"
        headers = {
            "Authorization": f"Bearer {self.tenant_access_token}"
        }

        response = requests.get(url, headers=headers)
        result = response.json()

        if result.get('code') == 0 and result['data']['items']:
            return result['data']['items'][0]['table_id']
        return None

    def create_fields(self, app_token, table_id, columns):
        """创建字段"""
        if not self.tenant_access_token:
            return False

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
        headers = {
            "Authorization": f"Bearer {self.tenant_access_token}",
            "Content-Type": "application/json"
        }

        created_count = 0
        for col in columns:
            # 跳过默认字段
            if col in ['序号', 'ID']:
                continue

            data = {
                "field_name": col,
                "type": 1  # 文本类型
            }

            response = requests.post(url, headers=headers, json=data)
            result = response.json()

            if result.get('code') == 0:
                created_count += 1
            else:
                print(f"   ⚠️  创建字段 '{col}' 失败: {result.get('msg')}")

        return created_count

    def add_records_batch(self, app_token, table_id, records):
        """批量添加记录"""
        if not self.tenant_access_token:
            return False

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create"
        headers = {
            "Authorization": f"Bearer {self.tenant_access_token}",
            "Content-Type": "application/json"
        }

        # 分批添加（每次最多500条）
        batch_size = 100
        total_added = 0

        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            data = {"records": batch}

            response = requests.post(url, headers=headers, json=data)
            result = response.json()

            if result.get('code') == 0:
                total_added += len(batch)
                print(f"   已添加 {total_added}/{len(records)} 条记录")
            else:
                print(f"⚠️  批次添加失败: {result}")

        return total_added == len(records)

    def sync_csv_to_bitable(self, csv_path, bitable_name):
        """将CSV同步到飞书多维表格"""
        print("=" * 80)
        print(f"同步到飞书多维表格: {bitable_name}")
        print("=" * 80)

        # 1. 读取CSV
        print("\n📖 步骤1: 读取CSV文件...")
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
        print(f"✅ 读取成功，共 {len(df)} 条数据")

        # 统计信息
        total = len(df)
        contacted = len(df[df['建联状态'].notna() & (df['建联状态'] != '未建联')])
        confirmed = len(df[df['确定合作'].notna() & (df['确定合作'] == '确定合作')])
        print(f"   📊 总达人: {total} | 已建联: {contacted} | 确定合作: {confirmed}")

        # 2. 创建多维表格
        print("\n📝 步骤2: 创建飞书多维表格...")
        app_token = self.create_bitable(bitable_name)
        if not app_token:
            return None
        print(f"✅ 多维表格创建成功")
        print(f"   ID: {app_token}")

        # 3. 获取默认表格
        print("\n📋 步骤3: 获取默认表格...")
        table_id = self.get_default_table(app_token)
        if not table_id:
            print("❌ 获取表格失败")
            return None
        print(f"✅ 表格ID: {table_id}")

        # 4. 创建字段
        print("\n🔧 步骤4: 创建字段...")
        created = self.create_fields(app_token, table_id, df.columns)
        print(f"✅ 创建了 {created} 个字段")

        # 5. 准备数据
        print("\n🔄 步骤5: 准备数据...")
        records = []
        for idx, row in df.iterrows():
            record = {"fields": {}}
            for col in df.columns:
                val = row[col]
                if pd.notna(val):
                    # 转换为字符串，避免类型问题
                    record["fields"][col] = str(val)
            records.append(record)
        print(f"✅ 准备了 {len(records)} 条记录")

        # 6. 批量添加数据
        print("\n📤 步骤6: 上传数据到飞书...")
        if self.add_records_batch(app_token, table_id, records):
            print("✅ 数据上传成功")
        else:
            print("⚠️  部分数据上传失败")

        # 7. 生成链接
        bitable_url = f"https://bytedance.larkoffice.com/base/{app_token}"

        print("\n" + "=" * 80)
        print("✅ 同步完成！")
        print("=" * 80)
        print(f"\n📊 多维表格链接: {bitable_url}")
        print("\n💡 提示:")
        print("   1. 在飞书中打开链接查看表格")
        print("   2. 可以在飞书中进一步编辑和管理数据")
        print("   3. 支持筛选、排序、视图等高级功能")

        return app_token


def main():
    """主函数"""
    csv_path = "data/达人跟进表.csv"
    bitable_name = f"达人跟进表 - {datetime.now().strftime('%Y年%m月%d日 %H:%M')}"

    syncer = FeishuBitableSync()
    app_token = syncer.sync_csv_to_bitable(csv_path, bitable_name)

    if app_token:
        print(f"\n🎉 成功！多维表格已创建")
        print(f"   链接: https://bytedance.larkoffice.com/base/{app_token}")
    else:
        print("\n❌ 同步失败")


if __name__ == '__main__':
    main()
