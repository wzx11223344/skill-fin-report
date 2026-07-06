# Financial Report Writer

AI 驱动的结构化金融分析报告生成工具。基于 akshare 实时数据 + Jinja2 模板引擎，生成专业券商研报风格的 HTML/PDF 报告。

## 功能

| 报告类型 | 命令 | 说明 |
|---------|------|------|
| 个股分析报告 | `stock` | 公司概况、财务指标、估值分析、技术面、风险提示 |
| 行业研报 | `industry` | 行业规模、竞争格局、产业链、龙头对比、投资建议 |
| 市场周报 | `weekly` | 行情回顾、资金流向、涨跌排行、北向资金、下周展望 |

## 安装

```bash
pip install -r requirements.txt
```

## 使用示例

```bash
# 个股分析 - 贵州茅台
python report.py stock --ticker 600519

# 个股分析 - 宁德时代 (指定输出路径)
python report.py stock --ticker 300750 --output reports/ndsd.html

# 行业研报
python report.py industry --sector 新能源汽车

# 市场周报
python report.py weekly --market A股

# 导出 PDF
python report.py stock --ticker 600519 --format pdf
```

## 目录结构

```
skill-fin-report/
├── SKILL.md           # ClawHub 技能定义
├── README.md          # 项目文档
├── requirements.txt   # Python 依赖
├── report.py          # CLI 入口脚本
└── templates/         # Jinja2 HTML 模板
    ├── stock.html     # 个股分析模板
    ├── industry.html  # 行业研报模板
    └── weekly.html    # 市场周报模板
```

## 数据来源

本工具通过 [akshare](https://github.com/akfamily/akshare) 获取公开金融数据：

- **个股行情**: 东方财富
- **财务数据**: 同花顺
- **行业板块**: 东方财富行业分类
- **资金流向**: 东方财富资金流

## 许可证

MIT
