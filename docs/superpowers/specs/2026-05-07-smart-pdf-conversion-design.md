# anyfile2md 智能 PDF 转换设计

**版本**: 2.0
**日期**: 2026-05-07
**状态**: 已修订（整合评审意见）

---

## 1. 概述

### 目标
将 anyfile2md 从单一 markitdown 引擎升级为**智能双引擎架构**，自动识别 PDF 复杂度并选择最佳转换方案。

### 核心思路
- **默认自动选择** + **用户可手动指定**
- 简单 PDF 用 markitdown（快速）
- 复杂 PDF 用 MinerU（高质量）
- 渐进式实现，先提示后自动

---

## 2. 架构设计

### 2.1 双引擎架构

```
convert.py
├── detect_complexity()     # 加权评分模型
├── convert_engine()       # 统一接口
├── markitdown_converter    # markitdown 引擎
├── mineru_converter       # MinerU 引擎
└── quality_checker        # 质量检测
```

### 2.2 引擎注册机制

```python
class BaseConverter(ABC):
    """引擎基类"""
    @property
    def name(self) -> str: ...

    @property
    def priority(self) -> int: ...

    def can_handle(self, file_path) -> float:
        """返回 0-1 的置信度"""
        ...

    def convert(self, input_path, output_path) -> ConversionResult:
        ...
```

**优先级**：数字越小优先级越高

```python
class MarkitdownConverter(BaseConverter):
    name = "markitdown"
    priority = 10  # 默认先用 markitdown

    def can_handle(self, file_path) -> float:
        # 简单文档高置信度
        if is_simple_pdf(file_path):
            return 0.9
        return 0.3

class MineruConverter(BaseConverter):
    name = "mineru"
    priority = 20

    def can_handle(self, file_path) -> float:
        # 复杂文档高置信度
        if is_complex_pdf(file_path):
            return 0.9
        return 0.3
```

### 2.3 多级回退机制

```
转换请求
    │
    ▼
┌─────────────────┐
│  尝试引擎1      │
│  (高优先级)      │
└────────┬────────┘
         │ 失败
         ▼
┌─────────────────┐
│  记录失败原因    │
│  (日志)         │
└────────┬────────┘
         │ 失败
         ▼
┌─────────────────┐
│  尝试引擎2      │
│  (次优先级)     │
└────────┬────────┘
         │
         ▼
    全部失败
    返回错误 + 解决方案
```

---

## 3. 复杂度检测

### 3.1 加权评分模型

| 检测项 | 权重 | 阈值 | 说明 |
|--------|------|------|------|
| 页数 | 1 | > 10 页 +1分 | 长文档更可能复杂 |
| 页眉页脚 | 2 | 检测到 +2分 | 连续3页相同文本 |
| 多栏布局 | 3 | 检测到 +3分 | 乱码率 > 5% |
| 跨页表格 | 3 | 检测到 +3分 | PyMuPDF 表格检测 |
| 非中文占比 | 1 | < 70% +1分 | 中文文档优先 MinerU |
| 扫描文档 | 5 | 检测到 +5分 | 图像型 PDF |

**评分阈值**：
- 0-3 分：markitdown
- 4-7 分：提示用户选择
- 8+ 分：MinerU

### 3.2 快速预检（< 1秒）

```python
def quick_check(file_path) -> dict:
    """快速预检，不实际转换"""
    return {
        "page_count": get_page_count(file_path),
        "has_headers_footers": detect_header_footer(file_path),
        "language_ratio": detect_language_ratio(file_path),
        "is_scanned": is_image_based_pdf(file_path),
    }
```

### 3.3 质量检测（转换后）

```python
def quality_check(md_content) -> QualityResult:
    """检测转换质量"""
    return {
        "garbled_ratio": count_garbled_chars() / total_chars,
        "table_integrity": check_table_structure(),
        "heading_structure": check_heading_hierarchy(),
        "总分": weighted_score
    }
```

**质量阈值**：
- 乱码率 > 5%：自动重试或切换引擎
- 表格破损：记录警告

---

## 4. 接口设计

### 4.1 命令行参数

```bash
# 自动选择（默认）
python convert.py --input doc.pdf --output doc.md

# 强制指定引擎
python convert.py --input doc.pdf --output doc.md -e mineru
python convert.py --input doc.pdf --output doc.md -e markitdown

# 列出可用引擎
python convert.py --list-engines

# 优化选项
python convert.py --input doc.pdf --output doc.md \
    --optimize term,toc,format

# 强制复杂度检测
python convert.py --input doc.pdf --output doc.md \
    --auto-select
```

### 4.2 帮助信息

```bash
$ python convert.py --help

用法: convert.py [选项]

选项:
  -i, --input FILE          输入文件
  -o, --output FILE         输出文件
  -e, --engine ENGINE       转换引擎: markitdown, mineru, auto
                           (默认: auto)
  --optimize OPTS           优化选项: term,toc,format,technical
                           term: 术语自动编号
                           toc: 生成目录
                           format: 标准化标题层级
                           technical: 等同于 term,toc,format
  --auto-select            强制使用自动选择
  --list-engines          列出可用引擎
  --list-formats           列出支持格式
  --plugins               启用插件（OCR等）
  -h, --help              显示帮助
```

### 4.3 引擎选择逻辑

