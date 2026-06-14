import type { GapAnalysis, IntakeForm, PracticeReport, ResumeOptimization } from "../types/api";

export const sampleIntake: IntakeForm = {
  targetRole: "后端 API 工程师（电商后台示例）",
  jdText:
    "【示例 JD】后端 API 工程师（电商后台）\n岗位职责：参与电商后台订单、商品和库存相关服务开发，设计 RESTful API，维护 MySQL 数据模型，接入 Redis 缓存热门商品列表，配合前端完成接口联调，关注接口稳定性、异常处理和日志排查。\n必备技能：Python / Java / Go 任一后端开发经验；熟悉 HTTP、RESTful API、MySQL、Redis；了解鉴权、分页、数据库索引设计、缓存一致性和接口文档。\n加分项：有 FastAPI、Spring Boot、Docker、消息队列或云服务部署经验；能解释一次性能优化或问题排查过程。\n面试重点：项目职责边界、Redis 缓存失效、接口鉴权边界、数据库索引设计/优化、错误处理、日志定位和协作沟通。",
  resumeText:
    "【示例简历】张同学 / 计算机科学与技术\n技能：Python、FastAPI、MySQL、Redis、Docker、React，了解 RESTful API 和基础 Linux 部署。\n项目一：电商后台订单系统。负责商品列表、订单状态、用户登录模块，使用 FastAPI 编写接口，MySQL 存储商品和订单数据，Redis 缓存热门商品列表；参与接口文档维护和前后端联调。\n项目二：课程资料管理系统。负责资料上传记录、标签检索和权限判断，处理过分页查询较慢的问题，新增索引并限制查询字段后降低响应时间。\n经历说明：项目主要来自课程和社团实践，缺少正式生产环境经验；部分指标需要在复盘时确认是否有真实记录。",
  jdFile: null,
  resumeFile: null,
  difficulty: "medium",
  duration: 20,
};

export const sampleEvidence = {
  label: "产品样例，不是用户历史",
  jdExcerpt: "JD 要求：RESTful API、MySQL、Redis、鉴权、分页、异常处理、接口文档、日志排查。",
  resumeExcerpt: "简历写到：FastAPI 接口、MySQL 数据表、Redis 缓存热门商品列表、分页查询优化。",
  weakEvidence: [
    {
      title: "Redis 证据偏弱",
      detail: "只写了“缓存热门商品列表”，缺少 key 设计、过期策略、更新时机和缓存失效后的兜底说明。",
    },
    {
      title: "Docker / 部署证据不足",
      detail: "技能区写了 Docker，但项目经历没有说明镜像构建、环境变量、日志或部署流程。",
    },
  ],
  gaps: [
    "JD 提到鉴权、异常处理和接口文档，简历只覆盖了“用户登录”和“文档维护”，实现细节不够。",
    "性能优化有一个索引案例，但缺少排查路径、前后指标和为什么选择该方案。",
  ],
  followUp:
    "你在热门商品缓存里如何设计 key、过期时间和更新策略？如果商品被下架，缓存和数据库如何保持一致？",
  followUps: [
    "你在热门商品缓存里如何设计 key、过期时间和更新策略？如果商品被下架，缓存和数据库如何保持一致？",
    "课程资料分页变慢时，你是怎么定位到索引问题的？有没有看过 explain 或慢查询日志？",
    "你简历里写了 Docker，具体做过镜像构建、环境变量配置、日志查看，还是只是在本地运行过容器？",
  ],
  reportSummary: "样例报告会展示维度评分理由、弱点定位、下一轮练习计划和可直接照着准备的回答框架。",
  reportPreview: [
    "证据质量：63分（技能词丰富，但缺乏追问细节）。",
    "下一轮重点：缓存一致性、接口鉴权、异常处理、项目职责边界。",
    "练习动作：把 Redis 案例改写成 key、TTL、失效、回源四段说明。",
  ],
};

const sampleGapAnalysis: GapAnalysis = {
  matched_skills: ["Python / FastAPI", "RESTful API", "MySQL", "Redis", "分页查询优化", "前后端联调"],
  missing_skills: ["消息队列经验", "云服务部署证据"],
  weak_evidence_skills: ["缓存一致性", "鉴权实现细节", "异常处理策略", "Docker 部署经验"],
  high_risk_topics: ["Redis 缓存失效", "接口鉴权边界", "数据库索引设计/优化", "项目职责边界"],
  recommended_focus: ["补齐缓存一致性案例", "准备鉴权和异常处理说明", "用 STAR 结构讲索引优化过程"],
  summary:
    "示例材料能支撑后端 API 岗的基础技能，但 Redis、鉴权、异常处理和部署经验证据偏弱，面试中容易被连续追问。",
};

