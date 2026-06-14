import { useEffect, useRef, useState } from "react";
import {
  Brain,
  CheckCircle,
  ClipboardList,
  FileText,
  GraduationCap,
  Play,
  School,
  ShieldCheck,
  Sparkles,
  UploadCloud,
  UserRound,
} from "lucide-react";
import { extractJDTextFromFile, extractResumeTextFromFile, userErrorMessage } from "../lib/api";
import { difficultyLabel } from "../lib/labels";
import { sampleIntake } from "../lib/sampleEvidence";
import type { Difficulty, IntakeForm } from "../types/api";

interface StartPageProps {
  busy: boolean;
  onSubmit: (form: IntakeForm) => void;
}

const jdPlaceholder =
  "粘贴目标岗位 JD：岗位名称、职责、必备技能、加分项、项目经验要求、技术栈、团队场景等。";

const resumePlaceholder =
  "粘贴你的真实简历内容：技能、项目、职责、技术选择、结果、遇到的问题和你实际负责的部分。";

export function StartPage({ busy, onSubmit }: StartPageProps) {
  const [targetRole, setTargetRole] = useState("");
  const [jdText, setJdText] = useState("");
  const [resumeText, setResumeText] = useState("");
  const [jdFile, setJdFile] = useState<File | null>(null);
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [difficulty, setDifficulty] = useState<Difficulty>("medium");
  const [duration, setDuration] = useState(20);
  const [demoLoaded, setDemoLoaded] = useState(false);
  const [scenarioApplied, setScenarioApplied] = useState(false);
  const [importedResumeNotice, setImportedResumeNotice] = useState("");
  const [importedJDNotice, setImportedJDNotice] = useState("");
  const [jdImportBusy, setJdImportBusy] = useState(false);
  const [resumeImportBusy, setResumeImportBusy] = useState(false);
  const targetRoleRef = useRef<HTMLInputElement>(null);
  const resumeUploadSectionRef = useRef<HTMLElement>(null);

  useEffect(() => {
    let importedResume = false;
    if (window.sessionStorage.getItem("interviewpilot_demo_requested") === "1") {
      window.sessionStorage.removeItem("interviewpilot_demo_requested");
      loadDemoData();
    }
    const prefillRole = window.sessionStorage.getItem("interviewpilot_prefill_role");
    const prefillDuration = Number(window.sessionStorage.getItem("interviewpilot_prefill_duration"));
    if (prefillRole) {
      window.sessionStorage.removeItem("interviewpilot_prefill_role");
      setTargetRole(prefillRole);
    }
    if (prefillDuration) {
      window.sessionStorage.removeItem("interviewpilot_prefill_duration");
      setDuration(Math.max(10, Math.min(45, prefillDuration)));
    }
    const prefillResumeText = window.sessionStorage.getItem("interviewpilot_prefill_resume_text");
    const prefillResumeNotice = window.sessionStorage.getItem("interviewpilot_prefill_resume_notice");
    if (prefillResumeText || prefillResumeNotice) {
      window.sessionStorage.removeItem("interviewpilot_prefill_resume_text");
      window.sessionStorage.removeItem("interviewpilot_prefill_resume_notice");
      if (prefillResumeText) {
        setResumeText(prefillResumeText);
      }
      setResumeFile(null);
      setImportedResumeNotice(
        prefillResumeText
          ? prefillResumeNotice || "已从首页上传文件识别文字并填入，你可以继续编辑。"
          : prefillResumeNotice || "没有识别到可用简历文字，请在这里粘贴文本或上传 PDF。",
      );
      importedResume = true;
      window.setTimeout(() => setImportedResumeNotice(""), 7000);
    }
    if (window.sessionStorage.getItem("interviewpilot_focus_resume_upload") === "1") {
      window.sessionStorage.removeItem("interviewpilot_focus_resume_upload");
      setImportedResumeNotice("请在这里上传简历 PDF/DOCX，识别后会自动填入文本框；也可以直接粘贴简历文本。");
      window.setTimeout(() => {
        resumeUploadSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
      }, 80);
      window.setTimeout(() => setImportedResumeNotice(""), 7000);
    }
  }, []);

  function loadDemoData() {
    setTargetRole(sampleIntake.targetRole);
    setJdText(sampleIntake.jdText);
    setResumeText(sampleIntake.resumeText);
    setJdFile(null);
    setResumeFile(null);
    setDifficulty(sampleIntake.difficulty);
    setDuration(sampleIntake.duration);
    setDemoLoaded(true);
  }

  function applyScenario(role: string, nextDifficulty: Difficulty, nextDuration: number) {
    setTargetRole(role);
    setDifficulty(nextDifficulty);
    setDuration(nextDuration);
    setScenarioApplied(true);
    window.setTimeout(() => setScenarioApplied(false), 1200);
    window.setTimeout(() => {
      targetRoleRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
      targetRoleRef.current?.focus({ preventScroll: true });
    }, 80);
  }

  async function handleResumeFileChange(file: File | null) {
    setResumeFile(file);
    if (!file) {
      return;
    }
    setResumeImportBusy(true);
    setImportedResumeNotice(`正在识别 ${file.name}，识别后会自动填入下方简历文本框。`);
    try {
      const result = await extractResumeTextFromFile(file);
      const warnings = result.warnings.filter(Boolean);
      if (result.rawText.trim()) {
        setResumeText(result.rawText.trim());
        setDemoLoaded(false);
        setImportedResumeNotice(
          warnings[0] ||
            (result.needsManualCorrection
              ? `已从 ${file.name} 识别文字并填入文本框，建议快速校对后继续。`
              : `已从 ${file.name} 识别文字并填入文本框。`),
        );
      } else {
        setImportedResumeNotice(warnings[0] || "没有识别到可用简历文字，请粘贴文本或换一个可复制文字的 PDF/DOCX。");
      }
    } catch (error) {
      setImportedResumeNotice(userErrorMessage(error));
    } finally {
      setResumeImportBusy(false);
    }
  }

  async function handleJDFileChange(file: File | null) {
    setJdFile(file);
    if (!file) {
      return;
    }
    setJdImportBusy(true);
    setImportedJDNotice(`正在识别 ${file.name}，识别后会自动填入 JD 文本框。`);
    try {
      const result = await extractJDTextFromFile(file);
      const warnings = result.warnings.filter(Boolean);
      if (result.rawText.trim()) {
        setJdText(result.rawText.trim());
        setDemoLoaded(false);
        setImportedJDNotice(
          warnings[0] ||
            (result.needsManualCorrection
              ? `已从 ${file.name} 识别 JD 文本并填入，建议快速校对后继续。`
              : `已从 ${file.name} 识别 JD 文本并填入。`),
        );
      } else {
        setImportedJDNotice(warnings[0] || "没有识别到可用 JD 文本，请粘贴文本或换一个可复制文字的 PDF/清晰图片。");
      }
    } catch (error) {
      setImportedJDNotice(userErrorMessage(error));
    } finally {
      setJdImportBusy(false);
    }
  }

  return (
    <form
      className="zip-page-stack"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit({ targetRole, jdText, resumeText, jdFile, resumeFile, difficulty, duration });
      }}
    >
      <section className="zip-start-hero intake-hero">
        <div>
          <p>
            <Sparkles size={16} />
            求职训练启动台
          </p>
          <h1>先生成你的免费预览报告，再决定是否继续完整训练。</h1>
          <small>免费预览会先给出岗位差距、弱证据提醒、追问样例和报告摘要。你可以先用脱敏简历试一轮。</small>
        </div>
        <aside>
          <ShieldCheck size={22} />
          <strong>只训练真实经历</strong>
          <span>系统会帮你重组表达和准备追问，但不会补造项目、指标、技能或结果。</span>
        </aside>
      </section>

      <section className="demo-entry-panel" aria-label="先看样例材料">
        <div>
          <span>
            <ClipboardList size={15} />
            先看样例材料
          </span>
          <strong>不想先上传真实简历时，可以用明确标注的示例 JD 和示例简历体验流程。</strong>
          <p>示例材料只用于展示产品如何分析，不代表真实用户数据；点击后会填入文本框，你仍可编辑后再生成训练地图。</p>
        </div>
        <button className="zip-outline" onClick={loadDemoData} type="button">
          {demoLoaded ? "示例材料已填入" : "使用示例材料体验"}
          <Sparkles size={16} />
        </button>
      </section>

      <section className="review-lens compact" aria-label="适用场景">
        <div className="zip-section-heading compact">
          <div>
            <span>适用场景</span>
            <h3>同一套训练流，可以服务三种真实求职准备场景。</h3>
            <p>启动页保留真实输入，不默认塞入假材料；不同场景只是组织训练方式不同。</p>
          </div>
        </div>
        <div className="review-lens__grid three scenario-fill-grid">
          <button className="review-lens__card scenario-fill-card" onClick={() => applyScenario("AI Agent 工程师", "medium", 20)} type="button">
            <header>
              <UserRound size={16} />
              <span>匿名体验前线</span>
            </header>
            <strong>求职准备前自测</strong>
            <p>点击后自动锁定 AI Agent 工程师，适合先用脱敏简历体验一次。</p>
          </button>
          <button className="review-lens__card scenario-fill-card" onClick={() => applyScenario("产品经理", "easy", 15)} type="button">
            <header>
              <School size={16} />
              <span>流动辅导工具</span>
            </header>
            <strong>就业辅导工具</strong>
            <p>点击后自动锁定产品经理，适合简历门诊和课后训练营。</p>
          </button>
          <button className="review-lens__card scenario-fill-card" onClick={() => applyScenario("高并发后端架构", "hard", 25)} type="button">
            <header>
              <GraduationCap size={16} />
              <span>高效冲刺</span>
            </header>
            <strong>面试前冲刺</strong>
            <p>点击后自动锁定高并发后端架构，直接进入更强追问模式。</p>
          </button>
        </div>
      </section>

      <section className="zip-launch-grid intake-grid">
        <article className="zip-launch-card wide">
          <header>
            <span>Step 0</span>
            <h2>目标岗位锁定</h2>
          </header>
          <label className="zip-field">
            <span>目标岗位</span>
            <input
              className={scenarioApplied ? "is-scenario-filled" : ""}
              placeholder="例如：后端 API 工程师 / 全栈工程师 / AI 应用工程师"
              ref={targetRoleRef}
              value={targetRole}
              onChange={(event) => setTargetRole(event.target.value)}
              required
            />
          </label>
          <div className="zip-spec-grid">
            <div>
              <Brain size={18} />
              <strong>JD 分析</strong>
              <small>角色标题 / 技能要求 / 责任 / 面试重点</small>
            </div>
            <div>
              <FileText size={18} />
              <strong>简历分析</strong>
              <small>技能 / 项目 / 强项 / 弱证据</small>
            </div>
            <div>
              <Play size={18} />
              <strong>面试计划</strong>
              <small>段落 / 时长 / 追问重点</small>
            </div>
          </div>
        </article>

        <article className="zip-launch-card" ref={resumeUploadSectionRef}>
          <header>
            <span>Step 1</span>
            <h2>JD 输入</h2>
          </header>
          {importedJDNotice ? (
            <div className="imported-resume-note">
              <CheckCircle size={14} />
              {importedJDNotice}
            </div>
          ) : null}
          <textarea placeholder={jdPlaceholder} value={jdText} onChange={(event) => setJdText(event.target.value)} rows={13} />
          <FilePicker
            accept=".pdf,image/png,image/jpeg,image/jpg,image/webp"
            label={jdImportBusy ? "正在识别 JD..." : "上传 JD PDF/图片"}
            file={jdFile}
            onChange={handleJDFileChange}
          />
        </article>

        <article className="zip-launch-card">
          <header>
            <span>Step 2</span>
            <h2>简历输入</h2>
          </header>
          {importedResumeNotice ? (
            <div className="imported-resume-note">
              <CheckCircle size={14} />
              {importedResumeNotice}
            </div>
          ) : null}
          <textarea placeholder={resumePlaceholder} value={resumeText} onChange={(event) => setResumeText(event.target.value)} rows={13} />
          <FilePicker
            accept=".pdf,.docx,image/png,image/jpeg,image/jpg,image/webp,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            label={resumeImportBusy ? "正在识别简历..." : "上传简历 PDF/DOCX/图片"}
            file={resumeFile}
            onChange={handleResumeFileChange}
          />
        </article>

        <article className="zip-launch-card wide footer">
          <header>
            <span>Step 3</span>
            <h2>训练参数</h2>
          </header>
          <div className="zip-param-grid">
            <fieldset>
              <legend>训练强度</legend>
              <div className="zip-segmented">
                {(["easy", "medium", "hard"] as Difficulty[]).map((value) => (
                  <button
                    className={difficulty === value ? "selected" : ""}
                    key={value}
                    onClick={() => setDifficulty(value)}
                    type="button"
                  >
                    {difficultyLabel[value]}
                  </button>
                ))}
              </div>
            </fieldset>
            <label className="zip-field">
              <span>训练时长：{duration} 分钟</span>
              <input
                max={45}
                min={10}
                onChange={(event) => setDuration(Number(event.target.value))}
                step={5}
                type="range"
                value={duration}
              />
            </label>
            <button className="zip-primary launch" disabled={busy} type="submit">
              {busy ? "正在生成免费预览..." : "生成我的免费预览报告"}
            </button>
          </div>
          <div className="zip-launch-checks">
            {["解析 JD", "解析简历", "生成差距分析", "识别弱证据", "生成追问样例", "生成报告摘要"].map((item) => (
              <span key={item}>
                <CheckCircle size={13} />
                {item}
              </span>
            ))}
          </div>
          <p className="intake-boundary">
            免费预览会创建当前训练上下文，方便你继续完整模拟面试。PDF/DOCX 会尝试提取文本；扫描版 PDF 会尽量 OCR，识别结果建议人工校对。
          </p>
        </article>
      </section>
    </form>
  );
}

function FilePicker({
  accept,
  label,
  file,
  onChange,
}: {
  accept: string;
  label: string;
  file: File | null;
  onChange: (file: File | null) => void;
}) {
  return (
    <div className="zip-file-picker">
      <label>
        <UploadCloud size={15} />
        {label}
        <input
          accept={accept}
          onChange={(event) => onChange(event.target.files?.[0] || null)}
          type="file"
        />
      </label>
      <span>{file ? file.name : "未选择文件"}</span>
    </div>
  );
}
