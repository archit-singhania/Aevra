"use client";

import {
  ArrowRight,
  Bell,
  BrainCircuit,
  CalendarDays,
  Check,
  ChevronDown,
  CircleHelp,
  Clock3,
  Command,
  FileStack,
  FileText,
  Gauge,
  Instagram,
  Linkedin,
  Menu,
  MessageCircle,
  PanelLeftClose,
  Plus,
  Search,
  Settings2,
  ShieldCheck,
  Sparkles,
  WandSparkles,
  X,
  Youtube,
  Zap,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const navigation = [
  { label: "Overview", icon: Gauge, active: true },
  { label: "Campaigns", icon: Sparkles },
  { label: "Brand brain", icon: BrainCircuit },
  { label: "Content library", icon: FileStack },
  { label: "Calendar", icon: CalendarDays },
];

const platforms = [
  { label: "LinkedIn", icon: Linkedin, tone: "linkedin-bg" },
  { label: "Instagram", icon: Instagram, tone: "instagram-bg" },
  { label: "YouTube", icon: Youtube, tone: "youtube-bg" },
  { label: "Threads", icon: MessageCircle, tone: "threads-bg" },
];

const steps = [
  { label: "Context retrieval", state: "done" },
  { label: "Campaign planning", state: "done" },
  { label: "Content generation", state: "done" },
  { label: "Platform adaptation", state: "done" },
  { label: "Quality validation", state: "active" },
  { label: "Approval boundary", state: "queued" },
];

const reviewVariants = [
  {
    platform: "LinkedIn",
    tone: "linkedin-bg",
    score: 96,
    copy: "Developer tools should not ask teams to choose between speed and evidence. VAE Studio keeps campaign decisions grounded in the knowledge your organization has already verified.",
    hashtags: ["#VAE", "#AgenticAI", "#DeveloperTools"],
  },
  {
    platform: "Instagram",
    tone: "instagram-bg",
    score: 93,
    copy: "Your brand knowledge, transformed into platform-native stories — with evidence attached and approval built in.",
    hashtags: ["#VAE", "#BrandIntelligence", "#ContentOps"],
  },
  {
    platform: "YouTube",
    tone: "youtube-bg",
    score: 94,
    copy: "See how VAE Studio turns a verified product brief into a grounded, review-ready campaign for every channel.",
    hashtags: ["#VAE", "#RAG", "#MarketingAI"],
  },
];

export function AevraWorkspace() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [commandOpen, setCommandOpen] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [approved, setApproved] = useState(false);
  const [reviewOpen, setReviewOpen] = useState(false);
  const [activeVariant, setActiveVariant] = useState(0);
  const commandInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setCommandOpen((value) => !value);
      }
      if (event.key === "Escape") setCommandOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    if (commandOpen) commandInputRef.current?.focus();
  }, [commandOpen]);

  const startGeneration = () => {
    setGenerating(true);
    setApproved(false);
    window.setTimeout(() => setGenerating(false), 1800);
  };

  return (
    <main className="app-shell">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />

      <aside className={cn("sidebar", sidebarOpen && "sidebar-open")}>
        <div className="brand-row">
          <div className="brand-mark" aria-hidden="true">
            <span />
          </div>
          <span className="brand-name">VAE</span>
          <button
            type="button"
            className="icon-button sidebar-dismiss"
            onClick={() => setSidebarOpen(false)}
            aria-label="Close navigation"
          >
            <PanelLeftClose size={18} />
          </button>
        </div>
        <div className="workspace-switcher">
          <div className="workspace-avatar">A</div>
          <div>
            <strong>Acme Labs</strong>
            <span>Core workspace</span>
          </div>
          <ChevronDown size={15} />
        </div>
        <nav aria-label="Main navigation">
          <p className="nav-kicker">Workspace</p>
          {navigation.map((item) => (
            <button
              type="button"
              className={cn("nav-item", item.active && "active")}
              key={item.label}
            >
              <item.icon size={18} strokeWidth={1.8} />
              <span>{item.label}</span>
              {item.label === "Campaigns" && <small>8</small>}
            </button>
          ))}
          <p className="nav-kicker spaced">System</p>
          <button type="button" className="nav-item">
            <Zap size={18} />
            <span>Automations</span>
          </button>
          <button type="button" className="nav-item">
            <ShieldCheck size={18} />
            <span>Approvals</span>
            <small>3</small>
          </button>
          <button type="button" className="nav-item">
            <Settings2 size={18} />
            <span>Settings</span>
          </button>
        </nav>
        <div className="sidebar-card">
          <div className="sidebar-card-icon">
            <BrainCircuit size={18} />
          </div>
          <div>
            <strong>Brand brain</strong>
            <span>84 sources indexed</span>
          </div>
          <div className="mini-ring">92</div>
        </div>
        <div className="profile-row">
          <div className="profile-avatar">DK</div>
          <div>
            <strong>Dhruv Kumar</strong>
            <span>Workspace admin</span>
          </div>
          <button type="button" className="icon-button" aria-label="Open settings">
            <Settings2 size={16} />
          </button>
        </div>
      </aside>

      {sidebarOpen && (
        <button
          type="button"
          className="backdrop"
          onClick={() => setSidebarOpen(false)}
          aria-label="Close navigation"
        />
      )}

      <section className="main-panel">
        <header className="topbar">
          <button
            type="button"
            className="icon-button mobile-menu"
            onClick={() => setSidebarOpen(true)}
            aria-label="Open navigation"
          >
            <Menu size={20} />
          </button>
          <button
            type="button"
            className="command-search"
            onClick={() => setCommandOpen(true)}
            aria-label="Search anything"
          >
            <Search size={16} />
            <span>Search anything</span>
            <kbd>
              <Command size={12} /> K
            </kbd>
          </button>
          <div className="topbar-actions">
            <button type="button" className="icon-button" aria-label="Help">
              <CircleHelp size={18} />
            </button>
            <button type="button" className="icon-button notification" aria-label="Notifications">
              <Bell size={18} />
              <i />
            </button>
            <Button size="sm" onClick={startGeneration}>
              <Plus size={16} /> New campaign
            </Button>
          </div>
        </header>

        <div className="content">
          <div className="page-heading">
            <div>
              <p className="eyebrow">
                <span /> Week of 15 September
              </p>
              <h1>Your brand, in motion.</h1>
              <p>
                Shape the next campaign. VAE keeps every idea grounded, adapted, and ready for
                approval.
              </p>
            </div>
            <div className="health-pill">
              <span className="pulse-dot" />
              All systems ready
            </div>
          </div>

          <section className="composer-card">
            <div className="composer-glow" />
            <div className="composer-header">
              <WandSparkles size={17} />
              <span>Campaign composer</span>
              <div className="model-pill">
                VAE local <span>·</span> Qwen
              </div>
            </div>
            <textarea
              aria-label="Campaign brief"
              defaultValue="Launch our new developer toolkit next week. Focus on engineering teams, use a confident and precise tone, and create platform-native content for our connected channels."
            />
            <div className="composer-footer">
              <div className="platform-selection">
                {platforms.map((platform) => (
                  <button
                    type="button"
                    aria-label={`${platform.label} selected`}
                    title={platform.label}
                    key={platform.label}
                    className={cn("platform-icon", platform.tone)}
                  >
                    <platform.icon size={15} />
                  </button>
                ))}
                <button type="button" className="platform-more">
                  +2
                </button>
                <span>6 channels</span>
              </div>
              <div className="composer-actions">
                <button type="button" className="mode-button">
                  <ShieldCheck size={15} />
                  Manual approval
                  <ChevronDown size={14} />
                </button>
                <Button onClick={startGeneration} disabled={generating}>
                  {generating ? (
                    <>
                      <span className="spinner" />
                      Orchestrating
                    </>
                  ) : (
                    <>
                      Generate campaign
                      <ArrowRight size={16} />
                    </>
                  )}
                </Button>
              </div>
            </div>
          </section>

          <div className="section-title">
            <div>
              <h2>Active intelligence</h2>
              <span>Live across this workspace</span>
            </div>
            <button type="button">
              View all activity <ArrowRight size={14} />
            </button>
          </div>
          <div className="overview-grid">
            <section className="panel agent-panel">
              <div className="panel-heading">
                <div className="heading-icon lime">
                  <BrainCircuit size={17} />
                </div>
                <div>
                  <h3>Agent run</h3>
                  <p>Developer toolkit launch</p>
                </div>
                <span className="live-label">
                  <i />
                  Live
                </span>
              </div>
              <div className="agent-steps">
                {steps.map((step, index) => (
                  <div className={cn("agent-step", step.state)} key={step.label}>
                    <div className="step-track">
                      <span>{step.state === "done" ? <Check size={12} /> : index + 1}</span>
                      {index < steps.length - 1 && <i />}
                    </div>
                    <div>
                      <strong>{step.label}</strong>
                      <small>
                        {step.state === "done"
                          ? "Completed"
                          : step.state === "active"
                            ? "Building the narrative"
                            : "Waiting"}
                      </small>
                    </div>
                    {step.state === "active" && (
                      <span className="working-bars">
                        <i />
                        <i />
                        <i />
                      </span>
                    )}
                  </div>
                ))}
              </div>
              <div className="trace-footer">
                <span>
                  <Clock3 size={13} />
                  Started 2m ago
                </span>
                <button type="button">
                  Open reasoning trace <ArrowRight size={13} />
                </button>
              </div>
            </section>

            <section className="panel calendar-panel">
              <div className="panel-heading">
                <div className="heading-icon violet">
                  <CalendarDays size={17} />
                </div>
                <div>
                  <h3>This week</h3>
                  <p>9 posts across 6 channels</p>
                </div>
                <button type="button" className="icon-button" aria-label="Change week">
                  <ChevronDown size={16} />
                </button>
              </div>
              <div className="week-row">
                {[
                  ["mon", "M"],
                  ["tue", "T"],
                  ["wed", "W"],
                  ["thu", "T"],
                  ["fri", "F"],
                  ["sat", "S"],
                  ["sun", "S"],
                ].map(([key, day], i) => (
                  <div className={cn(i === 0 && "today")} key={key}>
                    <span>{day}</span>
                    <strong>{15 + i}</strong>
                    {[0, 2, 4].includes(i) && <i />}
                  </div>
                ))}
              </div>
              <div className="upcoming-list">
                <article>
                  <div className="post-time">
                    <strong>09:30</strong>
                    <span>Today</span>
                  </div>
                  <div className="post-line linkedin" />
                  <div className="post-copy">
                    <strong>Why developer tools fail quietly</strong>
                    <span>LinkedIn · Thought leadership</span>
                  </div>
                  <div className="status-chip review">Review</div>
                </article>
                <article>
                  <div className="post-time">
                    <strong>14:00</strong>
                    <span>Wed</span>
                  </div>
                  <div className="post-line instagram" />
                  <div className="post-copy">
                    <strong>Inside the toolkit</strong>
                    <span>Instagram · Carousel</span>
                  </div>
                  <div className="status-chip ready">Ready</div>
                </article>
                <article>
                  <div className="post-time">
                    <strong>17:30</strong>
                    <span>Fri</span>
                  </div>
                  <div className="post-line youtube" />
                  <div className="post-copy">
                    <strong>Build faster, reason better</strong>
                    <span>YouTube · Short</span>
                  </div>
                  <div className="status-chip draft">Draft</div>
                </article>
              </div>
            </section>

            <section className="panel quality-panel">
              <div className="panel-heading">
                <div className="heading-icon cyan">
                  <ShieldCheck size={17} />
                </div>
                <div>
                  <h3>Brand quality</h3>
                  <p>Last 30 generated assets</p>
                </div>
              </div>
              <div className="score-block">
                <div className="score-ring">
                  <strong>94</strong>
                  <span>/100</span>
                </div>
                <div>
                  <strong>Excellent alignment</strong>
                  <p>Up 7 points this month</p>
                </div>
              </div>
              <div className="quality-meters">
                <div>
                  <span>
                    Voice consistency <b>96%</b>
                  </span>
                  <i>
                    <em style={{ width: "96%" }} />
                  </i>
                </div>
                <div>
                  <span>
                    Claim grounding <b>93%</b>
                  </span>
                  <i>
                    <em style={{ width: "93%" }} />
                  </i>
                </div>
                <div>
                  <span>
                    Platform fit <b>91%</b>
                  </span>
                  <i>
                    <em style={{ width: "91%" }} />
                  </i>
                </div>
              </div>
            </section>
          </div>

          <section className="approval-strip">
            <div className="approval-art">
              <Sparkles size={22} />
            </div>
            <div>
              <span className="approval-kicker">Approval queue</span>
              <h3>{approved ? "Campaign approved" : "Developer toolkit launch is ready"}</h3>
              <p>
                {approved
                  ? "The deterministic scheduler can now prepare the approved variants."
                  : "12 platform-native assets passed brand and compliance review."}
              </p>
            </div>
            <div className="approval-actions">
              {approved ? (
                <span className="approved-message">
                  <Check size={17} /> Approved safely
                </span>
              ) : (
                <>
                  <Button variant="secondary" size="sm" onClick={() => setReviewOpen(true)}>
                    Review assets
                  </Button>
                  <Button size="sm" onClick={() => setApproved(true)}>
                    Approve campaign <ArrowRight size={15} />
                  </Button>
                </>
              )}
            </div>
          </section>
        </div>
      </section>

      {commandOpen && (
        <div className="command-overlay">
          <button
            type="button"
            className="command-backdrop"
            onClick={() => setCommandOpen(false)}
            aria-label="Close command menu"
          />
          <section
            className="command-dialog"
            role="dialog"
            aria-modal="true"
            aria-label="Command menu"
          >
            <div className="command-input">
              <Search size={18} />
              <input
                ref={commandInputRef}
                aria-label="Search commands"
                placeholder="Search campaigns, knowledge, or actions…"
              />
              <button
                type="button"
                onClick={() => setCommandOpen(false)}
                aria-label="Close command menu"
              >
                <X size={16} />
              </button>
            </div>
            <p>Quick actions</p>
            <button
              type="button"
              onClick={() => {
                setCommandOpen(false);
                startGeneration();
              }}
            >
              <span>
                <Sparkles size={17} />
                Create a new campaign
              </span>
              <kbd>↵</kbd>
            </button>
            <button type="button">
              <span>
                <BrainCircuit size={17} />
                Open Brand Brain
              </span>
              <kbd>B</kbd>
            </button>
            <button type="button">
              <span>
                <CalendarDays size={17} />
                View content calendar
              </span>
              <kbd>C</kbd>
            </button>
          </section>
        </div>
      )}

      {reviewOpen && (
        <div className="review-overlay">
          <button
            type="button"
            className="command-backdrop"
            onClick={() => setReviewOpen(false)}
            aria-label="Close variant review"
          />
          <section className="review-dialog" role="dialog" aria-modal="true">
            <header className="review-header">
              <div>
                <span className="approval-kicker">Revision 1 · Manual approval</span>
                <h2>Review campaign variants</h2>
                <p>Every factual variant retains the Brand Brain evidence used to create it.</p>
              </div>
              <button
                type="button"
                className="icon-button"
                onClick={() => setReviewOpen(false)}
                aria-label="Close review"
              >
                <X size={18} />
              </button>
            </header>
            <div className="review-layout">
              <nav className="variant-list" aria-label="Generated variants">
                {reviewVariants.map((variant, index) => (
                  <button
                    type="button"
                    key={variant.platform}
                    className={cn(index === activeVariant && "selected")}
                    onClick={() => setActiveVariant(index)}
                  >
                    <span className={cn("variant-platform-icon", variant.tone)}>
                      {variant.platform.slice(0, 1)}
                    </span>
                    <span>
                      <strong>{variant.platform}</strong>
                      <small>Platform-native copy</small>
                    </span>
                    <b>{variant.score}</b>
                  </button>
                ))}
              </nav>
              <article className="variant-preview">
                <div className="variant-preview-meta">
                  <span>{reviewVariants[activeVariant].platform} variant</span>
                  <span className="quality-chip">
                    <ShieldCheck size={13} /> {reviewVariants[activeVariant].score}/100
                  </span>
                </div>
                <p className="variant-copy">{reviewVariants[activeVariant].copy}</p>
                <div className="variant-hashtags">
                  {reviewVariants[activeVariant].hashtags.map((tag) => (
                    <span key={tag}>{tag}</span>
                  ))}
                </div>
                <div className="evidence-card">
                  <div className="heading-icon lime">
                    <FileText size={16} />
                  </div>
                  <div>
                    <strong>2 evidence references attached</strong>
                    <p>Verified product brief · Brand positioning guide</p>
                  </div>
                  <button type="button">Inspect citations</button>
                </div>
                <div className="variant-notes">
                  <span>
                    <Check size={13} /> Voice aligned
                  </span>
                  <span>
                    <Check size={13} /> Claims grounded
                  </span>
                  <span>
                    <Check size={13} /> Platform fit
                  </span>
                </div>
              </article>
            </div>
            <footer className="review-footer">
              <button type="button" className="mode-button">
                Regenerate with feedback
              </button>
              <div>
                <Button variant="secondary" size="sm" onClick={() => setReviewOpen(false)}>
                  Save for later
                </Button>
                <Button
                  size="sm"
                  onClick={() => {
                    setApproved(true);
                    setReviewOpen(false);
                  }}
                >
                  Approve revision <ArrowRight size={15} />
                </Button>
              </div>
            </footer>
          </section>
        </div>
      )}
    </main>
  );
}