const sampleResumeOptimization: ResumeOptimization = {
  optimization_summary:
    "示例简历需要从“列技术栈”改成“说明负责边界、技术取舍和验证结果”。不要补造经历，只把真实做过的接口、缓存和索引优化讲清楚。",
  rewrite_targets: ["校园二手交易平台后端", "课程资料管理系统", "技能区 Docker / Redis 表述"],
  bullet_improvement_suggestions: [
    {
      original_issue: "Redis 缓存热门商品列表",
      why_it_is_weak: "没有说明缓存对象、失效策略、更新时机和异常兜底，无法证明理解缓存一致性。",
      suggested_direction: "补充真实的 key 设计、TTL、数据更新路径和遇到不一致时的处理方式。",
      example_rewrite:
        "为热门商品列表设计 Redis 缓存，按分类维度设置 key 和过期时间，并在商品状态变化后主动失效相关缓存，降低重复查询压力。",
    },
    {
      original_issue: "处理过分页查询较慢的问题",
      why_it_is_weak: "缺少排查方法、优化动作和可验证结果，面试官难以判断技术深度。",
      suggested_direction: "说明慢查询定位、索引字段选择、返回字段裁剪，以及优化前后的真实或可确认表现。",
      example_rewrite:
        "通过慢查询日志定位课程资料分页检索瓶颈，新增标签和创建时间联合索引，并限制返回字段，降低列表页查询延迟。",
    },
  ],
  skill_positioning_suggestions: [
    "把 FastAPI / MySQL / Redis 放到项目证据旁边，而不是只放在技能清单里。",
    "Docker 如果只是了解，应写成“了解基础部署流程”，避免被当作生产部署经验追问。",
  ],
  risk_warnings: ["不要把课程或社团项目包装成正式生产环境经验。", "没有真实指标时，可以描述排查路径，不要补造百分比。"],
};

export const samplePracticeReport: PracticeReport = {
  session_id: "sample-commercial-trust-report",
  evaluation: {
    overall_score: 72,
    dimension_scores: {
      technical_accuracy: {
        score: 76,
        reason: "能说明 FastAPI、MySQL 和分页优化的基本做法，但对缓存一致性和异常处理的解释还不够完整。",
      },
      depth: {
        score: 68,
        reason: "回答停留在“用了 Redis / 加了索引”，缺少设计取舍、失败场景和验证方法。",
      },
      structure: {
        score: 74,
        reason: "能按项目背景和行动说明，但结果、边界和复盘动作需要更清晰。",
      },
      communication: {
        score: 78,
        reason: "表达清楚，没有明显夸大；遇到不确定内容时能承认需要确认。",
      },
      role_fit: {
        score: 73,
        reason: "项目与后端 API 岗匹配，但鉴权、日志和稳定性相关证据需要补强。",
      },
      evidence_quality: {
        score: 63,
        reason: "简历中的关键技能有名称，但缺少足够细节支撑连续追问。",
      },
    },
    strengths: ["有完整的 API 项目上下文", "能把 MySQL、Redis 和前后端联调放进同一项目说明", "没有明显编造经历"],
    weaknesses: ["Redis 证据过薄", "鉴权和异常处理说明不足", "优化结果缺少验证口径"],
    risk_flags: ["缓存一致性追问", "项目职责边界追问", "Docker 经验追问"],
  },
  coaching: {
    summary:
      "这份样例报告说明：材料已经能进入针对性训练，但付费前用户需要看到弱证据为什么弱、会被怎样追问、下一轮该怎么补。",
    top_improvements: [
      {
        issue: "Redis 缓存只写了名词，没有讲机制",
        why_it_matters: "后端 API 岗常用追问会从“用了 Redis”进入一致性、过期、击穿和更新策略。",
        suggestion: "准备一个 90 秒缓存案例，讲清楚缓存对象、key、TTL、主动失效和数据库回源。",
        example_answer_guidance:
          "我缓存的是热门商品列表，key 按分类和排序维度拆分；商品上下架后会删除相关 key，读取失败时回源 MySQL 并重建缓存。",
      },
      {
        issue: "鉴权、异常处理和接口文档没有形成证据链",
        why_it_matters: "JD 明确要求这些能力，简历只提到用户登录和文档维护，不足以证明能独立负责接口质量。",
        suggestion: "把一个接口从请求校验、权限判断、错误码、日志和文档维护讲完整。",
        example_answer_guidance:
          "以商品发布接口为例，先校验登录态和参数，再按业务异常返回统一错误码，同时记录关键日志方便定位。",
      },
      {
        issue: "性能优化缺少结果口径",
        why_it_matters: "没有真实指标时，面试官会追问你如何确认优化有效。",
        suggestion: "不要补造数据，改为说明排查工具、对比方法和可验证现象。",
        example_answer_guidance:
          "我用慢查询和 explain 看到了全表扫描，新增索引后查询计划命中索引；当时没有完整压测，所以我会如实说明验证边界。",
      },
    ],
    practice_plan: [
      "用 5 分钟写下 Redis 缓存案例的 key、TTL、更新和异常兜底。",
      "选一个登录或资料上传接口，按“校验、鉴权、错误码、日志、文档”讲一遍。",
      "把索引优化案例改成“问题、定位、方案、验证边界”的四段回答。",
      "再用同一份 JD 重开一轮模拟面试，重点练缓存和接口质量追问。",
    ],
    next_round_focus: ["缓存一致性", "接口质量", "证据表达", "职责边界"],
  },
  gap_analysis: sampleGapAnalysis,
  resume_optimization: sampleResumeOptimization,
  disclaimer: "这是 InterviewPilot AI 的产品样例报告，用于展示输出形态；评分只代表训练反馈，不代表外部结果判断。",
};
