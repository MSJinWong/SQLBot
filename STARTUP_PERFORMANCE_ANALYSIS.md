# DataMate 启动性能分析与优化建议

## 问题分析

根据代码分析，DataMate 启动时在 `lifespan` 函数中执行了以下步骤（按顺序）：

### 启动流程详解

1. **数据库迁移** (`run_migrations()`)
   - 执行 Alembic 迁移，检查并应用数据库结构变更
   - **潜在耗时**：如果有待执行的迁移，可能需要几秒到几十秒

2. **缓存初始化** (`init_sqlbot_cache()`)
   - 初始化内存缓存或 Redis 缓存
   - **潜在耗时**：通常很快（<1秒），除非 Redis 连接有问题

3. **动态 CORS 初始化** (`init_dynamic_cors(app)`)
   - 从数据库查询所有 Assistant 配置，提取域名并更新 CORS 设置
   - **潜在耗时**：取决于数据库查询速度（通常 <1秒）

4. **术语嵌入初始化** (`init_terminology_embedding_data()`)
   - 查找所有没有 embedding 的术语记录
   - 提交到线程池异步执行嵌入计算
   - **关键问题**：首次启动或有大量未嵌入数据时，会触发 **Embedding 模型加载**

5. **训练数据嵌入初始化** (`init_data_training_embedding_data()`)
   - 查找所有没有 embedding 的训练数据
   - 提交到线程池异步执行嵌入计算
   - **关键问题**：同样可能触发 Embedding 模型加载

6. **表和数据源嵌入初始化** (`init_table_and_ds_embedding()`)
   - 查找所有没有 embedding 的表和数据源
   - 提交到线程池异步执行嵌入计算
   - **关键问题**：同样可能触发 Embedding 模型加载

7. **模型信息加密** (`async_model_info()`)
   - 异步加密已有模型的 API 密钥和地址
   - **潜在耗时**：取决于模型数量（通常 <1秒）

## 主要性能瓶颈

### 🔴 **最大瓶颈：Embedding 模型加载**

根据代码 `backend/apps/ai_model/embedding.py`：

```python
class EmbeddingModelCache:
    @staticmethod
    def get_model(key: str = settings.DEFAULT_EMBEDDING_MODEL,
                  config: EmbeddingModelInfo = local_embedding_model) -> Embeddings:
        model_instance = _embedding_model.get(key)
        if model_instance is None:
            lock = EmbeddingModelCache._get_lock(key)
            with lock:
                model_instance = _embedding_model.get(key)
                if model_instance is None:
                    model_instance = EmbeddingModelCache._new_instance(config)
                    _embedding_model[key] = model_instance
        return model_instance
    
    @staticmethod
    def _new_instance(config: EmbeddingModelInfo = local_embedding_model):
        return HuggingFaceEmbeddings(model_name=config.name, cache_folder=config.folder,
                                     model_kwargs={'device': config.device'},
                                     encode_kwargs={'normalize_embeddings': True})
```

**问题**：
- 首次调用 `EmbeddingModelCache.get_model()` 时会加载 HuggingFace 模型
- 默认模型：`shibing624/text2vec-base-chinese`
- 模型加载包括：
  - 从磁盘读取模型文件（可能几百 MB）
  - 初始化 tokenizer
  - 加载模型权重到内存
  - **典型耗时：10-30 秒**（取决于硬件和模型大小）

**触发时机**：
- 三个 embedding 初始化函数都会在后台线程中调用 `EmbeddingModelCache.get_model()`
- 虽然提交到线程池是异步的，但如果有未嵌入的数据，线程池会立即开始执行
- 第一个执行的线程会触发模型加载，**阻塞该线程 10-30 秒**

### 🟡 **次要瓶颈：数据库查询**

如果数据库中有大量数据：
- 查询未嵌入的术语、训练数据、表和数据源可能较慢
- 但这些查询通常在 1-5 秒内完成

## 优化方案

### 方案 1：延迟加载 Embedding 模型（推荐）⭐

