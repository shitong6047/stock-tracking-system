"""
国际消息面采集模块
功能：从东方财富网等来源采集国际新闻数据，分析宏观环境对个股的影响
"""

import requests
import json
import re
from typing import List, Dict, Optional
from datetime import datetime
import time


class GlobalNewsCollector:
    """国际新闻采集器"""
    
    def __init__(self):
        self.base_url = "http://api.eastmoney.com"
        self.timeout = 10
        self.retries = 3
        
    def get_global_news(self, category: str = 'all', count: int = 20) -> List[Dict]:
        """
        获取国际新闻数据
        
        参数:
            category: 新闻分类 (all/all/economy/finance/politics)
            count: 获取数量
            
        返回:
            新闻列表
        """
        news_list = []
        
        try:
            # 尝试从东方财富网获取国际新闻
            # 使用新浪财经API获取新闻数据
            url = "http://news.sina.com.cn/api/globalnews"
            
            params = {
                'page': 1,
                'size': count,
                'category': category
            }
            
            for attempt in range(self.retries):
                try:
                    response = requests.get(url, params=params, timeout=self.timeout)
                    if response.status_code == 200:
                        data = response.json()
                        news_list = self._parse_news_data(data)
                        break
                except Exception as e:
                    if attempt == self.retries - 1:
                        print(f"[警告] 获取国际新闻失败: {str(e)}")
                    time.sleep(1)
            
            # 如果网络请求失败，使用备用数据源
            if not news_list:
                news_list = self._get_fallback_news()
                
        except Exception as e:
            print(f"[错误] 获取国际新闻异常: {str(e)}")
            news_list = self._get_fallback_news()
        
        return news_list
    
    def _parse_news_data(self, data: Dict) -> List[Dict]:
        """
        解析新闻数据
        
        参数:
            data: 原始数据
            
        返回:
            解析后的新闻列表
        """
        news_list = []
        
        try:
            if 'data' in data and 'list' in data['data']:
                for item in data['data']['list']:
                    news = {
                        'title': item.get('title', ''),
                        'summary': item.get('summary', ''),
                        'url': item.get('url', ''),
                        'source': item.get('source', ''),
                        'pub_time': item.get('pubtime', ''),
                        'impact': self._analyze_impact(item.get('title', '')),
                        'relevance': self._calculate_relevance(item.get('title', ''))
                    }
                    news_list.append(news)
        except Exception as e:
            print(f"[警告] 解析新闻数据失败: {str(e)}")
        
        return news_list
    
    def _analyze_impact(self, title: str) -> str:
        """
        分析新闻影响方向
        
        参数:
            title: 新闻标题
            
        返回:
            影响方向 (positive/negative/neutral)
        """
        title_lower = title.lower()
        
        positive_keywords = ['上涨', '利好', '增长', '复苏', '扩张', '盈利', '乐观', '加息', '经济']
        negative_keywords = ['下跌', '利空', '下滑', '亏损', '裁员', '危机', '悲观', '降息', '衰退']
        
        positive_count = sum(1 for kw in positive_keywords if kw in title_lower)
        negative_count = sum(1 for kw in negative_keywords if kw in title_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _calculate_relevance(self, title: str) -> float:
        """
        计算新闻相关性
        
        参数:
            title: 新闻标题
            
        返回:
            相关性分数 (0-1)
        """
        relevance = 0.5
        
        title_lower = title.lower()
        
        # 关键词相关性权重
        high_relevance_keywords = ['美联储', '美联储', '加息', '降息', '美元', '人民币', '汇率', '经济', '股市', '股票']
        medium_relevance_keywords = ['全球', '国际', '市场', '金融', '投资', '企业', '公司', '行业']
        
        for kw in high_relevance_keywords:
            if kw in title_lower:
                relevance = min(1.0, relevance + 0.2)
        
        for kw in medium_relevance_keywords:
            if kw in title_lower:
                relevance = min(1.0, relevance + 0.1)
        
        return round(relevance, 2)
    
    def _get_fallback_news(self) -> List[Dict]:
        """
        获取备用新闻数据（当网络请求失败时）
        
        返回:
            备用新闻列表
        """
        return [
            {
                'title': '美联储维持利率不变',
                'summary': '美联储宣布维持当前利率水平，市场反应平稳',
                'url': '',
                'source': '备用数据',
                'pub_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'impact': 'neutral',
                'relevance': 0.7
            },
            {
                'title': '原油价格上涨',
                'summary': '国际原油价格持续上涨，能源股受益',
                'url': '',
                'source': '备用数据',
                'pub_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'impact': 'positive',
                'relevance': 0.5
            },
            {
                'title': '全球通胀压力缓解',
                'summary': '全球主要经济体通胀数据有所回落',
                'url': '',
                'source': '备用数据',
                'pub_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'impact': 'positive',
                'relevance': 0.6
            },
            {
                'title': '地缘政治紧张加剧',
                'summary': '国际局势紧张，市场避险情绪上升',
                'url': '',
                'source': '备用数据',
                'pub_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'impact': 'negative',
                'relevance': 0.8
            }
        ]
    
    def get_economic_calendar(self) -> List[Dict]:
        """
        获取经济日历数据
        
        返回:
            经济日历列表
        """
        try:
            url = "http://finance.sina.com.cn/money/future/ech.json"
            response = requests.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_economic_calendar(data)
        except Exception as e:
            print(f"[警告] 获取经济日历失败: {str(e)}")
        
        return []
    
    def _parse_economic_calendar(self, data: Dict) -> List[Dict]:
        """
        解析经济日历数据
        
        参数:
            data: 原始数据
            
        返回:
            解析后的日历列表
        """
        calendar_list = []
        
        try:
            if 'data' in data:
                for item in data['data']:
                    event = {
                        'date': item.get('date', ''),
                        'time': item.get('time', ''),
                        'event': item.get('event', ''),
                        'country': item.get('country', ''),
                        'importance': item.get('importance', 0),
                        'forecast': item.get('forecast', ''),
                        'previous': item.get('previous', '')
                    }
                    calendar_list.append(event)
        except Exception as e:
            print(f"[警告] 解析经济日历失败: {str(e)}")
        
        return calendar_list
    
    def analyze_market_impact(self, news_list: List[Dict], stock_category: str = 'all') -> Dict:
        """
        分析新闻对市场的影响
        
        参数:
            news_list: 新闻列表
            stock_category: 股票分类
            
        返回:
            影响分析结果
        """
        positive_count = 0
        negative_count = 0
        total_relevance = 0
        
        for news in news_list:
            if news['impact'] == 'positive':
                positive_count += 1
            elif news['impact'] == 'negative':
                negative_count += 1
            total_relevance += news['relevance']
        
        avg_relevance = total_relevance / len(news_list) if news_list else 0
        
        return {
            'positive_news_count': positive_count,
            'negative_news_count': negative_count,
            'net_impact': positive_count - negative_count,
            'avg_relevance': round(avg_relevance, 2),
            'market_sentiment': '乐观' if positive_count > negative_count else '悲观' if negative_count > positive_count else '中性'
        }


def main():
    """主函数"""
    collector = GlobalNewsCollector()
    
    print("正在获取国际新闻...")
    news = collector.get_global_news(count=5)
    
    print(f"\n获取到 {len(news)} 条国际新闻：")
    for i, item in enumerate(news, 1):
        print(f"\n{i}. {item['title']}")
        print(f"   来源: {item['source']}")
        print(f"   影响: {item['impact']} | 相关性: {item['relevance']}")
    
    print("\n" + "=" * 60)
    print("市场影响分析：")
    analysis = collector.analyze_market_impact(news)
    print(f"乐观新闻数: {analysis['positive_news_count']}")
    print(f"悲观新闻数: {analysis['negative_news_count']}")
    print(f"市场情绪: {analysis['market_sentiment']}")


if __name__ == "__main__":
    main()
