# InterviewPilot AI 提交材料清单

## 参赛信息

- 作品名称：InterviewPilot AI
- 参赛赛道：AI + 求职
- 作品类型：产品 Demo / AI 求职训练工具
- 一句话说明：基于目标 JD 与个人简历证据缺口的追问式模拟面试教练。

## 建议上传材料

1. `output/pdf/InterviewPilotAI_Product_Description.pdf`
   - 对应：产品说明书
   - 内容：产品概述、用户痛点、核心功能、技术实现、创新点、商业模式、当前进展与后续规划。

2. `docs/PRODUCT_DESCRIPTION.md`
   - 对应：产品说明书源文件
   - 作用：如需临时修改文案，可先改 Markdown，再重新导出 PDF。

3. 产品演示视频
   - 建议文件名：`InterviewPilotAI_产品演示视频.mp4`
   - 建议时长：3 分钟以内。
   - 必须展示：JD/简历输入、差距分析、面试计划、动态追问、练习报告。

4. 复赛作品 PPT
   - 建议文件名：`InterviewPilotAI_作品PPT.pdf`
   - 建议结构：痛点、方案、演示、技术架构、创新性、商业价值、可落地性、后续规划。

5. 《作品原创说明及授权书》
   - 建议文件名：`InterviewPilotAI_原创说明及授权书.pdf`
   - 需使用赛事官方模板并按要求签署。

6. Demo 地址
   - 静态演示地址：`https://zifeiyuuuuuuu.github.io/InterviewPilot-AI/`
   - 源码地址：`https://github.com/ZIFeIYUuuuuuu/InterviewPilot-AI`

## 静态演示说明

GitHub Pages 会在推送到 `master` 后自动执行 `.github/workflows/pages.yml`：

```text
npm ci
npm run build
deploy frontend/dist
```

静态演示主要用于展示产品界面、流程和样例报告。完整真实模型分析需要启动 FastAPI 后端，并按 `.env.example` 配置模型服务。

## 本地真实后端演示

```powershell
python -m pip install -e .
python -m backend.app.main
```

启动前端：

```powershell
cd frontend
npm ci
npm run dev
```

默认前端代理 `/api` 到 `http://127.0.0.1:8000`。

## 真实模型配置

复制 `.env.example` 为 `.env` 后配置：

```text
INTERVIEWPILOT_LLM_API_KEY=your-api-key
INTERVIEWPILOT_LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
INTERVIEWPILOT_LLM_MODEL=qwen-plus
INTERVIEWPILOT_LLM_ENABLED=true
```

不要提交真实 API Key。

## 提交前检查

- 视频可正常播放。
- PPT 已导出为 PDF，避免字体错乱。
- 产品说明书 PDF 可打开，中文无乱码。
- `.env` 和真实简历不进入提交包。
- 上传成功后保存平台成功页面截图。