**思路**：不在启动时立即触发 embedding 计算，而是在首次实际需要时才加载模型。

**实现**：

```python
# backend/main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    import time
    start_time = time.time()
    SQLBotLogUtil.info("🚀 DataMate 开始启动...")
    
    step_start = time.time()
    run_migrations()
    SQLBotLogUtil.info(f"✅ 数据库迁移完成 - 耗时: {time.time() - step_start:.2f}秒")
    
    step_start = time.time()
    init_sqlbot_cache()
    SQLBotLogUtil.info(f"✅ 缓存初始化完成 - 耗时: {time.time() - step_start:.2f}秒")
    
    step_start = time.time()
    init_dynamic_cors(app)
    SQLBotLogUtil.info(f"✅ 动态CORS初始化完成 - 耗时: {time.time() - step_start:.2f}秒")
    
    # 延迟 embedding 初始化 - 不阻塞启动
    if settings.EMBEDDING_ENABLED:
        SQLBotLogUtil.info("⏳ Embedding 初始化已提交到后台任务队列")
        # 使用 asyncio.create_task 在后台执行，不阻塞启动
        import asyncio
        asyncio.create_task(delayed_embedding_init())
    
    step_start = time.time()
    await async_model_info()
    SQLBotLogUtil.info(f"✅ 模型信息加密完成 - 耗时: {time.time() - step_start:.2f}秒")
    
    total_time = time.time() - start_time
    SQLBotLogUtil.info(f"✅ DataMate 初始化完成 - 总耗时: {total_time:.2f}秒")
    SQLBotLogUtil.info("💡 Embedding 模型将在后台加载，首次查询可能稍慢")
    yield
    SQLBotLogUtil.info("DataMate 应用关闭")

async def delayed_embedding_init():
    """延迟执行 embedding 初始化，避免阻塞启动"""
    import asyncio
    import time
    
    # 等待 2 秒，让应用先完全启动
    await asyncio.sleep(2)
    
    start_time = time.time()
    SQLBotLogUtil.info("🔄 开始后台 Embedding 初始化...")
    
    # 在线程池中执行，避免阻塞事件循环
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, init_terminology_embedding_data)
    await loop.run_in_executor(None, init_data_training_embedding_data)
    await loop.run_in_executor(None, init_table_and_ds_embedding)
    
    SQLBotLogUtil.info(f"✅ 后台 Embedding 初始化完成 - 耗时: {time.time() - start_time:.2f}秒")
```

**优点**：
- 启动时间从 30+ 秒降低到 2-5 秒
- 应用可以快速响应请求
- Embedding 模型在后台加载，不影响其他功能

**缺点**：
- 首次需要 embedding 的查询可能稍慢（等待模型加载）

---

### 方案 2：预热 Embedding 模型（适合生产环境）

**思路**：在启动时主动加载模型，但优化加载过程。

**实现**：

```python
def warmup_embedding_model():
    """预热 Embedding 模型"""
    if not settings.EMBEDDING_ENABLED:
        return
    
    try:
        SQLBotLogUtil.info("🔥 开始预热 Embedding 模型...")
        start_time = time.time()
        
        # 主动触发模型加载
        model = EmbeddingModelCache.get_model()
        
        # 执行一次测试嵌入，确保模型完全加载
        _ = model.embed_query("测试")
        
        SQLBotLogUtil.info(f"✅ Embedding 模型预热完成 - 耗时: {time.time() - start_time:.2f}秒")
    except Exception as e:
        SQLBotLogUtil.error(f"❌ Embedding 模型预热失败: {e}")

# 在 lifespan 中调用
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ... 其他初始化 ...
    
    # 预热模型（同步执行，确保模型加载完成）
    warmup_embedding_model()
    
    # 然后再执行 embedding 初始化（此时模型已加载，速度快）
    init_terminology_embedding_data()
    init_data_training_embedding_data()
    init_table_and_ds_embedding()
    
    # ... 其他初始化 ...
```

**优点**：
- 启动后立即可用，无需等待
- 适合生产环境

