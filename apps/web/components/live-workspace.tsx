/* biome-ignore-all lint/a11y/useButtonType: interactive buttons are outside submit forms. */
/* biome-ignore-all lint/a11y/noLabelWithoutControl: Field wraps its control component. */
"use client";

import {
  ArrowRight,
  BrainCircuit,
  CalendarDays,
  Check,
  CircleAlert,
  FileText,
  Image,
  LogOut,
  Menu,
  Plus,
  RefreshCw,
  Search,
  Send,
  ShieldCheck,
  Sparkles,
  Upload,
  X,
} from "lucide-react";
import { AnimatePresence, MotionConfig, motion } from "motion/react";
import {
  type CSSProperties,
  type FormEvent,
  type MouseEvent,
  type ReactNode,
  useCallback,
  useEffect,
  useState,
} from "react";
import {
  AiOrb,
  CommandPalette,
  DepthCard,
  Onboarding,
  ParticleField,
  Reveal,
  SoundToggle,
  TypewriterText,
  VoiceIndicator,
} from "@/components/advanced-ui";
import { GrainOverlay } from "@/components/background/grain-overlay";
import { WebglBackground } from "@/components/background/webgl-background";
import { Button } from "@/components/ui/button";
import {
  api,
  type Brand,
  type Campaign,
  type ContentVariant,
  type KnowledgeDocument,
  type MediaAsset,
  type Platform,
  type ScheduledPost,
  type SocialAccount,
  type User,
  type Workspace,
} from "@/lib/api";
import { overlayFade, variantSwap } from "@/lib/motion";
import { cn } from "@/lib/utils";

// Cursor-follow glow — writes pointer position as CSS custom properties so
// the glow itself stays CSS-driven (no re-renders on mouse move).
function handleGlow(event: MouseEvent<HTMLElement>) {
  const rect = event.currentTarget.getBoundingClientRect();
  event.currentTarget.style.setProperty(
    "--mx",
    `${((event.clientX - rect.left) / rect.width) * 100}%`,
  );
  event.currentTarget.style.setProperty(
    "--my",
    `${((event.clientY - rect.top) / rect.height) * 100}%`,
  );
}

type View = "overview" | "campaigns" | "brain" | "media" | "publishing";
const tokenKey = "vae.staging.access-token";
const platforms: Array<{ id: Platform; label: string }> = [
  "linkedin",
  "instagram",
  "threads",
  "youtube",
  "x",
  "facebook",
].map((id) => ({ id: id as Platform, label: id[0].toUpperCase() + id.slice(1) }));
const date = (value?: string | null) =>
  value
    ? new Intl.DateTimeFormat(undefined, {
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
      }).format(new Date(value))
    : "—";
const initial = (value?: string | null) => value?.trim().charAt(0).toUpperCase() || "V";
const idempotency = () =>
  `vae-web-${typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : Date.now()}`;
function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="live-field">
      <span>{label}</span>
      {children}
    </label>
  );
}
function Status({ value }: { value: string }) {
  return (
    <span className={cn("live-status", `status-${value.replaceAll("_", "-")}`)}>
      {value.replaceAll("_", " ")}
    </span>
  );
}
function Empty({
  icon: Icon,
  title,
  body,
}: {
  icon: typeof FileText;
  title: string;
  body: string;
}) {
  return (
    <div className="live-empty">
      <Icon size={20} />
      <strong>{title}</strong>
      <p>{body}</p>
    </div>
  );
}

