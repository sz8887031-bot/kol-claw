#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KOL投放管理系统 - 达人自动评级
根据报价、CPM、粉丝数自动评估达人级别
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / 'data'


class KOLGrader:
    """达人评级系统"""

    def __init__(self, csv_path=DATA_DIR / '达人跟进表.csv'):
        self.csv_path = csv_path
        self.target_cpm = 12  # 目标CPM

    def calculate_avg_views(self, row):
        """计算平均播放量（取最近4个有效数据）"""
        views = []
        for i in range(1, 6):
            val = row.get(f'播放{i}', np.nan)
            if pd.notna(val) and val > 0:
                views.append(float(val))

        if not views:
            return None

        # 取最近4个数据（如果有的话）
        recent_views = views[:4] if len(views) >= 4 else views
        return np.mean(recent_views)

    def calculate_cpm(self, price, avg_views):
        """计算CPM"""
        if not price or not avg_views or avg_views == 0:
            return None
        return (float(price) / float(avg_views)) * 1000

    def grade_kol(self, row):
        """
        达人评级逻辑：
        S级：超优质 - 有报价且CPM<8 或 报价<800
        A级：优质 - 有报价且CPM 8-12
        B级：合格 - 有报价且CPM 12-15
        C级：一般 - 有报价但CPM>15 或 数据不理想
        无评级：无报价且数据不足
        """
        # 获取报价
        price = row.get('报价', np.nan)
        fans = row.get('粉丝数', 0)

        # 如果没有报价，返回无评级
        if pd.isna(price) or price == '':
            return ''

        # 尝试转换为数字，如果失败则返回无评级
        try:
            price = float(price)
            if price == 0:
                return ''
        except (ValueError, TypeError):
            return ''

        # 计算平均播放量和CPM
        avg_views = self.calculate_avg_views(row)

        if not avg_views:
            # 没有播放数据，仅根据报价判断
            if price < 800:
                return 'S'
            elif price < 1500:
                return 'A'
            elif price < 3000:
                return 'B'
            else:
                return 'C'

        cpm = self.calculate_cpm(price, avg_views)

        if not cpm:
            return ''

        # 根据CPM评级
        if cpm < 8:
            return 'S'
        elif cpm < 12:
            return 'A'
        elif cpm < 15:
            return 'B'
        else:
            return 'C'

    def auto_grade_all(self):
        """自动评估所有达人"""
        if pd.isna(self.csv_path):
            print("❌ CSV文件路径无效")
            return

        df = pd.read_csv(self.csv_path, encoding='utf-8-sig')

        # 确保有达人级别字段
        if '达人级别' not in df.columns:
            df['达人级别'] = ''

        print("="*80)
        print(f"🎯 达人自动评级 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("="*80)
        print("\n评级标准：")
        print("  S级：超优质 - CPM<8 或 报价<800")
        print("  A级：优质 - CPM 8-12")
        print("  B级：合格 - CPM 12-15")
        print("  C级：一般 - CPM>15 或 数据不理想")
        print("  无评级：无报价或数据不足")
        print("\n" + "="*80)

        updated_count = 0
        unchanged_count = 0
        stats = {'S': 0, 'A': 0, 'B': 0, 'C': 0, '': 0}

        for idx, row in df.iterrows():
            # 跳过空行
            if pd.isna(row['达人昵称']) or not row['达人昵称']:
                continue

            old_grade = row['达人级别'] if pd.notna(row['达人级别']) else ''
            new_grade = self.grade_kol(row)

            # 更新评级
            df.at[idx, '达人级别'] = new_grade
            stats[new_grade] = stats.get(new_grade, 0) + 1

            # 如果评级有变化，打印详情
            if old_grade != new_grade:
                kol_name = row['达人昵称']
                price_raw = row.get('报价', 0)

                # 尝试转换报价为数字
                try:
                    price = float(price_raw) if price_raw else None
                except (ValueError, TypeError):
                    price = None

                avg_views = self.calculate_avg_views(row)

                # 安全计算CPM
                cpm = None
                if price and avg_views:
                    try:
                        cpm = self.calculate_cpm(price, avg_views)
                    except (ValueError, TypeError):
                        cpm = None

                print(f"\n📊 {kol_name}")
                print(f"   评级变化: {old_grade if old_grade else '未评级'} → {new_grade if new_grade else '未评级'}")
                if price:
                    print(f"   报价: {price}元")
                if cpm:
                    print(f"   CPM: {cpm:.2f}元")
                if avg_views:
                    print(f"   平均播放: {int(avg_views):,}")

                updated_count += 1
            else:
                unchanged_count += 1

        # 保存更新后的CSV
        df.to_csv(self.csv_path, index=False, encoding='utf-8-sig')

        print("\n" + "="*80)
        print("📈 评级统计")
        print("="*80)
        print(f"  S级（超优质）: {stats.get('S', 0)} 个")
        print(f"  A级（优质）: {stats.get('A', 0)} 个")
        print(f"  B级（合格）: {stats.get('B', 0)} 个")
        print(f"  C级（一般）: {stats.get('C', 0)} 个")
        print(f"  未评级: {stats.get('', 0)} 个")
        print(f"\n✅ 已更新 {updated_count} 个达人评级")
        print(f"⏭️  保持不变 {unchanged_count} 个")
        print(f"📁 已保存: {self.csv_path}")

        return df, stats


def main():
    """主函数"""
    grader = KOLGrader()
    grader.auto_grade_all()


if __name__ == '__main__':
    main()