```
用户指定引擎?
    │
    ├── 否 → 检测复杂度
    │         │
    │         ├── 0-3分 → markitdown + 提示
    │         ├── 4-7分 → 询问用户
    │         └── 8+分  → MinerU + 提示
    │
    └── 是 → 使用指定引擎
              │
              └── 失败 → 回退到次优先级引擎
```

### 4.4 输出示例

```bash
# 自动选择成功
$ python convert.py -i doc.pdf -o doc.md
检测复杂度: 8分 (多栏布局, 跨页表格)
已自动选择: MinerU (高质量模式)
转换完成 ✓
- 术语编号: 127 条
- 目录: 已生成
- 质量评分: 95/100

# 指定引擎
$ python convert.py -i doc.pdf -o doc.md -e mineru
转换完成 ✓ [MinerU]

# 引擎不可用
$ python convert.py -i doc.pdf -o doc.md -e mineru
错误: MinerU 不可用

解决方案:
1. 安装 MinerU: pip install mineru
2. 或使用 markitdown: -e markitdown

# 询问用户
$ python convert.py -i doc.pdf -o doc.md
检测复杂度: 5分 (中度复杂)
请选择引擎:
  [1] markitdown (快速, 可能丢失格式)
  [2] MinerU (高质量, 需要 GPU)
选择 [1/2]:
```

---

## 5. 安装与依赖

### 5.1 分层安装

```bash
# 轻量安装（仅 markitdown）
bash install_deps.sh --lite

# 标准安装（markitdown + MinerU CPU）
bash install_deps.sh --standard

# 完整安装（markitdown + MinerU GPU + OCR）
bash install_deps.sh --full

# 仅 MinerU
bash install_deps.sh --mineru
```

### 5.2 硬件要求

| 模式 | 内存 | 磁盘 | GPU |
|------|------|------|-----|
| markitdown | 4GB | 1GB | ❌ |
| MinerU CPU | 16GB | 20GB SSD | ❌ |
| MinerU GPU | 32GB | 20GB SSD | 4GB+ |

### 5.3 环境检测

```python
def check_engine_availability() -> dict:
    return {
        "markitdown": which("markitdown"),
        "mineru": which("mineru"),
        "gpu_available": check_gpu(),
        "memory": psutil.virtual_memory().total,
    }
```

---

## 6. 错误处理

### 6.1 统一错误模板

```python
class ConversionError(Exception):
    def __init__(self, engine, reason, solutions):
        self.engine = engine
        self.reason = reason
        self.solutions = solutions

    def __str__(self):
        return f"""错误: {self.engine} 转换失败
原因: {self.reason}

解决方案:
{chr(10).join(f"  {i+1}. {s}" for i, s in enumerate(self.solutions))}"""
```

### 6.2 失败日志

```json
{
  "timestamp": "2026-05-07T10:30:00",
  "file": "doc.pdf",
  "attempts": [
    {
      "engine": "mineru",
      "error": "GPU not available",
      "fallback_used": false
    },
    {
      "engine": "markitdown",
      "error": null,
      "fallback_used": true,
      "quality_score": 72
    }
  ],
  "final_result": "markitdown",
  "quality_warnings": ["low_score"]
}
```

---

## 7. 优化选项

### 7.1 术语自动编号

```python
def optimize_term_numbering(md_content) -> str:
    """识别并编号术语"""
    # 识别模式: 3.1.1 数据 data
    # 输出: ### 3.1.1 数据 data (统一格式)
```

### 7.2 目录生成

```python
def optimize_toc(md_content) -> str:
    """生成目录"""
    # 结合标题层级 + 术语编号
```

### 7.3 格式标准化

```python
def optimize_format(md_content) -> str:
    """标准化标题层级"""
    # 确保 # ## ### 正确嵌套
```

---

## 8. 实现计划

### 阶段 1: 基础框架
- [ ] 引擎基类 `BaseConverter`
- [ ] `markitdown_converter` 实现
- [ ] `mineru_converter` 存根
- [ ] 基础 `--engine` 参数

### 阶段 2: 复杂度检测
- [ ] 加权评分模型
- [ ] 快速预检函数
- [ ] `--auto-select` 逻辑

### 阶段 3: 回退机制
- [ ] 多级回退逻辑
- [ ] 失败日志
- [ ] 错误提示模板

### 阶段 4: MinerU 集成
- [ ] `mineru_converter` 完整实现
- [ ] GPU/CPU 模式检测
- [ ] 质量检测

### 阶段 5: 优化功能
- [ ] 术语编号
- [ ] 目录生成
- [ ] 格式标准化

---

## 9. 评审改进点（已整合）

| 评审意见 | 改进措施 |
|---------|---------|
| 复杂度检测阈值单一 | 改用加权评分模型 |
| 回退机制单向 | 增加多级回退 + 失败日志 |
| 缺少质量评估 | Post-convert quality check |
| 参数命名专业 | `--backend` → `--engine` + `-e` 别名 |
| 错误提示不足 | 统一错误模板 + 解决方案 |
| 硬件要求过高 | 分层安装 + CPU/GPU 自动检测 |

---

## 10. 风险与缓解

| 风险 | 缓解措施 |
|------|---------|
| MinerU 安装复杂 | 分层安装，markitdown 默认 |
| 32GB 内存要求 | CPU 模式可用，提示用户 |
| 误判复杂度 | 询问用户而非强行切换 |
| 回退死循环 | 限制回退次数 = 2 |
