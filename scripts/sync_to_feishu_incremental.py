#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书多维表格同步工具（规范化版本）

功能：
1. 达人跟进表：全量覆盖同步
2. 达人投放计划表：增量添加（只添加新达人，不改动已有数据）

使用方法：
    python3 sync_to_feishu_incremental.py
"""
import requests
import json
import os
from feishu_config import get_feishu_config
import pandas as pd
from datetime import datetime

# 飞书多维表格配置
APP_TOKEN = "your_app_token_here"
TABLE_1_ID = "your_table_1_id_here"  # 达人跟进表
TABLE_2_ID = "your_table_2_id_here"  # 达人投放计划表

# 本地CSV文件路径
CSV_TRACKING = "data/达人跟进表.csv"
CSV_CONFIRMED = "data/确定合作达人跟进表.csv"


class FeishuBitableSync:
    """飞书多维表格同步器"""

    def __init__(self):
        # 从项目配置加载
        config = get_feishu_config()
        self.app_id = config.app_id
        self.app_secret = config.app_secret
        self.tenant_access_token = None

    def get_fields_info(self, app_token, table_id):
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
            # 返回字段名到类型的映射
            fields_map = {}
            for field in result['data']['items']:
                fields_map[field['field_name']] = field['type']
            return fields_map
        else:
            print(f"❌ 获取字段信息失败: {result}")
            return None

    def convert_value_by_type(self, value, field_type):
        """根据字段类型转换值"""
        if pd.isna(value) or value == '':
            return None

        # 类型1: 文本
        if field_type == 1:
            return str(value)

        # 类型2: 数字
        elif field_type == 2:
            try:
                # 尝试转换为数字
                return float(value) if '.' in str(value) else int(float(value))
            except:
                return None

        # 类型3: 单选
        elif field_type == 3:
            return str(value)

        # 类型4: 多选（需要返回字符串列表）
        elif field_type == 4:
            # 如果值中包含分隔符，拆分为列表
            val_str = str(value)
            if ',' in val_str:
                return [s.strip() for s in val_str.split(',')]
            elif ';' in val_str:
                return [s.strip() for s in val_str.split(';')]
            else:
                # 单个值也要包装成列表
                return [val_str]

        # 类型5: 日期
        elif field_type == 5:
            try:
                # 尝试解析日期并转换为Unix时间戳（毫秒）
                date_str = str(value)
                # 支持多种日期格式
                for fmt in ['%Y/%m/%d', '%Y-%m-%d', '%Y/%m/%d %H:%M', '%Y-%m-%d %H:%M:%S']:
                    try:
                        dt = datetime.strptime(date_str, fmt)
                        return int(dt.timestamp() * 1000)
                    except:
                        continue
                return None
            except:
                return None

        # 其他类型默认转为字符串
        else:
            return str(value)

    def prepare_records(self, df, fields_map):
        """准备记录数据（根据字段类型转换）"""
        records = []
        for idx, row in df.iterrows():
            record = {"fields": {}}
            for col in df.columns:
                if col in fields_map:
                    val = row[col]
                    converted_val = self.convert_value_by_type(val, fields_map[col])
                    if converted_val is not None:
                        record["fields"][col] = converted_val
            records.append(record)
        return records

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

    def get_all_records(self, app_token, table_id):
        """获取表格的所有记录"""
        if not self.tenant_access_token:
            if not self.get_tenant_access_token():
                return None

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
        headers = {
            "Authorization": f"Bearer {self.tenant_access_token}"
        }

        all_records = []
        page_token = None

        while True:
            params = {"page_size": 500}
            if page_token:
                params["page_token"] = page_token

            response = requests.get(url, headers=headers, params=params)
            result = response.json()

            if result.get('code') == 0:
                items = result['data'].get('items', [])
                if items:
                    all_records.extend(items)

                if not result['data'].get('has_more'):
                    break
                page_token = result['data'].get('page_token')
            else:
                print(f"❌ 获取记录失败: {result}")
                return None

        return all_records

    def delete_all_records(self, app_token, table_id):
        """删除表格的所有记录"""
        if not self.tenant_access_token:
            return False

        # 先获取所有记录
        records = self.get_all_records(app_token, table_id)
        if not records:
            print("   表格为空，无需删除")
            return True

        # 批量删除
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_delete"
        headers = {
            "Authorization": f"Bearer {self.tenant_access_token}",
            "Content-Type": "application/json"
        }

        record_ids = [r['record_id'] for r in records]
        batch_size = 500

        deleted_count = 0
        for i in range(0, len(record_ids), batch_size):
            batch = record_ids[i:i+batch_size]
            data = {"records": batch}

            response = requests.post(url, headers=headers, json=data)
            result = response.json()

            if result.get('code') == 0:
                deleted_count += len(batch)
                print(f"   已删除 {deleted_count}/{len(record_ids)} 条记录")
            else:
                print(f"❌ 删除失败: {result}")
                return False

        return True

    def add_records_batch(self, app_token, table_id, records):
        """批量添加记录"""
        if not self.tenant_access_token:
            return False

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create"
        headers = {
            "Authorization": f"Bearer {self.tenant_access_token}",
            "Content-Type": "application/json"
        }

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
                print(f"❌ 批次添加失败: {result}")
                return False

        return True

    def sync_tracking_table(self):
        """同步达人跟进表（全量覆盖）"""
        print("\n" + "=" * 80)
        print("1. 同步达人跟进表（全量覆盖）")
        print("=" * 80)

        # 读取本地CSV
        print("\n📖 读取本地CSV...")
        df = pd.read_csv(CSV_TRACKING, encoding='utf-8-sig')
        print(f"✅ 读取成功，共 {len(df)} 条数据")

        # 获取字段类型信息
        print("\n🔍 获取字段类型信息...")
        fields_map = self.get_fields_info(APP_TOKEN, TABLE_1_ID)
        if not fields_map:
            return False
        print(f"✅ 获取了 {len(fields_map)} 个字段的类型信息")

        # 删除飞书表格中的所有记录
        print("\n🗑️  清空飞书表格...")
        if not self.delete_all_records(APP_TOKEN, TABLE_1_ID):
            return False
        print("✅ 清空完成")

        # 准备数据（根据字段类型转换）
        print("\n🔄 准备数据...")
        records = self.prepare_records(df, fields_map)
        print(f"✅ 准备了 {len(records)} 条记录")

        # 批量添加数据
        print("\n📤 上传数据到飞书...")
        if self.add_records_batch(APP_TOKEN, TABLE_1_ID, records):
            print("✅ 达人跟进表同步完成")
            return True
        else:
            print("❌ 达人跟进表同步失败")
            return False

    def sync_plan_table_incremental(self):
        """同步达人投放计划表（增量添加）"""
        print("\n" + "=" * 80)
        print("2. 同步达人投放计划表（增量添加）")
        print("=" * 80)

        # 读取本地CSV
        print("\n📖 读取本地CSV...")
        df_local = pd.read_csv(CSV_CONFIRMED, encoding='utf-8-sig')
        print(f"✅ 读取成功，共 {len(df_local)} 条数据")

        # 获取字段类型信息
        print("\n🔍 获取字段类型信息...")
        fields_map = self.get_fields_info(APP_TOKEN, TABLE_2_ID)
        if not fields_map:
            return False
        print(f"✅ 获取了 {len(fields_map)} 个字段的类型信息")

        # 获取飞书表格中已有的记录
        print("\n📥 获取飞书表格中已有的数据...")
        existing_records = self.get_all_records(APP_TOKEN, TABLE_2_ID)
        if existing_records is None:
            return False

        # 提取已有的达人昵称
        existing_names = set()
        for record in existing_records:
            fields = record.get('fields', {})
            name = fields.get('达人昵称', '')
            if name:
                existing_names.add(name)

        print(f"✅ 飞书表格中已有 {len(existing_names)} 个达人")

        # 找出新增的达人
        print("\n🔍 查找新增的达人...")
        new_df = df_local[~df_local['达人昵称'].isin(existing_names)]

        if len(new_df) == 0:
            print("✅ 没有新增的达人，无需同步")
            return True

        print(f"✅ 找到 {len(new_df)} 个新增达人")

        # 准备新记录（根据字段类型转换）
        print("\n🔄 准备数据...")
        new_records = self.prepare_records(new_df, fields_map)
        print(f"✅ 准备了 {len(new_records)} 条记录")

        # 批量添加新记录
        print("\n📤 添加新达人到飞书...")
        if self.add_records_batch(APP_TOKEN, TABLE_2_ID, new_records):
            print(f"✅ 成功添加 {len(new_records)} 个新达人")
            return True
        else:
            print("❌ 添加新达人失败")
            return False

    def run(self):
        """执行同步"""
        print("=" * 80)
        print(f"飞书多维表格同步工具 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        # 获取token
        if not self.get_tenant_access_token():
            return

        # 同步达人跟进表
        success1 = self.sync_tracking_table()

        # 同步达人投放计划表
        success2 = self.sync_plan_table_incremental()

        # 总结
        print("\n" + "=" * 80)
        if success1 and success2:
            print("✅ 所有表格同步完成")
        else:
            print("⚠️  部分表格同步失败")
        print("=" * 80)

        # 生成链接
        bitable_url = f"https://bytedance.larkoffice.com/base/{APP_TOKEN}"
        print(f"\n📊 飞书多维表格链接: {bitable_url}")


def main():
    syncer = FeishuBitableSync()
    syncer.run()


if __name__ == '__main__':
    main()