export function LiveWorkspace() {
  const [token, setToken] = useState<string | null>(null);
  const [hydrated, setHydrated] = useState(false);
  const [mode, setMode] = useState<"login" | "register">("login");
  const [view, setView] = useState<View>("overview");
  const [sidebar, setSidebar] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [brands, setBrands] = useState<Brand[]>([]);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [assets, setAssets] = useState<MediaAsset[]>([]);
  const [accounts, setAccounts] = useState<SocialAccount[]>([]);
  const [scheduled, setScheduled] = useState<ScheduledPost[]>([]);
  const [selected, setSelected] = useState("");
  const [variants, setVariants] = useState<ContentVariant[]>([]);
  const [evidence, setEvidence] = useState<
    Array<{ chunk_id: string; document_title: string; score: number; excerpt: string }>
  >([]);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [org, setOrg] = useState("");
  const [workspaceName, setWorkspaceName] = useState("");
  const [brandName, setBrandName] = useState("VAE");
  const [brandDescription, setBrandDescription] = useState(
    "Evidence-led GenAI content operations.",
  );
  const [sourceTitle, setSourceTitle] = useState("");
  const [sourceText, setSourceText] = useState("");
  const [query, setQuery] = useState("");
  const [campaignName, setCampaignName] = useState("");
  const [goal, setGoal] = useState("");
  const [product, setProduct] = useState("");
  const [audience, setAudience] = useState("");
  const [instructions, setInstructions] = useState("");
  const [platform, setPlatform] = useState<Platform>("linkedin");
  const [mediaPrompt, setMediaPrompt] = useState("");
  const [mediaCampaign, setMediaCampaign] = useState("");
  const [accountPlatform, setAccountPlatform] = useState<Platform>("linkedin");
  const [accountName, setAccountName] = useState("");
  const [externalId, setExternalId] = useState("");
  const [publishCampaign, setPublishCampaign] = useState("");
  const [publishAccount, setPublishAccount] = useState("");
  const [publishText, setPublishText] = useState("");
  const [scheduleAt, setScheduleAt] = useState("");
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [tourOpen, setTourOpen] = useState(false);
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [soundEnabled, setSoundEnabled] = useState(false);
  const [pulse, setPulse] = useState(0);
  const [scrolled, setScrolled] = useState(false);
  const [metricOrder, setMetricOrder] = useState(["sources", "campaigns", "approval", "assets"]);
  const [dragMetric, setDragMetric] = useState<string | null>(null);
  const currentCampaign = campaigns.find((item) => item.id === selected);
  const currentVariant = variants.find((item) => item.status === "approved") ?? variants[0];
  const playTone = useCallback(() => {
    if (!soundEnabled || typeof window === "undefined") return;
    const AudioContextClass =
      window.AudioContext ||
      (window as Window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!AudioContextClass) return;
    const context = new AudioContextClass();
    const oscillator = context.createOscillator();
    const gain = context.createGain();
    oscillator.frequency.value = 660;
    gain.gain.setValueAtTime(0.0001, context.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.035, context.currentTime + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.0001, context.currentTime + 0.18);
    oscillator.connect(gain).connect(context.destination);
    oscillator.start();
    oscillator.stop(context.currentTime + 0.2);
  }, [soundEnabled]);
  const reset = useCallback(() => {
    window.localStorage.removeItem(tokenKey);
    setToken(null);
    setUser(null);
    setWorkspace(null);
    setBrands([]);
    setCampaigns([]);
    setDocuments([]);
    setAssets([]);
    setAccounts([]);
    setScheduled([]);
    setVariants([]);
  }, []);
  const run = async (name: string, task: () => Promise<void>) => {
    setBusy(name);
    setError(null);
    try {
      await task();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The operation failed.");
    } finally {
      setBusy(null);
    }
  };
  const load = useCallback(
    async (accessToken: string) => {
      setBusy("load");
      try {
        const [me, workspaces] = await Promise.all([
          api.me(accessToken),
          api.workspaces(accessToken),
        ]);
        const nextWorkspace = workspaces[0];
        if (!nextWorkspace) throw new Error("No active workspace found.");
        const [nextBrands, nextCampaigns, nextDocuments, nextAssets, nextAccounts, nextScheduled] =
          await Promise.all([
            api.brands(accessToken, nextWorkspace.id),
            api.campaigns(accessToken, nextWorkspace.id),
            api.documents(accessToken, nextWorkspace.id),
            api.media(accessToken, nextWorkspace.id),
            api.accounts(accessToken, nextWorkspace.id),
            api.scheduled(accessToken, nextWorkspace.id),
          ]);
        setUser(me);
        setWorkspace(nextWorkspace);
        setBrands(nextBrands);
        setCampaigns(nextCampaigns);
        setDocuments(nextDocuments);
        setAssets(nextAssets);
        setAccounts(nextAccounts);
        setScheduled(nextScheduled);
        setSelected((value) => value || nextCampaigns[0]?.id || "");
        setMediaCampaign((value) => value || nextCampaigns[0]?.id || "");
        setPublishCampaign((value) => value || nextCampaigns[0]?.id || "");
        setPublishAccount((value) => value || nextAccounts[0]?.id || "");
      } catch (caught) {
        if (caught instanceof Error && caught.message.includes("401")) reset();
        setError(caught instanceof Error ? caught.message : "Unable to load workspace.");
      } finally {
        setBusy(null);
      }
    },
    [reset],
  );
  useEffect(() => {
    const saved = window.localStorage.getItem(tokenKey);
    if (saved) setToken(saved);
    setHydrated(true);
  }, []);
  useEffect(() => {
    if (token) void load(token);
  }, [token, load]);
  useEffect(() => {
    if (token && workspace && selected)
      void api
        .variants(token, workspace.id, selected)
        .then(setVariants)
        .catch(() => setVariants([]));
  }, [token, workspace, selected]);
  useEffect(() => {
    const savedTheme = window.localStorage.getItem("vae.theme");
    const savedOrder = window.localStorage.getItem("vae.metric-order");
    if (savedTheme === "light") setTheme("light");
    if (savedOrder) {
      try {
        const parsed = JSON.parse(savedOrder) as string[];
        if (parsed.length === 4) setMetricOrder(parsed);
      } catch {
        // Ignore stale local preferences.
      }
    }
    setTourOpen(window.localStorage.getItem("vae.tour-complete") !== "1");
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setPaletteOpen(true);
      }
      if (event.key === "Escape") {
        setPaletteOpen(false);
        setTourOpen(false);
      }
    };
    const onScroll = () => setScrolled(window.scrollY > 24);
    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("scroll", onScroll);
    };
  }, []);
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem("vae.theme", theme);
  }, [theme]);
  useEffect(() => {
    window.localStorage.setItem("vae.metric-order", JSON.stringify(metricOrder));
  }, [metricOrder]);
  const authenticate = async (event: FormEvent) => {
    event.preventDefault();
    setBusy("auth");
    setError(null);
    try {
      const result =
        mode === "login"
          ? await api.login(email, password)
          : await api.register({
              email,
              password,
              display_name: name,
              organization_name: org,
              workspace_name: workspaceName,
              timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC",
            });
      const accessToken = "token" in result ? result.token.access_token : result.access_token;
      window.localStorage.setItem(tokenKey, accessToken);
      setToken(accessToken);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Authentication failed.");
    } finally {
      setBusy(null);
    }
  };
  const createCampaign = async (event: FormEvent) => {
    event.preventDefault();
    if (!token || !workspace || !brands[0]) {
      setView("brain");
      setError("Create a Brand Brain profile first.");
      return;
    }
    await run("campaign", async () => {
      const campaign = await api.createCampaign(token, workspace.id, {
        brand_id: brands[0].id,
        name: campaignName,
        goal,
        product_service: product,
        audience,
        instructions,
        platforms: [platform],
        media_types: ["text", "image"],
        publishing_mode: "manual",
      });
      const generated = await api.generateCampaign(token, workspace.id, campaign.id);
      setCampaigns((items) => [generated.campaign, ...items]);
      setSelected(campaign.id);
      setMediaCampaign(campaign.id);
      setPublishCampaign(campaign.id);
      setVariants(generated.variants);
      setNotice("Review-ready variants generated.");
      setPulse((value) => value + 1);
      playTone();
    });
  };
  const decide = async (decision: "approve" | "reject") => {
    if (!token || !workspace || !currentCampaign) return;
    await run(decision, async () => {
      const generated = await api.decideCampaign(token, workspace.id, currentCampaign.id, decision);
      setCampaigns((items) =>
        items.map((item) => (item.id === currentCampaign.id ? generated.campaign : item)),
      );
      setVariants(generated.variants);
      setNotice(
        decision === "approve" ? "Campaign approved for publishing." : "Changes requested.",
      );
      setPulse((value) => value + 1);
      playTone();
    });
  };
  const createBrand = async (event: FormEvent) => {
    event.preventDefault();
    if (!token || !workspace) return;
    await run("brand", async () => {
      const brand = await api.createBrand(token, workspace.id, {
        name: brandName,
        description: brandDescription,
        website_url: null,
        industry: "Artificial intelligence",
        tone_attributes: ["clear", "confident", "evidence-led"],
        target_audiences: ["marketing teams"],
        preferred_ctas: ["Explore VAE"],
        preferred_hashtags: ["#VAE", "#AgenticAI"],
        status: "active",
      });
      setBrands((items) => [brand, ...items]);
    });
  };
  const ingest = async (event: FormEvent) => {
    event.preventDefault();
    if (!token || !workspace) return;
    await run("ingest", async () => {
      const result = await api.ingest(token, workspace.id, {
        title: sourceTitle,
        source_type: "markdown",
        content: sourceText,
        brand_id: brands[0]?.id ?? null,
      });
      setDocuments((items) => [result.document, ...items]);
      setSourceTitle("");
      setSourceText("");
      setNotice(`${result.chunks_created} evidence chunks indexed.`);
    });
  };
  const searchBrain = async (event: FormEvent) => {
    event.preventDefault();
    if (!token || !workspace) return;
    await run("search", async () => {
      const result = await api.searchKnowledge(token, workspace.id, {
        query,
        brand_id: brands[0]?.id ?? null,
      });
      setEvidence(result.citations);
    });
  };
  const createImage = async (event: FormEvent) => {
    event.preventDefault();
    if (!token || !workspace) return;
    await run("image", async () => {
      const result = await api.generateImage(token, workspace.id, {
        campaign_id: mediaCampaign,
        prompt: mediaPrompt,
        platforms: ["instagram"],
        aspect_ratio: "1:1",
        brand_overlay: true,
        brand_text: brands[0]?.name ?? "VAE",
      });
      setAssets((items) => [...result.assets, ...items]);
      setMediaPrompt("");
      setNotice("Visual asset generated.");
      setPulse((value) => value + 1);
      playTone();
    });
  };
  const downloadAsset = async (asset: MediaAsset) => {
    if (!token || !asset.download_url) return;
    await run(`download-${asset.id}`, async () => {
      const response = await fetch(asset.download_url as string, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error("The asset download could not be completed.");
      const objectUrl = URL.createObjectURL(await response.blob());
      const link = document.createElement("a");
      link.href = objectUrl;
      link.download = asset.filename;
      link.click();
      URL.revokeObjectURL(objectUrl);
    });
  };
  const connect = async (event: FormEvent) => {
    event.preventDefault();
    if (!token || !workspace) return;
    await run("connect", async () => {
      const account = await api.connectAccount(token, workspace.id, {
        platform: accountPlatform,
        external_account_id: externalId,
        display_name: accountName,
        access_token_ref: `staging-ref-${externalId}`,
        capabilities: ["publish", "analytics"],
      });
      setAccounts((items) => [account, ...items]);
      setPublishAccount(account.id);
      setNotice("Staging publishing account connected.");
    });
  };
  const publish = async (shouldSchedule: boolean) => {
    if (
      !token ||
      !workspace ||
      !publishCampaign ||
      !publishAccount ||
      !(publishText || currentVariant?.caption)
    )
      return;
    await run(shouldSchedule ? "schedule" : "publish", async () => {
      const payload = {
        campaign_id: publishCampaign,
        social_account_id: publishAccount,
        idempotency_key: idempotency(),
        text: publishText || currentVariant?.caption || "",
        media_urls: [],
      };
      if (shouldSchedule) {
        const item = await api.schedule(token, workspace.id, {
          ...payload,
          scheduled_for: new Date(scheduleAt || Date.now() + 86_400_000).toISOString(),
        });
        setScheduled((items) => [item, ...items]);
        setNotice(`Post scheduled for ${date(item.scheduled_for)}.`);
      } else {
        const job = await api.publish(token, workspace.id, payload);
        setNotice(`Publishing job is ${job.status}.`);
      }
    });
  };
  if (!hydrated)
    return (
      <main className="live-loading">
        <WebglBackground />
        <GrainOverlay />
        <RefreshCw size={18} /> Opening VAE…
      </main>
    );
  if (!token)
    return (
      <MotionConfig reducedMotion="user">
        <main className="live-auth">
          <WebglBackground />
          <GrainOverlay />
          <motion.section
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          >
            <div className="live-logo">
              <span />
              <b>VAE</b>
            </div>
            <p className="live-kicker">Campaign intelligence, grounded</p>
            <h1>Make every campaign feel like your sharpest team member made it.</h1>
            <p>
              Turn approved brand knowledge into evidence-backed, human-approved content operations.
            </p>
            <div className="live-auth-points">
              <span>
                <Check size={15} /> Brand-grounded generation
              </span>
              <span>
                <Check size={15} /> Reviewable evidence trail
              </span>
              <span>
                <Check size={15} /> Staged publishing control
              </span>
            </div>
          </motion.section>
          <motion.form
            className="live-auth-card"
            onSubmit={authenticate}
            onMouseMove={handleGlow}
            initial={{ opacity: 0, y: 16, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1], delay: 0.1 }}
          >
            <div className="live-tabs">
              <button
                type="button"
                className={cn(mode === "login" && "active")}
                onClick={() => setMode("login")}
              >
                Sign in
              </button>
              <button
                type="button"
                className={cn(mode === "register" && "active")}
                onClick={() => setMode("register")}
              >
                Create workspace
              </button>
            </div>
            <h2>{mode === "login" ? "Welcome back" : "Start your VAE workspace"}</h2>
            {error && (
              <div className="live-alert error">
                <CircleAlert size={15} /> {error}
              </div>
            )}
            {mode === "register" && (
              <>
                <Field label="Your name">
                  <input
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Jane Smith"
                  />
                </Field>
                <Field label="Organization">
                  <input
                    required
                    value={org}
                    onChange={(e) => setOrg(e.target.value)}
                    placeholder="VAE Studio"
                  />
                </Field>
                <Field label="Workspace">
                  <input
                    required
                    value={workspaceName}
                    onChange={(e) => setWorkspaceName(e.target.value)}
                    placeholder="Marketing"
                  />
                </Field>
              </>
            )}
            <Field label="Email">
              <input
                required
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
              />
            </Field>
            <Field label="Password">
              <input
                required
                type="password"
                minLength={mode === "register" ? 12 : 1}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Your password"
              />
            </Field>
            <Button type="submit" className="live-full-button" disabled={busy === "auth"}>
              <ArrowRight size={15} /> {mode === "login" ? "Enter workspace" : "Create workspace"}
            </Button>
          </motion.form>
        </main>
      </MotionConfig>
    );
  const nav = [
    { id: "overview" as View, label: "Overview", icon: BrainCircuit },
    { id: "campaigns" as View, label: "Campaigns", icon: Sparkles },
    { id: "brain" as View, label: "Brand Brain", icon: Search },
    { id: "media" as View, label: "Content library", icon: Image },
    { id: "publishing" as View, label: "Calendar & publishing", icon: CalendarDays },
  ];
  const overview = (
    <>
      <Reveal className="live-hero live-glow" onMouseMove={handleGlow}>
        <ParticleField pulse={pulse} />
        <div>
          <p className="live-kicker">Live staging workspace</p>
          <h1>Good to see you, {user?.display_name?.split(" ")[0] ?? "there"}.</h1>
          <p>
            <TypewriterText text="Your VAE control room is connected to the FastAPI workspace." />
          </p>
        </div>
        <div className="live-hero-tools">
          <AiOrb state={busy === "load" ? "thinking" : notice ? "success" : "idle"} />
          <span className="live-connected">
            <i /> API connected
          </span>
          <VoiceIndicator />
        </div>
      </Reveal>
      <Reveal className="live-stats bento-grid">
        {metricOrder.map((metric) => {
          const metricData = {
            sources: [BrainCircuit, "Brand Brain", documents.length, "indexed sources"],
            campaigns: [Sparkles, "Campaigns", campaigns.length, "in workspace"],
            approval: [
              ShieldCheck,
              "Approval queue",
              campaigns.filter((item) => item.status === "awaiting_approval").length,
              "human decisions",
            ],
            assets: [Image, "Media assets", assets.length, "generated assets"],
          }[metric] ?? [Sparkles, "Signals", 0, "awaiting data"];
          const Icon = metricData[0] as typeof BrainCircuit;
          return (
            <DepthCard
              key={metric}
              className="metric-card"
              onDragOver={(event) => event.preventDefault()}
              onDrop={() => {
                if (!dragMetric || dragMetric === metric) return;
                setMetricOrder((items) => {
                  const next = [...items];
                  const from = next.indexOf(dragMetric);
                  const to = next.indexOf(metric);
                  next.splice(from, 1);
                  next.splice(to, 0, dragMetric);
                  return next;
                });
                setDragMetric(null);
              }}
            >
              <button
                className="metric-drag-handle"
                draggable
                onDragStart={() => setDragMetric(metric)}
                aria-label={`Reorder ${metric}`}
              >
                <Icon size={18} />
              </button>
              <small>{metricData[1] as string}</small>
              <strong>{metricData[2] as number}</strong>
              <span>{metricData[3] as string}</span>
            </DepthCard>
          );
        })}
      </Reveal>
      <section className="live-panel">
        <div className="live-panel-head">
          <div>
            <p className="live-kicker">Pipeline</p>
            <h2>Recent campaigns</h2>
          </div>
          <Button size="sm" onClick={() => setView("campaigns")}>
            <Plus size={14} /> New campaign
          </Button>
        </div>
        {campaigns.length ? (
          campaigns.map((item) => (
            <button
              className="live-list-row"
              key={item.id}
              onClick={() => {
                setSelected(item.id);
                setView("campaigns");
              }}
            >
              <Sparkles size={16} />
              <span>
                <b>{item.name}</b>
                <small>
                  {item.platforms.join(" · ")} · {date(item.updated_at)}
                </small>
              </span>
              <Status value={item.status} />
              <ArrowRight size={15} />
            </button>
          ))
        ) : (
          <Empty
            icon={Sparkles}
            title="Your campaign runway is clear"
            body="Create a campaign brief to start generating grounded content."
          />
        )}
      </section>
    </>
  );
  const campaignsView = (
    <div className="live-columns">
      <section className="live-panel">
        <p className="live-kicker">New campaign</p>
        <h2>From brief to review</h2>
        <form className="live-form" onSubmit={createCampaign}>
          <Field label="Campaign name">
            <input
              required
              value={campaignName}
              onChange={(e) => setCampaignName(e.target.value)}
              placeholder="Q4 product launch"
            />
          </Field>
          <Field label="Objective">
            <textarea
              required
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              placeholder="What should this campaign achieve?"
            />
          </Field>
          <Field label="Product or service">
            <input
              required
              value={product}
              onChange={(e) => setProduct(e.target.value)}
              placeholder="VAE Studio"
            />
          </Field>
          <Field label="Audience">
            <input
              required
              value={audience}
              onChange={(e) => setAudience(e.target.value)}
              placeholder="Marketing leaders"
            />
          </Field>
          <div className="live-form-grid">
            <Field label="Primary platform">
              <select value={platform} onChange={(e) => setPlatform(e.target.value as Platform)}>
                {platforms.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Instructions">
              <input
                value={instructions}
                onChange={(e) => setInstructions(e.target.value)}
                placeholder="Optional direction"
              />
            </Field>
          </div>
          <Button type="submit" disabled={busy === "campaign"}>
            <Sparkles size={14} /> Create & generate
          </Button>
        </form>
      </section>
      <div className="live-stack">
        <section className="live-panel">
          <p className="live-kicker">Human approval boundary</p>
          <h2>Review queue</h2>
          {campaigns.map((item) => (
            <button
              className={cn("live-list-row", selected === item.id && "selected")}
              key={item.id}
              onClick={() => setSelected(item.id)}
            >
              <Sparkles size={15} />
              <span>
                <b>{item.name}</b>
                <small>{date(item.updated_at)}</small>
              </span>
              <Status value={item.status} />
            </button>
          ))}
        </section>
        <section className="live-panel">
          {currentCampaign ? (
            <>
              <div className="live-panel-head">
                <div>
                  <p className="live-kicker">Generated variants</p>
                  <h2>{currentCampaign.name}</h2>
                </div>
                <Status value={currentCampaign.status} />
              </div>
              {variants.map((variant) => (
                <article className="live-variant" key={variant.id}>
                  <div>
                    <b>{variant.platform}</b>
                    <span>{Math.round(variant.quality_score)}/100</span>
                  </div>
                  <p>{variant.caption}</p>
                  <small>
                    {variant.citations.length} evidence references · {variant.status}
                  </small>
                </article>
              ))}
              {currentCampaign.status === "awaiting_approval" && (
                <div className="live-approval">
                  <Button variant="secondary" onClick={() => void decide("reject")}>
                    Request changes
                  </Button>
                  <Button onClick={() => void decide("approve")}>
                    <Check size={14} /> Approve
                  </Button>
                </div>
              )}
            </>
          ) : (
            <Empty
              icon={ShieldCheck}
              title="Select a campaign"
              body="Inspect variants and approve them before publishing."
            />
          )}
        </section>
      </div>
    </div>
  );
  const brainView = (
    <div className="live-columns">
      <section className="live-panel">
        <p className="live-kicker">Brand Brain</p>
        <h2>Profile & evidence</h2>
        {brands[0] ? (
          <div className="live-brand">
            <div>{initial(brands[0].name)}</div>
            <span>
              <b>{brands[0].name}</b>
              <small>{brands[0].description}</small>
            </span>
          </div>
        ) : (
          <form className="live-form" onSubmit={createBrand}>
            <Field label="Brand name">
              <input required value={brandName} onChange={(e) => setBrandName(e.target.value)} />
            </Field>
            <Field label="Description">
              <textarea
                value={brandDescription}
                onChange={(e) => setBrandDescription(e.target.value)}
              />
            </Field>
            <Button type="submit">Create brand profile</Button>
          </form>
        )}
        <div className="live-divider" />
        <form className="live-form" onSubmit={ingest}>
          <Field label="Source title">
            <input
              required
              value={sourceTitle}
              onChange={(e) => setSourceTitle(e.target.value)}
              placeholder="Positioning guide"
            />
          </Field>
          <Field label="Approved source content">
            <textarea
              required
              className="live-tall"
              value={sourceText}
              onChange={(e) => setSourceText(e.target.value)}
              placeholder="Paste verified product evidence…"
            />
          </Field>
          <Button type="submit" disabled={busy === "ingest"}>
            <Upload size={14} /> Index source
          </Button>
        </form>
      </section>
      <div className="live-stack">
        <section className="live-panel">
          <p className="live-kicker">Retrieval preview</p>
          <h2>Ask the Brain</h2>
          <form className="live-search" onSubmit={searchBrain}>
            <input
              required
              minLength={2}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="What proof supports this claim?"
            />
            <Button size="sm" type="submit">
              Search
            </Button>
          </form>
          {evidence.map((item) => (
            <article className="live-evidence" key={item.chunk_id}>
              <b>{item.document_title}</b>
              <span>{Math.round(item.score * 100)}% match</span>
              <p>{item.excerpt}</p>
            </article>
          ))}
        </section>
        <section className="live-panel">
          <p className="live-kicker">Indexed sources</p>
          <h2>
            {documents.length} source{documents.length === 1 ? "" : "s"}
          </h2>
          {documents.length ? (
            documents.map((doc) => (
              <div className="live-list-row" key={doc.id}>
                <FileText size={15} />
                <span>
                  <b>{doc.title}</b>
                  <small>
                    {doc.source_type} · {doc.content_length.toLocaleString()} chars
                  </small>
                </span>
                <Status value={doc.status} />
              </div>
            ))
          ) : (
            <Empty
              icon={FileText}
              title="Brand Brain is waiting"
              body="Index an approved source to ground generation."
            />
          )}
        </section>
      </div>
    </div>
  );
  const mediaView = (
    <div className="live-columns">
      <section className="live-panel">
        <p className="live-kicker">Image studio</p>
        <h2>Generate a visual</h2>
        <form className="live-form" onSubmit={createImage}>
          <Field label="Campaign">
            <select
              required
              value={mediaCampaign}
              onChange={(e) => setMediaCampaign(e.target.value)}
            >
              <option value="">Select campaign</option>
              {campaigns.map((item) => (
                <option value={item.id} key={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Visual direction">
            <textarea
              required
              className="live-tall"
              value={mediaPrompt}
              onChange={(e) => setMediaPrompt(e.target.value)}
              placeholder="Premium editorial composition with chartreuse energy…"
            />
          </Field>
          <Button type="submit" disabled={busy === "image"}>
            <Sparkles size={14} /> Generate visual
          </Button>
        </form>
      </section>
      <section className="live-panel">
        <p className="live-kicker">Asset library</p>
        <h2>
          {assets.length} generated asset{assets.length === 1 ? "" : "s"}
        </h2>
        {assets.length ? (
          assets.map((asset) => (
            <article className="live-asset" key={asset.id}>
              <Image size={22} />
              <Status value={asset.status} />
              <b>{asset.filename}</b>
              <small>
                {asset.media_type} · {date(asset.created_at)}
              </small>
              {asset.download_url && (
                <button type="button" onClick={() => void downloadAsset(asset)}>
                  Open asset <ArrowRight size={12} />
                </button>
              )}
            </article>
          ))
        ) : (
          <Empty
            icon={Image}
            title="Your library is empty"
            body="Generate the first visual from a campaign brief."
          />
        )}
      </section>
    </div>
  );
  const publishingView = (
    <div className="live-columns">
      <section className="live-panel">
        <p className="live-kicker">Staging connector</p>
        <h2>Connect publisher</h2>
        <p className="live-helper">
          OAuth approval remains a production step; this creates a safely referenced staging
          account.
        </p>
        <form className="live-form" onSubmit={connect}>
          <Field label="Platform">
            <select
              value={accountPlatform}
              onChange={(e) => setAccountPlatform(e.target.value as Platform)}
            >
              {platforms.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.label}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Display name">
            <input
              required
              value={accountName}
              onChange={(e) => setAccountName(e.target.value)}
              placeholder="VAE on LinkedIn"
            />
          </Field>
          <Field label="External account ID">
            <input
              required
              value={externalId}
              onChange={(e) => setExternalId(e.target.value)}
              placeholder="company-page-id"
            />
          </Field>
          <Button type="submit" disabled={busy === "connect"}>
            <Plus size={14} /> Connect staging account
          </Button>
        </form>
        {accounts.map((account) => (
          <div className="live-list-row" key={account.id}>
            <Send size={15} />
            <span>
              <b>{account.display_name}</b>
              <small>
                {account.platform} · {account.capabilities.join(", ")}
              </small>
            </span>
            <Status value={account.status} />
          </div>
        ))}
      </section>
      <div className="live-stack">
        <section className="live-panel">
          <p className="live-kicker">Controlled distribution</p>
          <h2>Publish or schedule</h2>
          <div className="live-form">
            <Field label="Campaign">
              <select value={publishCampaign} onChange={(e) => setPublishCampaign(e.target.value)}>
                <option value="">Select campaign</option>
                {campaigns.map((item) => (
                  <option value={item.id} key={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Account">
              <select value={publishAccount} onChange={(e) => setPublishAccount(e.target.value)}>
                <option value="">Select account</option>
                {accounts.map((item) => (
                  <option value={item.id} key={item.id}>
                    {item.display_name}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Post copy">
              <textarea
                value={publishText}
                onChange={(e) => setPublishText(e.target.value)}
                placeholder={currentVariant?.caption || "Choose an approved variant."}
              />
            </Field>
            <Field label="Schedule time">
              <input
                type="datetime-local"
                value={scheduleAt}
                onChange={(e) => setScheduleAt(e.target.value)}
              />
            </Field>
            <div className="live-approval">
              <Button variant="secondary" onClick={() => void publish(true)}>
                <CalendarDays size={14} /> Schedule
              </Button>
              <Button onClick={() => void publish(false)}>
                <Send size={14} /> Publish now
              </Button>
            </div>
          </div>
        </section>
        <section className="live-panel">
          <p className="live-kicker">Delivery queue</p>
          <h2>Scheduled posts</h2>
          {scheduled.length ? (
            scheduled.map((item) => (
              <div className="live-list-row" key={item.id}>
                <CalendarDays size={15} />
                <span>
                  <b>{date(item.scheduled_for)}</b>
                  <small>{item.payload.text?.slice(0, 72) || "Campaign post"}</small>
                </span>
                <Status value={item.status} />
              </div>
            ))
          ) : (
            <Empty
              icon={CalendarDays}
              title="No scheduled posts"
              body="Approved content can be scheduled here."
            />
          )}
        </section>
      </div>
    </div>
  );
  const content =
    view === "overview"
      ? overview
      : view === "campaigns"
        ? campaignsView
        : view === "brain"
          ? brainView
          : view === "media"
            ? mediaView
            : publishingView;
  const paletteItems = [
    ...nav.map((item) => ({
      label: `Open ${item.label}`,
      hint: "View",
      onSelect: () => setView(item.id),
    })),
    { label: "New campaign", hint: "Create", onSelect: () => setView("campaigns") },
    {
      label: theme === "dark" ? "Use light theme" : "Use dark theme",
      hint: "Appearance",
      onSelect: () => setTheme(theme === "dark" ? "light" : "dark"),
    },
    {
      label: soundEnabled ? "Mute ambient sound" : "Enable ambient sound",
      hint: "Audio",
      onSelect: () => setSoundEnabled(!soundEnabled),
    },
  ];
  return (
    <MotionConfig reducedMotion="user">
      <main className="live-app">
        <WebglBackground />
        <GrainOverlay />
        {paletteOpen && (
          <CommandPalette items={paletteItems} onClose={() => setPaletteOpen(false)} />
        )}
        {tourOpen && (
          <Onboarding
            onDismiss={() => {
              window.localStorage.setItem("vae.tour-complete", "1");
              setTourOpen(false);
            }}
            onComplete={() => {
              window.localStorage.setItem("vae.tour-complete", "1");
              setTourOpen(false);
            }}
          />
        )}
        <aside className={cn("live-sidebar", sidebar && "open")}>
          <div className="live-logo">
            <span />
            <b>VAE</b>
            <button onClick={() => setSidebar(false)} aria-label="Close">
              <X size={17} />
            </button>
          </div>
          <div className="live-workspace">
            <div>{initial(workspace?.name)}</div>
            <span>
              <b>{workspace?.name}</b>
              <small>{workspace?.timezone}</small>
            </span>
          </div>
          <nav>
            {nav.map((item) => (
              <button
                className={cn(view === item.id && "active")}
                key={item.id}
                onClick={() => {
                  setView(item.id);
                  setSidebar(false);
                }}
              >
                <item.icon size={17} />
                <span>{item.label}</span>
              </button>
            ))}
          </nav>
          <div className="live-sidebar-foot">
            <div className="live-user">
              <div>{initial(user?.display_name)}</div>
              <span>
                <b>{user?.display_name}</b>
                <small>{user?.email}</small>
              </span>
            </div>
            <button onClick={reset}>
              <LogOut size={15} /> Sign out
            </button>
          </div>
        </aside>
        {sidebar && (
          <button
            className="live-backdrop"
            onClick={() => setSidebar(false)}
            aria-label="Close navigation"
          />
        )}
        <section className="live-main" data-scrolled={scrolled}>
          <header className="live-topbar">
            <button onClick={() => setSidebar(true)} aria-label="Open navigation">
              <Menu size={19} />
            </button>
            <span>
              <i /> Staging environment
            </span>
            <div>
              <button className="live-command-trigger" onClick={() => setPaletteOpen(true)}>
                <Search size={14} /> <span>Search</span> <kbd>⌘K</kbd>
              </button>
              <SoundToggle enabled={soundEnabled} onChange={setSoundEnabled} />
              <button
                className="live-theme-toggle"
                onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              >
                {theme === "dark" ? "Light" : "Dark"}
              </button>
              <button className="live-refresh" onClick={() => token && void load(token)}>
                <RefreshCw size={15} /> Refresh
              </button>
              <Button size="sm" onClick={() => setView("campaigns")}>
                <Plus size={14} /> New campaign
              </Button>
            </div>
          </header>
          <div
            className="live-content"
            style={{ "--glass-alpha": scrolled ? 0.82 : 0.62 } as CSSProperties}
          >
            <AnimatePresence>
              {notice && (
                <motion.div
                  className="live-alert success"
                  variants={overlayFade}
                  initial="hidden"
                  animate="show"
                  exit="exit"
                >
                  <Check size={15} /> {notice}
                  <button onClick={() => setNotice(null)}>
                    <X size={14} />
                  </button>
                </motion.div>
              )}
              {error && (
                <motion.div
                  className="live-alert error"
                  variants={overlayFade}
                  initial="hidden"
                  animate="show"
                  exit="exit"
                >
                  <CircleAlert size={15} /> {error}
                  <button onClick={() => setError(null)}>
                    <X size={14} />
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
            {busy === "load" ? (
              <div className="live-stats">
                {[0, 1, 2, 3].map((i) => (
                  <article key={i}>
                    <div className="live-skeleton" style={{ width: 18, height: 18 }} />
                    <div className="live-skeleton" style={{ width: "60%", height: 10 }} />
                    <div className="live-skeleton" style={{ width: "40%", height: 26 }} />
                    <div className="live-skeleton" style={{ width: "70%", height: 9 }} />
                  </article>
                ))}
              </div>
            ) : (
              <AnimatePresence mode="wait">
                <motion.div
                  key={view}
                  variants={variantSwap}
                  initial="hidden"
                  animate="show"
                  exit="exit"
                >
                  {content}
                </motion.div>
              </AnimatePresence>
            )}
          </div>
        </section>
      </main>
    </MotionConfig>
  );
}