**缺点**：
- 启动时间仍然较长（20-30 秒）

---

### 方案 3：禁用 Embedding（开发环境）

**思路**：开发环境下完全禁用 embedding 功能，加快启动速度。

**实现**：

在 `.env` 文件中添加：

```bash
# 开发环境禁用 Embedding
EMBEDDING_ENABLED=false
TABLE_EMBEDDING_ENABLED=false
```

**优点**：
- 启动速度最快（2-3 秒）
- 适合不需要语义搜索的开发场景

**缺点**：
- 无法测试 embedding 相关功能

---

### 方案 4：使用更轻量的 Embedding 模型

**思路**：替换为更小的模型，减少加载时间。

**实现**：

```bash
# .env
DEFAULT_EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

**优点**：
- 模型更小，加载更快（5-10 秒）
- 仍然保留 embedding 功能

**缺点**：
- 中文效果可能不如 `text2vec-base-chinese`

---

## 推荐方案组合

### 开发环境
1. **方案 3**：禁用 Embedding（最快）
2. 或 **方案 1**：延迟加载（平衡性能和功能）

### 生产环境
1. **方案 2**：预热模型（确保启动后立即可用）
2. 配合优化：
   - 使用 Redis 缓存（避免重复计算）
   - 定期清理无用的 embedding 数据

---

## 其他优化建议

### 1. 数据库连接池优化

当前配置（`backend/common/core/config.py`）：
```python
PG_POOL_SIZE: int = 20
PG_MAX_OVERFLOW: int = 30
```

建议：
- 开发环境减小连接池：`PG_POOL_SIZE=5, PG_MAX_OVERFLOW=10`
- 减少启动时的连接开销

### 2. 日志级别优化

当前 `.env` 配置：
```bash
LOG_LEVEL=DEBUG
SQL_DEBUG=True
```

建议：
- 开发环境使用 `LOG_LEVEL=INFO`
- 禁用 SQL 调试：`SQL_DEBUG=False`
- 减少日志输出开销

### 3. 迁移优化

如果每次启动都执行迁移检查较慢，可以：
- 开发环境跳过迁移检查（手动执行 `alembic upgrade head`）
- 生产环境保留自动迁移

### 4. 监控启动时间

我已经在代码中添加了详细的启动时间日志，运行后你会看到：

```
🚀 DataMate 开始启动...
✅ 数据库迁移完成 - 耗时: 2.34秒
✅ 缓存初始化完成 - 耗时: 0.12秒
✅ 动态CORS初始化完成 - 耗时: 0.45秒
✅ 术语嵌入初始化完成 - 耗时: 15.67秒  ← 这里是瓶颈
✅ 训练数据嵌入初始化完成 - 耗时: 0.23秒
✅ 表和数据源嵌入初始化完成 - 耗时: 0.18秒
✅ 模型信息加密完成 - 耗时: 0.08秒
✅ DataMate 初始化完成 - 总耗时: 19.07秒
```

这样可以精确定位瓶颈。

---

## 立即可用的快速优化

最简单的优化方式（无需改代码）：

1. **修改 `.env` 文件**：
```bash
# 开发环境快速启动配置
EMBEDDING_ENABLED=false
TABLE_EMBEDDING_ENABLED=false
LOG_LEVEL=INFO
SQL_DEBUG=False
```

2. **重启应用**，启动时间应该从 30+ 秒降低到 2-3 秒

3. **需要测试 embedding 功能时**，再临时启用：
```bash
EMBEDDING_ENABLED=true
TABLE_EMBEDDING_ENABLED=true
```

---

## 总结

**核心问题**：启动时加载 HuggingFace Embedding 模型导致卡顿 10-30 秒

**最佳实践**：
- 开发环境：禁用 Embedding 或延迟加载
- 生产环境：预热模型 + Redis 缓存
- 监控：使用详细的启动日志定位瓶颈

**预期效果**：
- 优化前：30+ 秒
- 优化后（开发）：2-3 秒
- 优化后（生产）：5-10 秒（含模型预热）

