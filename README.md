# Discord Group AI - 智能多角色群聊框架

一个工业级的 Discord 群聊多角色 AI 框架。通过独特的“决策层+生成层”架构，实现高度拟人化、有社交分寸感的群聊互动。

## 🌟 核心特性

- **多角色并发**：单进程支持无限个独立 AI 角色，每个角色拥有独立 Token、性格定位（Persona）和配置。
- **双层架构**：
  - **决策引擎 (Decision Engine)**：LLM 根据上下文打分（0-1），判断“要不要说话”、“以什么语气说”、“说多少”。
  - **生成引擎 (Generation Engine)**：根据决策建议和特定 Persona 提示词生成极具个性的回复。
- **社交协调机制**：
  - **随机抖动 (Jitter)**：模拟人类思考时间，防止机器人秒回。
  - **Redis 分布式锁**：确保在激烈的群聊中，多个 Bot 不会同时对同一条消息进行回复，保持自然的对话节奏。
  - **防套娃机制**：内置提示词约束，严禁机器人之间进行无意义的疯狂互撩。
- **安全加固**：敏感信息（Token）全面支持环境变量覆盖，杜绝硬编码泄露风险。

## 📂 项目结构

- `main.py`：应用入口，整合 FastAPI 监控与 Discord Bot 运行。
- `app/`：
  - `role_config.py`：动态角色配置加载系统。
  - `decision.py` & `generation.py`：AI 核心逻辑。
  - `discord_bot/bot.py`：Discord 事件响应与协调逻辑。
  - `utils/logging.py`：精美的终端日志收集器，实时展示多 Bot 决策过程。
- `roles/`：角色定义目录。每个子目录代表一个独立人格：
  - `aggressive`：互联网毒舌乐子人。
  - `creative`：点子大王、话题开启者。
  - `warm`：温柔贴心的情感支柱。
  - `expert`：冷静、专业的知识百科。

## 🚀 快速开始

### 1. 环境准备
确保已安装 Python 3.10+，并配置好 PostgreSQL 和 Redis。

### 2. 配置环境变量
复制 `.env.example` 为 `.env` 并填写核心配置：
```env
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://...
ENABLED_ROLES=aggressive,creative,warm,expert
```

### 3. 配置角色 Token (安全推荐)
为了安全，建议在 `.env` 中为每个角色配置 Token，格式为 `DISCORD_BOT_TOKEN_{ROLE_NAME}`：
```env
DISCORD_BOT_TOKEN_AGGRESSIVE=MTQ...
DISCORD_BOT_TOKEN_CREATIVE=MTQ...
# 其他角色依此类推...
```

### 4. 角色微调
每个角色在 `roles/<name>/` 下都有 `decision.txt` 和 `generation.txt`，你可以随时修改这些文本来改变他们的“灵魂”。

### 5. 启动
```bash
python main.py
```

## 🛠 进阶配置

- **RESPONSE_THRESHOLD**：全局或角色单独设置。分值越高，Bot 越“高冷”，只有在认为非常有必要时才会发言。
- **Context Management**：通过 Redis 维护短时记忆，通过 PostgreSQL 存储长时记录。

