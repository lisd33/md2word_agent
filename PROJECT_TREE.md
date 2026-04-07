# Project Tree

This file explains the current repository structure and the role of each major file.

```text
md2word_agent/
├── PROJECT_PLAN.md                                       # 项目计划书，定义阶段目标、研究边界与推进顺序
├── RESEARCH_PROBLEM.md                                   # 科研问题定义，说明研究主线与方法问题
├── PROJECT_TREE.md                                       # 当前项目树说明文档，解释每个主要文件的职责
├── complete.md                                           # 开发完成记录，按阶段记录已实现内容与验证情况
├── pyproject.toml                                        # Python 包配置与项目元信息
├── .env                                                  # 本地 API 配置，保存 provider、模型名、key 等运行参数
├── .gitignore                                            # Git 忽略规则，避免提交缓存、密钥和中间输出
├── api/
│   └── README.md                                         # HTTP 接口使用文档，包含 curl 示例与启动方式
├── data/
│   └── rules/
│       └── sample_author_guidelines.md                   # 规则文本样例，用于 Stage 2 规则解析测试
├── schemas/
│   ├── content_intent.schema.json                        # ContentIntent 的 JSON Schema
│   ├── document_ir.schema.json                           # DocumentIR 的 JSON Schema
│   └── template_requirement.schema.json                  # TemplateRequirement 的 JSON Schema
├── scripts/
│   ├── parse_rule_text.py                                # 命令行入口：规则文本 -> TemplateRequirement
│   ├── parse_docx_template.py                            # 命令行入口：docx -> 候选结构 -> LLM -> TemplateRequirement
│   └── run_api_server.py                                 # 启动本地 HTTP 接口服务
├── intermediate_outputs/
│   ├── README.md                                         # 中间输出总目录说明
│   └── template_understanding/
│       └── README.md                                     # Stage 3 模型输出说明，真实运行后会生成 JSON 文件
├── src/
│   └── md2word_agent/
│       ├── __init__.py                                   # 顶层包导出入口
│       ├── api/
│       │   ├── __init__.py                               # API 子包导出
│       │   ├── service.py                                # API 服务层，封装规则解析与模板解析的统一调用接口
│       │   └── server.py                                 # 基于标准库 http.server 的本地 HTTP 服务器实现
│       ├── input/
│       │   ├── __init__.py                               # 输入模块导出
│       │   └── router.py                                 # 输入路由器，识别 template_file / rule_text / content_draft / mixed_input
│       ├── ir/
│       │   └── __init__.py                               # Document IR 子包占位入口，后续用于可编辑文档表示
│       ├── llm/
│       │   ├── __init__.py                               # LLM 子包导出
│       │   ├── config.py                                 # 多 provider 配置加载，解析 .env 中的 Moonshot / MiniMax / Zhipu 设置
│       │   ├── factory.py                                # 按 provider 创建对应 JSON 客户端的工厂
│       │   ├── kimi_client.py                            # Moonshot/Kimi API 客户端
│       │   ├── minimax_client.py                         # MiniMax API 客户端
│       │   └── zhipu_client.py                           # 智谱 API 客户端
│       ├── parser/
│       │   ├── __init__.py                               # 解析模块导出
│       │   ├── docx_reader.py                            # 低层 docx 读取器，抽取 paragraph、style 等基础结构
│       │   ├── models.py                                 # 解析阶段数据模型，如 ParagraphRecord、TemplateCandidate
│       │   ├── rule_parser.py                            # Stage 2 规则文本解析器，抽 citation style、章节和基础格式约束
│       │   └── template_file_parser.py                   # Stage 3 模板文件解析器，负责候选结构抽取并调用 planner
│       ├── planner/
│       │   ├── __init__.py                               # planner 子包导出
│       │   └── template_understanding.py                 # Stage 3 核心：模板结构意图理解、LLM 调用后结果规范化、模型输出落盘
│       └── specs/
│           ├── __init__.py                               # 规范对象导出
│           └── models.py                                 # 核心规范对象：TemplateRequirement、ContentIntent、DocumentIR 等
├── tests/
│   ├── __init__.py                                       # 测试包入口
│   ├── test_llm_config.py                                # provider 配置加载与别名解析测试
│   ├── test_llm_factory.py                               # provider 工厂测试，确保能创建正确客户端
│   ├── api/
│   │   ├── __init__.py                                   # API 测试包入口
│   │   └── test_service.py                               # API 服务层测试，验证规则解析与模板解析接口行为
│   ├── input/
│   │   ├── __init__.py                                   # 输入测试包入口
│   │   └── test_router.py                                # 输入路由器测试
│   ├── parser/
│   │   ├── __init__.py                                   # 解析测试包入口
│   │   ├── test_docx_reader.py                           # docx 读取与模板候选提取测试
│   │   └── test_rule_parser.py                           # 规则解析测试
│   ├── planner/
│   │   ├── __init__.py                                   # planner 测试包入口
│   │   └── test_template_understanding.py                # TemplateUnderstandingPlanner 测试，同时验证模型输出会写入中间目录
│   └── specs/
│       ├── __init__.py                                   # specs 测试包入口
│       └── test_models.py                                # 核心 schema/dataclass 序列化测试
└── tip.docx                                              # 当前用于真实 Stage 3 调试的模板示例文件
```

## Main Runtime Flow

1. `scripts/parse_docx_template.py` 或 `POST /api/v1/parse/template`
2. `parser/docx_reader.py` 读取 `.docx`
3. `parser/template_file_parser.py` 抽取候选标题与上下文
4. `planner/template_understanding.py` 调用大模型理解候选结构
5. `specs/models.py` 中的 `TemplateRequirement` 承接最终规范化输出
6. `intermediate_outputs/template_understanding/` 保存模型最终输出与规范化结果

## Current Stage Mapping

- Stage 1: `input/` + `specs/` + `schemas/`
- Stage 2: `parser/rule_parser.py`
- Stage 3: `parser/docx_reader.py` + `parser/template_file_parser.py` + `planner/template_understanding.py` + `llm/`
- Tooling/API: `api/` + `scripts/run_api_server.py`
