# anyfile2md 待办事项

> 创建时间: 2026-05-08
> 更新时间: 2026-05-08
> 状态: 已完成 ✅

---

## Phase 1-4 完成摘要

### 核心功能

| 功能 | 状态 | 说明 |
|------|------|------|
| 引擎抽象框架 | ✅ | BaseConverter, ConversionResult |
| 复杂度检测 | ✅ | ComplexityDetector, 28x 提速 |
| Fallback机制 | ✅ | FallbackHandler, 自动切换引擎 |
| MinerU集成 | ✅ | do_parse API, GPU/MPS 支持 |
| 批量转换CLI | ✅ | BatchProcessor, 并发处理 |
| 错误处理 | ✅ | 0字节检测, 空内容验证 |

### 测试覆盖

| 测试类别 | 数量 | 状态 |
|---------|------|------|
| 批量处理器测试 | 24 | ✅ |
| 复杂度检测测试 | 22 | ✅ |
| 置信度评分测试 | 10 | ✅ |
| 转换脚本测试 | 12 | ✅ |
| 转换器测试 | 15 | ✅ |
| Fallback机制测试 | 7 | ✅ |
| MinerU API测试 | 3 | ✅ |
| **总计** | **99** | **全部通过** |

---

## 技术指标

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 复杂度分析 | 426ms | 15ms | **28.5x** |
| 测试覆盖 | - | 99 | - |
| GB-T 转换成功率 | - | 3/6 | - |

---

## 提交记录 (2026-05-08)

| Commit | 描述 |
|--------|------|
| `30135a9` | refactor: architecture improvements (DI, singleton, caching, SRP) |
| `3364897` | fix: add empty output detection for 0-byte file fallback |
| `51462c6` | feat(batch): add concurrent processing with engine-aware routing |
| `ac8ea1a` | perf: optimize complexity detection 28x faster |
| `d275ec5` | perf: add timing debug log for complexity analysis |
| `fc9da1b` | refactor: add detector caching and injection support |
| `d936da0` | test(batch): add integration test |
| `d189dbf` | feat(batch): add CLI entry point |
| `73193a6` | feat(batch): add BatchProcessor |

---

## 架构改进详情

### 已完成的5个改进

1. **BaseConverter 构造器注入** - `__init__(detector)` 替代类级别 `_detector`
2. **EngineRegistry 单例重构** - 模块级 `_registry` 实例
3. **FallbackHandler preferred_engine** - 优先使用指定引擎
4. **is_available() 缓存** - 模块级缓存避免重复调用
5. **FallbackHandler 职责分离** - 拆分为 `_get_sorted_engines`, `_attempt_conversion`, `_write_log`

---

## 已知问题

### MinerU 模型下载 (已解决)

**问题:** 默认从 HuggingFace 下载模型超时

**解决方案:**
```bash
export MINERU_MODEL_SOURCE=modelscope
```

### Apple Silicon MPS (已支持)

**检测逻辑:**
```python
if nvidia-smi 可用:
    → hybrid-auto-engine (NVIDIA GPU)
elif torch.backends.mps.is_available():
    → hybrid-auto-engine (Apple Silicon MPS)
else:
    → pipeline (CPU)
```

---

## Phase 5 建议

| 事项 | 优先级 | 说明 |
|------|--------|------|
| MinerU 超时配置 | 中 | 添加可配置超时，避免长时间卡住 |
| 自动降级策略 | 中 | MinerU 超时后自动切换 MarkItDown |
| 进度条美化 | 低 | 添加更友好的 CLI 进度显示 |
| 文档完善 | 低 | 补充 CLI 详细使用说明 |

---

## 使用方法

### 单文件转换
```bash
python -m scripts.convert --input file.pdf --output out.md
```

### 批量转换
```bash
python -m scripts.batch --input <目录> --output <输出目录>
```

### 指定引擎
```bash
python -m scripts.convert --input file.pdf --output out.md --engine mineru
```

### 环境变量
```bash
export MINERU_MODEL_SOURCE=modelscope  # 国内用户推荐
```
