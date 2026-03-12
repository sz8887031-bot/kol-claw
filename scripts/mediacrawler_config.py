#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MediaCrawler 配置和调用模块
用于 KOL 投放管理系统的达人数据采集

整合了原有的 discover_creators.py 自定义脚本
"""

import subprocess
import json
import os
from pathlib import Path
from typing import List, Dict, Optional

# MediaCrawler 安装路径
MEDIACRAWLER_PATH = "<MEDIACRAWLER_DIR>"

# 自定义脚本路径
DISCOVER_CREATORS_SCRIPT = os.path.join(MEDIACRAWLER_PATH, "discover_creators.py")

# 已保存的达人数据路径
DISCOVERED_CREATORS_DATA = "<MEDIACRAWLER_DIR>/discovered_creators.json"

class MediaCrawlerClient:
    """MediaCrawler 客户端封装类"""

    def __init__(self, mediacrawler_path: str = MEDIACRAWLER_PATH):
        self.mediacrawler_path = Path(mediacrawler_path)
        if not self.mediacrawler_path.exists():
            raise FileNotFoundError(f"MediaCrawler 路径不存在: {mediacrawler_path}")

    def _run_command(self, args: List[str]) -> subprocess.CompletedProcess:
        """执行 MediaCrawler 命令"""
        cmd = ["uv", "run", "python", "main.py"] + args
        result = subprocess.run(
            cmd,
            cwd=self.mediacrawler_path,
            capture_output=True,
            text=True
        )
        return result

    def search_creators(
        self,
        platform: str = "xhs",
        keywords: str = "美妆博主",
        login_type: str = "qrcode",
        max_count: int = 20,
        save_format: str = "json",
        headless: bool = False
    ) -> Dict:
        """
        搜索达人/创作者

        Args:
            platform: 平台 (xhs=小红书, dy=抖音, ks=快手, bili=B站, wb=微博, tieba=贴吧, zhihu=知乎)
            keywords: 搜索关键词，多个关键词用逗号分隔
            login_type: 登录方式 (qrcode=二维码, phone=手机号, cookie=Cookie)
            max_count: 最大爬取数量
            save_format: 保存格式 (json, csv, excel, sqlite, db)
            headless: 是否无头模式

        Returns:
            执行结果字典
        """
        args = [
            "--platform", platform,
            "--type", "search",
            "--keywords", keywords,
            "--lt", login_type,
            "--save_data_option", save_format,
            "--headless", "true" if headless else "false"
        ]

        result = self._run_command(args)

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "data_path": self.mediacrawler_path / "data"
        }

    def get_creator_detail(
        self,
        platform: str = "xhs",
        creator_id: str = "",
        login_type: str = "qrcode",
        save_format: str = "json",
        get_comments: bool = True,
        headless: bool = False
    ) -> Dict:
        """
        获取指定创作者的详细信息

        Args:
            platform: 平台
            creator_id: 创作者ID或主页URL
            login_type: 登录方式
            save_format: 保存格式
            get_comments: 是否爬取评论
            headless: 是否无头模式

        Returns:
            执行结果字典
        """
        args = [
            "--platform", platform,
            "--type", "creator",
            "--creator_id", creator_id,
            "--lt", login_type,
            "--save_data_option", save_format,
            "--get_comment", "true" if get_comments else "false",
            "--headless", "true" if headless else "false"
        ]

        result = self._run_command(args)

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "data_path": self.mediacrawler_path / "data"
        }

    def get_post_detail(
        self,
        platform: str = "xhs",
        post_ids: str = "",
        login_type: str = "qrcode",
        save_format: str = "json",
        get_comments: bool = True,
        max_comments: int = 50,
        headless: bool = False
    ) -> Dict:
        """
        获取指定帖子/视频的详细信息

        Args:
            platform: 平台
            post_ids: 帖子/视频ID列表，多个ID用逗号分隔
            login_type: 登录方式
            save_format: 保存格式
            get_comments: 是否爬取评论
            max_comments: 最大评论数
            headless: 是否无头模式

        Returns:
            执行结果字典
        """
        args = [
            "--platform", platform,
            "--type", "detail",
            "--specified_id", post_ids,
            "--lt", login_type,
            "--save_data_option", save_format,
            "--get_comment", "true" if get_comments else "false",
            "--max_comments_count_singlenotes", str(max_comments),
            "--headless", "true" if headless else "false"
        ]

        result = self._run_command(args)

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "data_path": self.mediacrawler_path / "data"
        }

    def load_latest_data(self, platform: str = "xhs", data_type: str = "search") -> Optional[List[Dict]]:
        """
        加载最新爬取的数据

        Args:
            platform: 平台名称
            data_type: 数据类型 (search, creator, detail)

        Returns:
            数据列表或 None
        """
        data_dir = self.mediacrawler_path / "data"

        # 查找最新的 JSON 文件
        json_files = list(data_dir.glob(f"{platform}_*_{data_type}_*.json"))
        if not json_files:
            return None

        latest_file = max(json_files, key=lambda p: p.stat().st_mtime)

        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载数据失败: {e}")
            return None

    def run_discover_creators(self, keywords: List[str] = None) -> Dict:
        """
        运行自定义的达人发现脚本 (discover_creators.py)

        这是你原有的自定义脚本，专门用于抖音达人发现
        支持关键词搜索、达人信息获取、视频数据分析

        Args:
            keywords: 搜索关键词列表，默认为 ["求职", "个人成长", "职场"]

        Returns:
            执行结果字典
        """
        if not os.path.exists(DISCOVER_CREATORS_SCRIPT):
            return {
                "success": False,
                "error": f"自定义脚本不存在: {DISCOVER_CREATORS_SCRIPT}"
            }

        # 如果需要自定义关键词，可以修改脚本
        # 这里直接运行原脚本
        cmd = ["uv", "run", "python", "discover_creators.py"]

        result = subprocess.run(
            cmd,
            cwd=self.mediacrawler_path,
            capture_output=True,
            text=True
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "data_file": DISCOVERED_CREATORS_DATA
        }

    def load_discovered_creators(self) -> Optional[Dict]:
        """
        加载 discover_creators.py 生成的达人数据

        Returns:
            达人数据字典或 None
        """
        if not os.path.exists(DISCOVERED_CREATORS_DATA):
            return None

        try:
            with open(DISCOVERED_CREATORS_DATA, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载达人数据失败: {e}")
            return None

    def get_top_creators(self, min_followers: int = 10000, limit: int = 10) -> Optional[List[Dict]]:
        """
        从已发现的达人中筛选优质达人

        Args:
            min_followers: 最小粉丝数
            limit: 返回数量限制

        Returns:
            达人列表或 None
        """
        data = self.load_discovered_creators()
        if not data:
            return None

        creators = data.get("creators", [])

        # 筛选符合条件的达人
        filtered = [
            c for c in creators
            if c.get("follower_count", 0) >= min_followers
        ]

        # 按粉丝数排序
        filtered.sort(key=lambda x: x.get("follower_count", 0), reverse=True)

        return filtered[:limit]


# 使用示例
if __name__ == "__main__":
    client = MediaCrawlerClient()

    # 示例1: 使用自定义的抖音达人发现脚本（推荐）
    print("=== 运行抖音达人发现脚本 ===")
    result = client.run_discover_creators()
    if result['success']:
        print("✅ 达人发现完成")
        # 加载并展示结果
        creators_data = client.load_discovered_creators()
        if creators_data:
            print(f"发现 {creators_data['total_creators']} 个达人")
            top_creators = client.get_top_creators(min_followers=50000, limit=5)
            if top_creators:
                print("\n前5名优质达人:")
                for i, creator in enumerate(top_creators, 1):
                    print(f"{i}. {creator['creator_name']} - 粉丝: {creator['follower_count']:,}")
    else:
        print(f"❌ 执行失败: {result.get('error', result.get('stderr'))}")

    # 示例2: 搜索小红书美妆博主
    # print("\n=== 搜索小红书美妆博主 ===")
    # result = client.search_creators(
    #     platform="xhs",
    #     keywords="美妆博主,护肤达人",
    #     max_count=10
    # )
    # print(f"执行结果: {result['success']}")

    # 示例3: 获取指定创作者详情
    # result = client.get_creator_detail(
    #     platform="xhs",
    #     creator_id="5c9e3e3e0000000007009d3e"
    # )

    # 示例4: 获取指定帖子详情
    # result = client.get_post_detail(
    #     platform="xhs",
    #     post_ids="65f3e3e3e3e3e3e3e3e3e3e3"
    # )
