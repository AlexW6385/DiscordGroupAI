## Discord Group AI - 多人格群聊 Bot

一个面向 Discord 群聊的多人格 AI Bot：
- 决策层：先判断「要不要说话」「说多少」「语气是什么」。
- 生成层：再根据上下文和 persona 提示词生成自然的群聊回复。
- 多人格：一个进程里可以同时跑多只 bot，每只 bot 是一个独立人格（攻击型、创意型、温柔型、知识型）。


## 目录结构（与本次需求相关）

- `main.py`：进程入口，同时启动 FastAPI + 多个 Discord bot。
- `app/config.py`：全局配置（从 `.env` 加载）。
- `app/decision.py`：是否发言的决策逻辑（LLM + JSON schema）。
- `app/generation.py`：生成真正回复文本的逻辑。
- `app/discord_bot/bot.py`：根据 `RoleConfig` 创建具体的 Discord bot 实例。
- `app/role_config.py`：每个 role 的配置加载与合并逻辑。
- `prompts/decision.txt` / `prompts/generation.txt`：默认通用人格的提示词（单 bot 模式兜底）。
- `roles/`：每个角色一个子目录，完全独立配置与提示词：
  - `roles/aggressive/`：攻击型（辛辣讽刺、聪明直接）
  - `roles/creative/`：创意型（点子多、爱脑洞、能开新话题）
  - `roles/warm/`：温柔型（友好、女性化气质、惹人喜欢）
  - `roles/expert/`：知识型（知识渊博、善于解释和回答问题）


## 配置模型：全局 env + 每 role 独立 config

### 1. 全局 `.env`

路径：项目根目录下 `.env`（可参考 `.env.example`）。

只放**共用**配置：
- App & 日志：
  - `APP_NAME`, `DEBUG`, `LOG_DIR`
- LLM：
  - `OPENAI_API_KEY`
  - `DECISION_MODEL`, `DECISION_TEMPERATURE`, `DECISION_CONTEXT_MESSAGES`
  - `GENERATION_MODEL`, `GENERATION_TEMPERATURE`, `GENERATION_CONTEXT_MESSAGES`, `GENERATION_MIN_TOKENS`
- 数据库 / Redis：
  - `DATABASE_URL`, `REDIS_URL`
- 上下文配置：
  - `CONTEXT_MAX_HISTORY`, `CONTEXT_TTL_SECONDS`
- 单 bot / 多 bot 控制：
  - `DISCORD_BOT_TOKEN`, `DISCORD_CLIENT_ID`（仅单 bot 模式需要）
  - `ENABLED_ROLES`：多 role 模式时启用哪些人格
  - `RESPONSE_THRESHOLD`：单 bot 模式下的全局回复阈值
  - `DECISION_PROMPT_FILE`, `GENERATION_PROMPT_FILE`：单 bot 模式下使用的默认提示词


### 2. 每个 role 自己的配置与提示词

每个 role 一个文件夹：`roles/<name>/`，包含：

- `roles/<name>/config.yaml`
  - `discord_bot_token`: 该人格使用的 Discord Bot Token（必填）
  - `discord_client_id`: 该人格的 Application Client ID（必填）
  - `response_threshold`: 该人格的回复阈值（可选，默认 0.5）
  - 可选覆盖全局的 LLM 配置：
    - `decision_model`, `decision_temperature`, `decision_context_messages`
    - `generation_model`, `generation_temperature`, `generation_context_messages`, `generation_min_tokens`
  - `decision_prompt_file`, `generation_prompt_file`（一般不填）
    - 不填时默认指向本目录下的 `decision.txt` / `generation.txt`
    - 如要拆分成多个 variant，可以在这里指向其他路径

- `roles/<name>/decision.txt`
  - 决策 persona：说明这个人是什么性格、什么时候更愿意说话、打分标准、tone / max_words 等。

- `roles/<name>/generation.txt`
  - 说话 persona：真正发出去的消息风格，如何称呼别人、句式、幽默/温柔程度等。


### 3. 四个内置角色

#### aggressive（攻击型）
- 文件夹：`roles/aggressive/`
- 性格：辛辣讽刺、聪明、直接，喜欢抓别人话里的漏洞和装逼点。
- 用途：负责群里的「毒舌聪明人」，对弱论点/瞎说/吹牛更爱出手。

#### creative（创意型）
- 文件夹：`roles/creative/`
- 性格：点子多、爱脑洞、擅长开新话题和给建议。
- 用途：有人纠结「接下来干嘛」「有什么想法」时，这个人来给选项、出主意。

#### warm（温柔型）
- 文件夹：`roles/warm/`
- 性格：温柔、友好、略带女性化气质，让人觉得「很好相处」。
- 用途：别人分享、吐槽、受挫、开心或难过时给出温柔、贴心的反应。

#### expert（知识型）
- 文件夹：`roles/expert/`
- 性格：知识渊博、冷静，习惯清晰解释问题，像一个很懂的同学。
- 用途：有人问「是什么」「为什么」「怎么做」「有没有推荐」时，给清晰、简洁的回答。


## 运行模式

### 单人格模式（兼容旧用法）

不设置 `ENABLED_ROLES` 或让它为空时：
- 使用 `.env` 中的：
  - `DISCORD_BOT_TOKEN`, `DISCORD_CLIENT_ID`
  - `RESPONSE_THRESHOLD`
  - `DECISION_PROMPT_FILE`, `GENERATION_PROMPT_FILE`（或默认 `prompts/decision.txt` / `prompts/generation.txt`）
- 整个进程只跑一个人格。


### 多人格模式

设置 `.env`：

```env
ENABLED_ROLES=aggressive,creative,warm,expert
```

然后为每个 role 填好：
- `roles/aggressive/config.yaml`
- `roles/creative/config.yaml`
- `roles/warm/config.yaml`
- `roles/expert/config.yaml`

此时：
- 不再使用 `.env` 里的 `DISCORD_BOT_TOKEN` / `DISCORD_CLIENT_ID`；
- 进程会为 `ENABLED_ROLES` 里的每个名字启动一只 Discord bot；
- 每只 bot 用各自的 token、各自的阈值和各自的提示词人格。


## 快速上手步骤

1. 复制 `.env.example` 为 `.env`，填入：
   - `OPENAI_API_KEY`
   - `DATABASE_URL`, `REDIS_URL`
   - 根据需要设置 `ENABLED_ROLES`。

2. 为每个启用的 role 填写 `roles/<name>/config.yaml`：
   - `discord_bot_token`
   - `discord_client_id`
   - （可选）`response_threshold` 与模型覆盖参数。

3. 根据喜好微调四个角色各自目录下的 `decision.txt` / `generation.txt`。

4. 运行：
   ```bash
   cd discord_group_ai
   python main.py
   ```

5. 在对应的 Discord 服务器里把各个 bot 拉进需要的群，观察不同人格的发言效果。

