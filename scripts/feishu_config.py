#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书配置加载模块
优先级：项目级 .env.feishu > 系统环境变量 > 报错
"""
import os
from pathlib import Path
from dotenv import load_dotenv


class FeishuConfig:
    """飞书配置管理器"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # 加载项目级配置文件
        project_root = Path(__file__).parent
        env_file = project_root / '.env.feishu'

        if env_file.exists():
            load_dotenv(env_file, override=True)
            self._config_source = f"项目配置文件: {env_file}"
        else:
            self._config_source = "系统环境变量"

        # 读取配置
        self.app_id = os.environ.get('FEISHU_APP_ID')
        self.app_secret = os.environ.get('FEISHU_APP_SECRET')
        self.user_id = os.environ.get('FEISHU_USER_ID')
        self.webhook_url = os.environ.get('FEISHU_WEBHOOK_URL')
        self.app_token = os.environ.get('FEISHU_APP_TOKEN')
        self.table_1_id = os.environ.get('FEISHU_TABLE_1_ID')
        self.table_2_id = os.environ.get('FEISHU_TABLE_2_ID')

        # 验证必需配置
        if not self.app_id or not self.app_secret:
            raise ValueError(
                f"飞书配置缺失！\n"
                f"配置来源: {self._config_source}\n"
                f"请确保以下环境变量已设置：\n"
                f"  - FEISHU_APP_ID\n"
                f"  - FEISHU_APP_SECRET\n"
                f"\n"
                f"方式1（推荐）：在项目根目录创建 .env.feishu 文件\n"
                f"方式2：在系统环境变量中设置"
            )

        if not self.user_id:
            raise ValueError(
                f"飞书用户ID未配置！\n"
                f"请在环境变量中设置 FEISHU_USER_ID"
            )

        # 可选配置检查（不存在时打印警告）
        if not self.app_token:
            print("警告: FEISHU_APP_TOKEN 未配置，多维表格功能将不可用")
        if not self.table_1_id:
            print("警告: FEISHU_TABLE_1_ID 未配置，表格1相关功能将不可用")
        if not self.table_2_id:
            print("警告: FEISHU_TABLE_2_ID 未配置，表格2相关功能将不可用")

        self._initialized = True

    def get_config_info(self):
        """获取配置信息（用于调试）"""
        return {
            'source': self._config_source,
            'app_id': self.app_id[:10] + '...' if self.app_id else None,
            'app_secret': '***' if self.app_secret else None,
            'user_id': self.user_id,
            'webhook_url': self.webhook_url[:30] + '...' if self.webhook_url else None,
            'app_token': self.app_token,
            'table_1_id': self.table_1_id,
            'table_2_id': self.table_2_id,
        }


# 全局配置实例
def get_feishu_config():
    """获取飞书配置实例"""
    return FeishuConfig()


if __name__ == '__main__':
    # 测试配置加载
    print("=== 飞书配置测试 ===\n")
    try:
        config = get_feishu_config()
        info = config.get_config_info()

        print(f"配置来源: {info['source']}")
        print(f"\n配置详情:")
        print(f"  APP_ID: {info['app_id']}")
        print(f"  APP_SECRET: {info['app_secret']}")
        print(f"  USER_ID: {info['user_id']}")
        print(f"  WEBHOOK_URL: {info['webhook_url']}")
        print(f"  APP_TOKEN: {info['app_token']}")
        print(f"  TABLE_1_ID: {info['table_1_id']}")
        print(f"  TABLE_2_ID: {info['table_2_id']}")
        print("\n✅ 配置加载成功")
    except ValueError as e:
        print(f"❌ 配置加载失败:\n{e}")
