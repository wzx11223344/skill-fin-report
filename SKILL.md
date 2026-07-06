---
name: "financial-report-writer"
description: "Auto-generate structured financial analysis reports. Invoke when user asks for financial reports, stock analysis, investment reports, or market summaries in document format."
---

# 金融报告生成 (Financial Report Writer)

自动生成结构化金融分析报告。支持个股分析、行业研报、市场周报三种报告类型，输出专业排版的 HTML/PDF。

## 触发条件

- "写一份XX股票分析报告" / "分析一下XX公司" / "给我一份XX行业报告"
- "生成投资报告" / "市场周报" / "financial report" / "stock analysis report"

## 报告模板

### 1. 个股分析报告
- 公司概况与主营业务
- 财务指标分析 (ROE/ROA/毛利率/净利率)
- 估值分析 (PE/PB/PS分位数)
- 机构持仓与评级
- 技术面分析
- 风险提示

### 2. 行业研报
- 行业规模与增长
- 竞争格局分析
- 产业链梳理
- 龙头企业对比
- 投资建议

### 3. 市场周报
- 本周行情回顾
- 资金流向分析
- 行业涨跌排行
- 北向资金动态
- 下周展望

## 使用方法

```
python report.py stock --ticker 600519
python report.py industry --sector 新能源汽车
python report.py weekly --market A股
```

## 技术栈
- 数据: akshare (股票/行业数据)
- 模板: jinja2
- 样式: 专业券商研报风格CSS
