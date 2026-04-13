# ASR 模型对比测试（2026-04-12）

## 测试条件

- 音频：两段语音备忘录（约 1h + 1h），双人中文对话，含大量英文专有名词（Claude Code, Agent, Anthropic, monitor, system prompt 等）
- 录音设备：iPhone 语音备忘录，m4a 格式（43MB + 32MB）

## 测试模型

| 模型 | 来源 | 调用方式 | 费用 |
|------|------|---------|------|
| 听悟 (Tingwu) | 阿里云 | REST API (OSS URL → 离线转写) | 按时长 |
| Paraformer-v2 | 阿里 DashScope | REST API (异步, OSS URL) | 按时长 |
| SenseVoice-v1 | 阿里 DashScope | REST API (异步, OSS URL) | 按时长 |
| Qwen3-ASR-Flash | 阿里 DashScope | qwen3-asr-toolkit (VAD分段 → API) | ~0.79元/小时 |
| Whisper large-v3-turbo | OpenAI (开源) | 本地 mlx-whisper (Apple Silicon) | 免费 |
| Whisper large-v3 | OpenAI (开源) | 本地 mlx-whisper (Apple Silicon) | 免费 |

## 关键指标对比

### 中文识别准确度（关键 case）

| 原文 | 听悟 | Paraformer | SenseVoice | Whisper v3-turbo | Whisper v3 | **Qwen3-ASR** |
|------|------|-----------|------------|-----------------|-----------|---------------|
| "system prompt" | — | — | 心声 | c-c-c-c | 事情 | **system prompt** ✅ |
| "Claude Code" | 克拉克 | code | cloud code | Cloud Code | 靠扣 | **cloud code** ✅ |
| "agent" | 那个啥 | a ent | agent | Agent | Agent | **agent** ✅ |
| "monitor" | — | Monit | monster | 模型起人 | 模型 | **monitor** ✅ |
| "纸上雕花" | 史上雕花 | 史上雕花 | 史上雕花 | 史上掉花 | 史上掉花 | **纸上雕花** ✅ |
| "看论文" | 看路 | 看路 | 看中 | 看路 | 看路 | **看论文** ✅ |
| "安全漏洞" | — | — | 安全漏洞 | — | 安全 | **安全漏洞** ✅ |
| "reasoning" | — | — | — | Raising | Raising | **reasoning** ⚠️ |
| "batch" | — | 班刷 | — | 班创 | 班创 | **batch** ✅ |
| "Anthropic" | — | 安抢 | 安卓被 | Altrobit | 爱说个 | 艾弗贝斯 ❌ |

### 功能对比

| 功能 | 听悟 | Paraformer | SenseVoice | Whisper | **Qwen3-ASR** |
|------|------|-----------|------------|---------|---------------|
| 说话人分离 | ✅ | ❌ | ❌ | ❌ | ❌ |
| 章节摘要 | ✅ | ❌ | ❌ | ❌ | ❌ |
| 情绪标注 | ❌ | ❌ | ✅ | ❌ | ❌ |
| 断句质量 | 好 | 好 | 好 | **无断句** | 好 |
| 幻觉/重复 | 少 | 少 | 少 | 有幻觉+重复 | **极少** |
| 口语书面化 | ✅(可选) | ❌ | ❌ | ❌ | ❌ |

## 结论

1. **文本准确度：Qwen3-ASR >> SenseVoice > 听悟 ≈ Paraformer >> Whisper**
   - Qwen3-ASR 在中英混合场景碾压其他所有模型
   - Whisper 在中文上表现最差（CER ~7-8% vs Qwen3 的 3.76%）
2. **综合功能：听悟最全**（说话人分离 + 章节摘要 + 口语书面化），适合会议场景
3. **推荐方案：Qwen3-ASR 做转录 + 听悟补充说话人分离/摘要**
4. **OpenRouter 不支持音频转录 API**（只支持通过 chat completions 发 base64 音频给多模态模型）

## 原始结果文件

存放在 `docs/ref/asr-benchmark/` 目录下，均为同一段音频（清华大学科学馆录音）的转录结果。
