import { useEffect, useState } from "react";

import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  BarChart3,
  Brain,
  CheckCircle2,
  ChevronRight,
  Circle,
  Clock3,
  Database,
  FileSearch,
  GitBranch,
  History,
  LayoutDashboard,
  Menu,
  Network,
  Plus,
  RefreshCw,
  Search,
  Settings,
  ShieldCheck,
  Sparkles,
  Target,
} from "lucide-react";

import NewDecision from "./NewDecision";
import "./App.css";

const API_BASE_URL = "http://localhost:8000";

const navigation = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "new", label: "New Decision", icon: Plus },
  { id: "decisions", label: "Decisions", icon: History },
  { id: "investigate", label: "Investigate", icon: FileSearch },
  { id: "analytics", label: "Analytics", icon: BarChart3 },
  { id: "agents", label: "Agent Network", icon: Network },
  { id: "rules", label: "Business Rules", icon: GitBranch },
  { id: "audit", label: "Audit Trail", icon: ShieldCheck },
  { id: "system", label: "System Status", icon: Activity },
];

function App() {
  const [activePage, setActivePage] = useState("dashboard");
  const [latestDecision, setLatestDecision] = useState(null);
  const [selectedRequestId, setSelectedRequestId] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleNavigation = (page) => {
    setActivePage(page);
    setSidebarOpen(false);
  };

  const handleDecisionComplete = (result) => {
    setLatestDecision(result);
    setSelectedRequestId(result?.request_id || null);
    setActivePage("result");
  };

  const handleOpenInvestigation = (requestId) => {
    if (!requestId) return;
    setSelectedRequestId(requestId);
    setActivePage("investigate");
  };

  return (
    <div className="app-shell">
      {sidebarOpen && (
        <button
          className="mobile-overlay"
          onClick={() => setSidebarOpen(false)}
          aria-label="Close menu"
        />
      )}

      <aside className={`app-sidebar ${sidebarOpen ? "sidebar-open" : ""}`}>
        <div className="brand">
          <div className="brand-mark"><Brain size={19} /></div>
          <div>
            <div className="brand-name">DecisionOS</div>
            <div className="brand-subtitle">Multi-Agent Intelligence</div>
          </div>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section-label">WORKSPACE</div>
          {navigation.slice(0, 5).map((item) => (
            <SidebarItem
              key={item.id}
              item={item}
              activePage={activePage}
              onClick={() => handleNavigation(item.id)}
            />
          ))}

          <div className="nav-section-label nav-section-spacer">GOVERNANCE</div>
          {navigation.slice(5).map((item) => (
            <SidebarItem
              key={item.id}
              item={item}
              activePage={activePage}
              onClick={() => handleNavigation(item.id)}
            />
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="system-indicator">
            <div className="status-dot" />
            <div>
              <span className="status-title">Engine Online</span>
              <span className="status-caption">Gemini + PostgreSQL</span>
            </div>
          </div>

          <button className="sidebar-settings" onClick={() => handleNavigation("settings")}>
            <Settings size={17} />
            Settings
          </button>
        </div>
      </aside>

      <main className="app-main">
        <header className="app-header">
          <button
            className="mobile-menu-button"
            onClick={() => setSidebarOpen(true)}
            aria-label="Open menu"
          >
            <Menu size={20} />
          </button>

          <div className="header-breadcrumb">
            <span>DecisionOS</span>
            <ChevronRight size={14} />
            <strong>{getPageTitle(activePage)}</strong>
          </div>

          <div className="header-actions">
            <div className="header-status">
              <span className="header-status-dot" />
              System operational
            </div>
            <div className="header-search">
              <Search size={15} />
              <input placeholder="Search decisions..." />
              <span className="search-shortcut">/</span>
            </div>
          </div>
        </header>

        <div className="page-container">
          {activePage === "dashboard" && (
            <Dashboard
              latestDecision={latestDecision}
              onNewDecision={() => handleNavigation("new")}
              onOpenInvestigation={handleOpenInvestigation}
            />
          )}

          {activePage === "new" && <NewDecision onComplete={handleDecisionComplete} />}

          {activePage === "result" && (
            <DecisionResult
              result={latestDecision}
              onBack={() => handleNavigation("new")}
              onInvestigate={handleOpenInvestigation}
            />
          )}

          {activePage === "decisions" && (
            <DecisionHistory onOpenInvestigation={handleOpenInvestigation} />
          )}

          {activePage === "investigate" && (
            <Investigation
              requestId={selectedRequestId}
              onBack={() => handleNavigation("decisions")}
            />
          )}

          {activePage === "analytics" && <AnalyticsPage />}

          {activePage === "agents" && <AgentNetwork />}

          {activePage === "rules" && <BusinessRules />}

          {activePage === "audit" && <AuditTrail />}

          {activePage === "system" && <SystemStatus />}

          {activePage === "settings" && (
            <PlaceholderPage
              title="Settings"
              description="Configure engine behavior, model preferences and workspace options."
              icon={Settings}
            />
          )}
        </div>
      </main>
    </div>
  );
}

function SidebarItem({ item, activePage, onClick }) {
  const Icon = item.icon;
  return (
    <button
      className={`sidebar-nav-item ${activePage === item.id ? "active" : ""}`}
      onClick={onClick}
    >
      <Icon size={17} />
      <span>{item.label}</span>
    </button>
  );
}

function getPageTitle(page) {
  const titles = {
    dashboard: "Dashboard",
    new: "New Decision",
    result: "Decision Result",
    decisions: "Decisions",
    investigate: "Investigate",
    analytics: "Analytics",
    agents: "Agent Network",
    rules: "Business Rules",
    audit: "Audit Trail",
    system: "System Status",
    settings: "Settings",
  };
  return titles[page] || "Dashboard";
}

function Dashboard({ onNewDecision, onOpenInvestigation, latestDecision }) {
  const [recentItems, setRecentItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    async function loadRecent() {
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/business-questions?limit=6`);
        if (!response.ok) throw new Error();
        const data = await response.json();
        if (mounted) setRecentItems(data.items || []);
      } catch {
        if (mounted) setRecentItems([]);
      } finally {
        if (mounted) setLoading(false);
      }
    }

    loadRecent();
    return () => { mounted = false; };
  }, []);

  return (
    <div className="dashboard-page">
      <section className="hero-section">
        <div>
          <div className="hero-eyebrow">
            <Sparkles size={14} />
            AI-POWERED BUSINESS DECISION ENGINE
          </div>
          <h1>Business decisions,<br />reasoned by agents.</h1>
          <p>
            Ask complex business questions and let a dynamic network of AI specialists investigate,
            critique and synthesize the evidence.
          </p>
          <button className="primary-action" onClick={onNewDecision}>
            <Plus size={17} />
            Ask a Business Question
            <ArrowLeft size={16} className="action-arrow" />
          </button>
        </div>

        <div className="hero-network">
          <div className="hero-network-core"><Brain size={24} /></div>
          <div className="hero-node hero-node-one"><Database size={14} /></div>
          <div className="hero-node hero-node-two"><Target size={14} /></div>
          <div className="hero-node hero-node-three"><ShieldCheck size={14} /></div>
          <div className="hero-line hero-line-one" />
          <div className="hero-line hero-line-two" />
          <div className="hero-line hero-line-three" />
        </div>
      </section>

      <section className="metric-grid">
        <MetricCard label="Questions Processed" value={recentItems.length || "—"} caption="Latest records" icon={Activity} />
        <MetricCard label="Business Areas" value="13" caption="Specialist domains" icon={Network} />
        <MetricCard label="Agent Stages" value="6" caption="Router → Synthesis" icon={GitBranch} />
        <MetricCard label="Engine Status" value="Online" caption="Gemini + PostgreSQL" icon={CheckCircle2} />
      </section>

      <section className="dashboard-grid">
        <div className="dashboard-card">
          <div className="card-header">
            <div><span className="card-kicker">ACTIVITY</span><h2>Recent Questions</h2></div>
            <button
              className="text-button"
              onClick={() => onOpenInvestigation(recentItems[0]?.request_id)}
              disabled={!recentItems[0]}
            >
              View latest <ChevronRight size={14} />
            </button>
          </div>

          {loading ? (
            <div className="empty-state">Loading decisions...</div>
          ) : recentItems.length === 0 ? (
            <div className="empty-state">
              <FileSearch size={22} />
              <span>No business questions yet.</span>
              <button className="text-button" onClick={onNewDecision}>Run your first question <ChevronRight size={14} /></button>
            </div>
          ) : (
            <div className="recent-list">
              {recentItems.map((item) => (
                <button
                  key={item.request_id}
                  className="recent-item"
                  onClick={() => onOpenInvestigation(item.request_id)}
                >
                  <div className="recent-item-main">
                    <div className="recent-item-title">{item.question}</div>
                    <div className="recent-item-meta">
                      <span>{item.business_area}</span><span>•</span><span>{item.question_type}</span>
                    </div>
                  </div>
                  <div className="recent-item-side">
                    <StatusBadge status={item.status} />
                    <ChevronRight size={15} />
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="dashboard-card">
          <div className="card-header">
            <div><span className="card-kicker">AGENT NETWORK</span><h2>Active Intelligence Layer</h2></div>
          </div>
          <div className="mini-agent-list">
            <AgentMini icon={GitBranch} name="Question Router" description="Semantic classification" />
            <AgentMini icon={Database} name="Evidence Agent" description="Evidence validation" />
            <AgentMini icon={Network} name="Specialists" description="Dynamic domain analysis" />
            <AgentMini icon={ShieldCheck} name="Critic" description="Reasoning validation" />
            <AgentMini icon={Sparkles} name="Synthesis" description="Final business answer" />
          </div>
        </div>
      </section>

      {latestDecision && (
        <div className="latest-result-strip">
          <div><span>Latest request</span><strong>{latestDecision.request_id}</strong></div>
          <button className="text-button" onClick={() => onOpenInvestigation(latestDecision.request_id)}>
            Open investigation <ChevronRight size={14} />
          </button>
        </div>
      )}
    </div>
  );
}

function MetricCard({ label, value, caption, icon: Icon }) {
  return (
    <div className="metric-card">
      <div className="metric-icon"><Icon size={17} /></div>
      <div>
        <span className="metric-label">{label}</span>
        <div className="metric-value">{value}</div>
        <span className="metric-caption">{caption}</span>
      </div>
    </div>
  );
}

function AgentMini({ icon: Icon, name, description }) {
  return (
    <div className="mini-agent">
      <div className="mini-agent-icon"><Icon size={15} /></div>
      <div><strong>{name}</strong><span>{description}</span></div>
      <CheckCircle2 size={15} className="mini-agent-status" />
    </div>
  );
}

/* ============================================================
   ANALYTICS
   Progress bars intentionally removed.
   The analytics page now uses compact stat rows/cards.
   ============================================================ */

function AnalyticsPage() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  async function loadAnalytics(showRefreshState = false) {
    try {
      if (showRefreshState) setRefreshing(true);
      else setLoading(true);

      setError("");

      const response = await fetch(`${API_BASE_URL}/api/v1/analytics`);
      if (!response.ok) throw new Error("Unable to load decision analytics.");

      const data = await response.json();
      setAnalytics(data);
    } catch (err) {
      setError(err.message || "Unable to load decision analytics.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    loadAnalytics(false);
  }, []);

  if (loading) {
    return (
      <div className="empty-state full-page-empty">
        <BarChart3 size={22} />
        Loading decision analytics...
      </div>
    );
  }

  if (error) {
    return (
      <div className="empty-state full-page-empty">
        <AlertTriangle size={22} />
        <span>{error}</span>
        <button className="text-button" onClick={() => loadAnalytics(true)}>
          Try again <RefreshCw size={14} />
        </button>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="empty-state full-page-empty">
        <BarChart3 size={22} />
        No analytics data available.
      </div>
    );
  }

  const overview = analytics.overview || {};
  const businessAreas = analytics.business_areas || [];
  const questionTypes = analytics.question_types || [];
  const agents = analytics.agents || [];
  const recentActivity = analytics.recent_activity || [];

  const questionTypeCards = [
    ["Investigate", overview.investigate_count, FileSearch],
    ["Analyze", overview.analyze_count, BarChart3],
    ["Compare", overview.compare_count, GitBranch],
    ["Predict", overview.predict_count, Target],
    ["Explain", overview.explain_count, Search],
    ["Optimize", overview.optimize_count, Sparkles],
  ];

  return (
    <div className="analytics-page">
      <div className="page-heading">
        <div>
          <div className="hero-eyebrow"><BarChart3 size={14} />DECISION ANALYTICS</div>
          <h1>Decision intelligence</h1>
          <p>
            Analyze business questions, confidence, question patterns and agent performance using persisted DecisionOS data.
          </p>
        </div>

        <button className="secondary-action" onClick={() => loadAnalytics(true)} disabled={refreshing}>
          <RefreshCw className={refreshing ? "analytics-spin" : ""} size={16} />
          {refreshing ? "Refreshing..." : "Refresh analytics"}
        </button>
      </div>

      <section className="metric-grid analytics-metric-grid">
        <MetricCard label="Total Questions" value={overview.total_questions ?? 0} caption="All persisted business questions" icon={Activity} />
        <MetricCard label="Completed" value={overview.completed_questions ?? 0} caption="Successfully processed" icon={CheckCircle2} />
        <MetricCard label="Average Confidence" value={formatConfidence(overview.average_confidence)} caption="Across completed decisions" icon={Target} />
        <MetricCard label="Top Business Area" value={overview.top_business_area || "—"} caption="Most active domain" icon={Network} />
      </section>

      <section className="analytics-grid analytics-grid-top">
        <div className="dashboard-card">
          <div className="card-header">
            <div><span className="card-kicker">QUESTION TYPES</span><h2>Decision workload</h2></div>
          </div>

          <div className="analytics-type-grid">
            {questionTypeCards.map(([label, value, Icon]) => (
              <div className="analytics-type-card" key={label}>
                <div className="analytics-type-top">
                  <span>{label}</span>
                  <Icon size={15} />
                </div>
                <strong>{value ?? 0}</strong>
              </div>
            ))}
          </div>
        </div>

        <div className="dashboard-card">
          <div className="card-header">
            <div><span className="card-kicker">STATUS</span><h2>Execution health</h2></div>
          </div>

          <div className="analytics-health-list">
            <AnalyticsHealthStat
              label="Completed questions"
              value={overview.completed_questions ?? 0}
              suffix={`of ${overview.total_questions ?? 0}`}
              icon={CheckCircle2}
            />
            <AnalyticsHealthStat
              label="Failed questions"
              value={overview.failed_questions ?? 0}
              suffix={`of ${overview.total_questions ?? 0}`}
              icon={AlertTriangle}
            />
            <AnalyticsHealthStat
              label="Average confidence"
              value={formatConfidence(overview.average_confidence)}
              suffix="overall"
              icon={Target}
            />
          </div>
        </div>
      </section>

      <section className="analytics-grid analytics-grid-two">
        <div className="dashboard-card">
          <div className="card-header">
            <div><span className="card-kicker">BUSINESS AREAS</span><h2>Where questions are coming from</h2></div>
            <span className="section-count">{businessAreas.length} areas</span>
          </div>

          {businessAreas.length === 0 ? (
            <div className="empty-state">No business-area data available.</div>
          ) : (
            <div className="analytics-stat-list">
              {businessAreas.map((item) => (
                <div className="analytics-stat-row" key={item.business_area}>
                  <div className="analytics-stat-icon"><Network size={14} /></div>
                  <div className="analytics-stat-main">
                    <strong>{item.business_area}</strong>
                    <span>Average confidence {formatConfidence(item.average_confidence)}</span>
                  </div>
                  <div className="analytics-stat-value">
                    <strong>{item.question_count}</strong>
                    <span>questions</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="dashboard-card">
          <div className="card-header">
            <div><span className="card-kicker">QUESTION MIX</span><h2>Question types</h2></div>
          </div>

          {questionTypes.length === 0 ? (
            <div className="empty-state">No question-type data available.</div>
          ) : (
            <div className="analytics-stat-list">
              {questionTypes.map((item) => (
                <div className="analytics-stat-row" key={item.question_type}>
                  <div className="analytics-stat-icon"><BarChart3 size={14} /></div>
                  <div className="analytics-stat-main">
                    <strong>{item.question_type}</strong>
                    <span>Recorded question type</span>
                  </div>
                  <div className="analytics-stat-value">
                    <strong>{item.question_count}</strong>
                    <span>questions</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      <section className="dashboard-card">
        <div className="card-header">
          <div><span className="card-kicker">AGENT PERFORMANCE</span><h2>Agent execution metrics</h2></div>
          <span className="section-count">{agents.length} agents</span>
        </div>

        {agents.length === 0 ? (
          <div className="empty-state">No agent execution data available.</div>
        ) : (
          <div className="analytics-table-wrap">
            <table className="analytics-table">
              <thead>
                <tr>
                  <th>Agent</th>
                  <th>Runs</th>
                  <th>Completed</th>
                  <th>Failed</th>
                  <th>Avg Score</th>
                </tr>
              </thead>
              <tbody>
                {agents.map((agent) => (
                  <tr key={agent.agent_name}>
                    <td>
                      <div className="analytics-agent-name">
                        <div className="analytics-agent-icon"><Brain size={13} /></div>
                        <span>{formatAgentName(agent.agent_name)}</span>
                      </div>
                    </td>
                    <td>{agent.run_count ?? 0}</td>
                    <td>{agent.completed_count ?? 0}</td>
                    <td>{agent.failed_count ?? 0}</td>
                    <td>{agent.average_score != null ? Number(agent.average_score).toFixed(1) : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="dashboard-card analytics-recent-card">
        <div className="card-header">
          <div><span className="card-kicker">RECENT ACTIVITY</span><h2>Latest business questions</h2></div>
          <span className="section-count">{recentActivity.length} records</span>
        </div>

        {recentActivity.length === 0 ? (
          <div className="empty-state">No recent activity available.</div>
        ) : (
          <div className="analytics-recent-list">
            {recentActivity.map((item) => (
              <div className="analytics-recent-row" key={item.request_id}>
                <div className="analytics-recent-main">
                  <strong>{item.question}</strong>
                  <span>{item.request_id} • {item.business_area} • {item.question_type}</span>
                </div>
                <div className="analytics-recent-confidence">
                  <span>Confidence</span>
                  <strong>{formatConfidence(item.confidence)}</strong>
                </div>
                <StatusBadge status={item.status} />
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function AnalyticsHealthStat({ label, value, suffix, icon: Icon }) {
  return (
    <div className="analytics-health-stat">
      <div className="analytics-health-icon"><Icon size={15} /></div>
      <div className="analytics-health-main">
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
      <span className="analytics-health-suffix">{suffix}</span>
    </div>
  );
}

function DecisionResult({ result, onBack, onInvestigate }) {
  if (!result) {
    return <PlaceholderPage title="No Decision Result" description="Run a business question to see the synthesized result." icon={FileSearch} />;
  }

  return (
    <div className="result-page">
      <button className="back-button" onClick={onBack}><ArrowLeft size={16} />Back to New Decision</button>

      <div className="result-header">
        <div>
          <div className="hero-eyebrow"><Sparkles size={14} />DECISION ENGINE RESULT</div>
          <h1>{result.question}</h1>
          <div className="result-meta">
            <span>{result.business_area}</span><span>•</span><span>{result.question_type}</span><span>•</span><span>{result.request_id}</span>
          </div>
        </div>
        <StatusBadge status={result.status} />
      </div>

      <div className="result-summary-grid">
        <div className="answer-card">
          <div className="card-kicker">FINAL ANSWER</div>
          <p>{result.answer || "No final answer was generated."}</p>
          {result.recommendation && (
            <div className="recommendation-box"><span>RECOMMENDATION</span><strong>{result.recommendation}</strong></div>
          )}
        </div>
        <div className="confidence-card">
          <div className="card-kicker">CONFIDENCE</div>
          <div className="confidence-value">{formatConfidence(result.confidence)}</div>
          <div className="confidence-bar">
            <div
              className="confidence-fill"
              style={{ width: `${Math.max(0, Math.min(100, (result.confidence || 0) * 100))}%` }}
            />
          </div>
          <span>Based on evidence completeness, consistency and relevance.</span>
        </div>
      </div>

      <div className="result-section-grid">
        <ResultListCard title="Key Factors" items={result.key_factors} icon={Target} />
        <ResultListCard title="Risks" items={result.risks} icon={AlertTriangle} />
        <ResultListCard title="Assumptions" items={result.assumptions} icon={AlertTriangle} />
      </div>

      <RuleExecutionPanel ruleSummary={result.business_rules || result.rule_results} />

      <div className="result-section">
        <div className="section-heading">
          <div><span className="card-kicker">AGENT NETWORK</span><h2>Reasoning Trace</h2></div>
          <span className="section-count">{result.agents?.length || 0} agents</span>
        </div>
        <div className="agent-trace-list">
          {(result.agents || []).map((agent) => (
            <AgentTrace key={`${agent.agent_name}-${agent.status}`} agent={agent} />
          ))}
        </div>
      </div>

      <div className="result-section">
        <div className="section-heading"><div><span className="card-kicker">EVIDENCE</span><h2>Supporting Evidence</h2></div></div>
        {(result.evidence || []).length === 0 ? (
          <div className="empty-state">No structured evidence was returned.</div>
        ) : (
          <div className="evidence-list">
            {result.evidence.map((item, index) => (
              <div key={`${item.source}-${index}`} className="evidence-item">
                <div className="evidence-source">{item.source}</div>
                <div className="evidence-content">
                  <strong>{item.factor}</strong>
                  <span>{String(item.value)}</span>
                  <p>{item.reason}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="result-footer-actions">
        <button className="secondary-action" onClick={() => onInvestigate(result.request_id)}>
          <FileSearch size={16} />Investigate Full Run
        </button>
      </div>
    </div>
  );
}

function RuleExecutionPanel({ ruleSummary }) {
  const summary = ruleSummary || {};
  const evaluated = Number(summary.total_evaluated || 0);
  const matched = Number(summary.matched_count || 0);
  const matchedRules = Array.isArray(summary.matched_rules)
    ? summary.matched_rules
    : [];

  const panelStyle = {
    border: "1px solid #1d2836",
    borderRadius: "12px",
    background: "#0d141d",
    overflow: "hidden",
    marginBottom: "20px",
  };

  const headerStyle = {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: "16px",
    padding: "16px 18px",
    borderBottom: "1px solid #1d2836",
  };

  const statPill = {
    display: "inline-flex",
    alignItems: "center",
    gap: "6px",
    padding: "6px 9px",
    borderRadius: "999px",
    border: "1px solid #263244",
    background: "#121a25",
    color: "#9aa9bb",
    fontSize: "10px",
    fontWeight: 700,
  };

  return (
    <section style={panelStyle}>
      <div style={headerStyle}>
        <div>
          <span className="card-kicker">GOVERNANCE</span>
          <h2 style={{ margin: "5px 0 0", fontSize: "18px" }}>Business Rule Checks</h2>
          <p style={{ margin: "5px 0 0", color: "#68788e", fontSize: "11px" }}>
            Deterministic policies evaluated alongside the AI reasoning layer.
          </p>
        </div>
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", justifyContent: "flex-end" }}>
          <span style={statPill}>Evaluated {evaluated}</span>
          <span style={{ ...statPill, color: matched > 0 ? "#dfe8f4" : "#9aa9bb" }}>
            Matched {matched}
          </span>
        </div>
      </div>

      {matchedRules.length === 0 ? (
        <div style={{ padding: "18px", color: "#7f8fa4", fontSize: "12px" }}>
          No configured business rules were triggered for this decision.
        </div>
      ) : (
        <div style={{ display: "grid", gap: "10px", padding: "14px 18px 18px" }}>
          {matchedRules.map((rule) => (
            <div
              key={rule.rule_id}
              style={{
                border: "1px solid #273447",
                borderRadius: "10px",
                background: "#101923",
                padding: "13px 14px",
              }}
            >
              <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "14px" }}>
                <div style={{ minWidth: 0 }}>
                  <strong style={{ display: "block", color: "#e5ebf3", fontSize: "13px" }}>{rule.rule_name}</strong>
                  <span style={{ display: "block", marginTop: "3px", color: "#6f7f94", fontSize: "10px" }}>
                    {rule.rule_id} · Priority {rule.priority} · {rule.severity || "INFO"}
                  </span>
                </div>
                <span
                  style={{
                    flexShrink: 0,
                    padding: "4px 8px",
                    borderRadius: "999px",
                    border: "1px solid #31445a",
                    background: "#152130",
                    color: "#b9c7d8",
                    fontSize: "9px",
                    fontWeight: 800,
                    letterSpacing: "0.06em",
                  }}
                >
                  TRIGGERED
                </span>
              </div>

              {rule.reason && (
                <div style={{ marginTop: "10px", color: "#9aa9bb", fontSize: "11px", lineHeight: 1.5 }}>
                  {rule.reason}
                </div>
              )}

              {(rule.actions || []).length > 0 && (
                <div style={{ marginTop: "10px", display: "flex", flexWrap: "wrap", gap: "7px" }}>
                  {rule.actions.map((action, index) => (
                    <span
                      key={`${rule.rule_id}-action-${index}`}
                      style={{
                        padding: "5px 8px",
                        borderRadius: "7px",
                        border: "1px solid #2b3a4e",
                        background: "#0c131c",
                        color: "#aebccc",
                        fontSize: "10px",
                      }}
                    >
                      {action.action_type || "ACTION"}
                      {action.value !== undefined && action.value !== null && ` · ${String(action.value)}`}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function ResultListCard({ title, items, icon: Icon }) {
  return (
    <div className="result-list-card">
      <div className="result-list-title"><Icon size={16} /><span>{title}</span></div>
      {!items || items.length === 0 ? (
        <div className="result-list-empty">None identified.</div>
      ) : (
        <div className="result-list-items">
          {items.map((item, index) => (
            <div key={index} className="result-list-item"><Circle size={6} /><span>{item}</span></div>
          ))}
        </div>
      )}
    </div>
  );
}

function AgentTrace({ agent }) {
  return (
    <div className="agent-trace">
      <div className="agent-trace-icon"><Brain size={16} /></div>
      <div className="agent-trace-main">
        <div className="agent-trace-top">
          <strong>{formatAgentName(agent.agent_name)}</strong>
          <StatusBadge status={agent.status} />
        </div>
        <div className="agent-trace-meta">
          {agent.recommendation && <span>{agent.recommendation}</span>}
          {agent.score !== null && agent.score !== undefined && (
            <><span>•</span><span>Score {Number(agent.score).toFixed(1)}</span></>
          )}
        </div>
      </div>
    </div>
  );
}

function DecisionHistory({ onOpenInvestigation }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    async function loadHistory() {
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/business-questions?limit=100`);
        if (!response.ok) throw new Error();
        const data = await response.json();
        if (mounted) setItems(data.items || []);
      } catch {
        if (mounted) setItems([]);
      } finally {
        if (mounted) setLoading(false);
      }
    }

    loadHistory();
    return () => { mounted = false; };
  }, []);

  return (
    <div className="history-page">
      <div className="page-heading">
        <div>
          <div className="hero-eyebrow"><History size={14} />DECISION HISTORY</div>
          <h1>Business decisions</h1>
          <p>Review previously processed business questions and open their investigation trails.</p>
        </div>
      </div>

      <div className="history-card">
        {loading ? (
          <div className="empty-state">Loading decision history...</div>
        ) : items.length === 0 ? (
          <div className="empty-state"><History size={22} /><span>No decisions have been processed yet.</span></div>
        ) : (
          <div className="history-list">
            {items.map((item) => (
              <button className="history-row" key={item.request_id} onClick={() => onOpenInvestigation(item.request_id)}>
                <div className="history-row-main">
                  <strong>{item.question}</strong>
                  <div className="history-row-meta">
                    <span>{item.business_area}</span><span>•</span><span>{item.question_type}</span><span>•</span><span>{item.request_id}</span>
                  </div>
                </div>
                <div className="history-row-side">
                  {item.confidence !== null && item.confidence !== undefined && <span>{formatConfidence(item.confidence)}</span>}
                  <StatusBadge status={item.status} />
                  <ChevronRight size={16} />
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function Investigation({ requestId, onBack }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;

    async function loadInvestigation() {
      if (!requestId) {
        if (mounted) setLoading(false);
        return;
      }

      try {
        if (mounted) {
          setLoading(true);
          setError("");
        }

        const response = await fetch(`${API_BASE_URL}/api/v1/business-questions/${requestId}`);
        if (!response.ok) throw new Error("Unable to load investigation.");

        const result = await response.json();
        if (mounted) setData(result);
      } catch (err) {
        if (mounted) setError(err.message || "Unable to load investigation.");
      } finally {
        if (mounted) setLoading(false);
      }
    }

    loadInvestigation();
    return () => { mounted = false; };
  }, [requestId]);

  if (loading) {
    return <div className="empty-state full-page-empty"><Clock3 size={22} />Loading investigation...</div>;
  }

  if (error) {
    return (
      <div className="empty-state full-page-empty">
        <AlertTriangle size={22} />
        <span>{error}</span>
        <button className="text-button" onClick={onBack}>Back to Decisions</button>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="empty-state full-page-empty">
        <FileSearch size={22} />
        <span>Select a decision to investigate.</span>
        <button className="text-button" onClick={onBack}>View Decisions</button>
      </div>
    );
  }

  return (
    <div className="investigation-page">
      <button className="back-button" onClick={onBack}><ArrowLeft size={16} />Back to Decisions</button>

      <div className="investigation-header">
        <div>
          <div className="hero-eyebrow"><FileSearch size={14} />INVESTIGATION</div>
          <h1>{data.question}</h1>
          <div className="result-meta">
            <span>{data.request_id}</span><span>•</span><span>{data.business_area}</span><span>•</span><span>{data.question_type}</span>
          </div>
        </div>
        <StatusBadge status={data.status} />
      </div>

      <div className="investigation-summary">
        <div className="investigation-answer">
          <span className="card-kicker">ANSWER</span>
          <p>{data.answer || "No final answer was stored."}</p>
        </div>
        <div className="investigation-confidence">
          <span className="card-kicker">CONFIDENCE</span>
          <strong>{formatConfidence(data.confidence)}</strong>
        </div>
      </div>

      <InvestigationRulePanel auditEvents={data.audit_events || []} />

      <div className="section-heading">
        <div><span className="card-kicker">EXECUTION</span><h2>Agent Timeline</h2></div>
      </div>

      <div className="investigation-timeline">
        {(data.agents || []).map((agent, index) => (
          <div className="timeline-item" key={agent.id}>
            <div className="timeline-marker">{index + 1}</div>
            <div className="timeline-content">
              <div className="timeline-title">
                <strong>{formatAgentName(agent.agent_name)}</strong>
                <StatusBadge status={agent.status} />
              </div>
              <div className="timeline-meta">
                <span>{agent.recommendation || "No recommendation"}</span>
                {agent.score !== null && agent.score !== undefined && (
                  <><span>•</span><span>Score {Number(agent.score).toFixed(1)}</span></>
                )}
              </div>
              {agent.findings?.length > 0 && (
                <div className="timeline-findings">
                  {agent.findings.slice(0, 4).map((finding, findingIndex) => (
                    <div className="timeline-finding" key={findingIndex}>
                      <strong>{finding.factor}</strong>
                      <span>{String(finding.value)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="section-heading">
        <div><span className="card-kicker">AUDIT</span><h2>Audit Timeline</h2></div>
        <span className="section-count">{data.audit_events?.length || 0} events</span>
      </div>

      <div className="audit-list">
        {(data.audit_events || []).map((event) => (
          <div className="audit-row" key={event.id}>
            <div className="audit-icon"><Clock3 size={15} /></div>
            <div className="audit-main">
              <strong>{event.event_type}</strong>
              <span>{event.agent_name || "System"}</span>
            </div>
            <div className="audit-time">{formatDateTime(event.created_at)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function InvestigationRulePanel({ auditEvents }) {
  const ruleEvents = (auditEvents || []).filter(
    (event) =>
      event.event_type === "BUSINESS_RULE_TRIGGERED" &&
      (!event.details || event.details.phase === "POST_ROUTING")
  );

  const evaluationEvent = (auditEvents || []).find(
    (event) =>
      event.event_type === "BUSINESS_RULES_EVALUATED" &&
      event.details?.phase === "POST_ROUTING"
  );

  const evaluated = Number(evaluationEvent?.details?.total_evaluated || 0);

  return (
    <section
      style={{
        border: "1px solid #1d2836",
        borderRadius: "12px",
        background: "#0d141d",
        overflow: "hidden",
        marginBottom: "22px",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "16px",
          padding: "16px 18px",
          borderBottom: "1px solid #1d2836",
        }}
      >
        <div>
          <span className="card-kicker">POLICY EXECUTION</span>
          <h2 style={{ margin: "5px 0 0", fontSize: "18px" }}>Business Rule Results</h2>
        </div>
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", justifyContent: "flex-end" }}>
          <span
            style={{
              padding: "6px 9px",
              borderRadius: "999px",
              border: "1px solid #263244",
              background: "#121a25",
              color: "#9aa9bb",
              fontSize: "10px",
              fontWeight: 700,
            }}
          >
            Evaluated {evaluated}
          </span>
          <span
            style={{
              padding: "6px 9px",
              borderRadius: "999px",
              border: "1px solid #263244",
              background: "#121a25",
              color: "#9aa9bb",
              fontSize: "10px",
              fontWeight: 700,
            }}
          >
            Triggered {ruleEvents.length}
          </span>
        </div>
      </div>

      {ruleEvents.length === 0 ? (
        <div style={{ padding: "18px", color: "#7f8fa4", fontSize: "12px" }}>
          No business rule was triggered during the final routed evaluation.
        </div>
      ) : (
        <div style={{ display: "grid", gap: "10px", padding: "14px 18px 18px" }}>
          {ruleEvents.map((event) => {
            const details = event.details || {};
            return (
              <div
                key={event.id}
                style={{
                  padding: "13px 14px",
                  borderRadius: "10px",
                  border: "1px solid #273447",
                  background: "#101923",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", gap: "12px", alignItems: "flex-start" }}>
                  <div>
                    <strong style={{ display: "block", color: "#e5ebf3", fontSize: "13px" }}>
                      {details.rule_name || details.rule_id || "Business Rule"}
                    </strong>
                    <span style={{ display: "block", marginTop: "3px", color: "#6f7f94", fontSize: "10px" }}>
                      {details.rule_id || "RULE"} · {details.severity || "INFO"}
                    </span>
                  </div>
                  <span
                    style={{
                      padding: "4px 8px",
                      borderRadius: "999px",
                      border: "1px solid #31445a",
                      background: "#152130",
                      color: "#b9c7d8",
                      fontSize: "9px",
                      fontWeight: 800,
                    }}
                  >
                    TRIGGERED
                  </span>
                </div>
                {details.reason && (
                  <div style={{ marginTop: "9px", color: "#9aa9bb", fontSize: "11px", lineHeight: 1.5 }}>
                    {details.reason}
                  </div>
                )}
                {(details.actions || []).length > 0 && (
                  <div style={{ marginTop: "9px", display: "flex", flexWrap: "wrap", gap: "7px" }}>
                    {details.actions.map((action, index) => (
                      <span
                        key={`${event.id}-action-${index}`}
                        style={{
                          padding: "5px 8px",
                          borderRadius: "7px",
                          border: "1px solid #2b3a4e",
                          background: "#0c131c",
                          color: "#aebccc",
                          fontSize: "10px",
                        }}
                      >
                        {action.action_type || "ACTION"}
                        {action.value !== undefined && action.value !== null && ` · ${String(action.value)}`}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}

function AgentNetwork() {
  const specialistNames = [
    "Finance",
    "Sales",
    "Marketing",
    "Customer",
    "Operations",
    "Product",
    "HR",
    "Procurement",
    "Strategy",
    "Risk",
    "Technology",
    "Compliance",
    "Market",
  ];

  const coreAgents = [
    "question_router_agent",
    "evidence_agent",
    "critic_agent",
    "synthesis_agent",
  ];

  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [refreshing, setRefreshing] = useState(false);

  async function loadAgentData(showRefreshState = false) {
    try {
      if (showRefreshState) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      setError("");

      const response = await fetch(
        `${API_BASE_URL}/api/v1/analytics`
      );

      if (!response.ok) {
        throw new Error("Unable to load agent analytics.");
      }

      const data = await response.json();
      setAnalytics(data);
    } catch (err) {
      setError(
        err.message || "Unable to load agent analytics."
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    loadAgentData(false);
  }, []);

  if (loading) {
    return (
      <div className="empty-state full-page-empty">
        <Network size={22} />
        Loading agent network...
      </div>
    );
  }

  if (error) {
    return (
      <div className="empty-state full-page-empty">
        <AlertTriangle size={22} />
        <span>{error}</span>
        <button
          className="text-button"
          onClick={() => loadAgentData(true)}
        >
          Try again <RefreshCw size={14} />
        </button>
      </div>
    );
  }

  const agentMetrics = analytics?.agents || [];

  const metricMap = new Map(
    agentMetrics.map((agent) => [
      agent.agent_name,
      agent,
    ])
  );

  const getSpecialistMetric = (name) => {
    const key = `${name.toLowerCase()}_agent`;
    return (
      metricMap.get(key) || {
        agent_name: key,
        run_count: 0,
        completed_count: 0,
        failed_count: 0,
        average_score: null,
      }
    );
  };

  const coreMetrics = coreAgents.map(
    (agentName) =>
      metricMap.get(agentName) || {
        agent_name: agentName,
        run_count: 0,
        completed_count: 0,
        failed_count: 0,
        average_score: null,
      }
  );

  const coreRuns = coreMetrics.reduce(
    (total, agent) =>
      total + Number(agent.run_count || 0),
    0
  );

  const coreCompleted = coreMetrics.reduce(
    (total, agent) =>
      total + Number(agent.completed_count || 0),
    0
  );

  return (
    <div className="agent-network-page">
      <div className="page-heading agent-network-heading-row">
        <div>
          <div className="hero-eyebrow">
            <Network size={14} />
            AGENT NETWORK
          </div>

          <h1>Specialist intelligence layer</h1>

          <p>
            Live agent execution metrics from the DecisionOS
            analytics engine. Specialist agents are available
            across business domains and activated according to
            the question being analyzed.
          </p>
        </div>

        <button
          className="secondary-action"
          onClick={() => loadAgentData(true)}
          disabled={refreshing}
        >
          <RefreshCw
            size={16}
            className={
              refreshing ? "analytics-spin" : ""
            }
          />
          {refreshing ? "Refreshing..." : "Refresh network"}
        </button>
      </div>

      <div className="agent-network-summary-grid">
        <div className="network-core-card">
          <div className="network-core">
            <Brain size={28} />
          </div>

          <strong>Gemini Orchestrator</strong>

          <span>
            Routing, evidence, critique and synthesis
          </span>

          <div className="network-core-metrics">
            <div>
              <strong>{coreRuns}</strong>
              <span>core runs</span>
            </div>

            <div>
              <strong>{coreCompleted}</strong>
              <span>completed</span>
            </div>

            <div>
              <strong>4</strong>
              <span>core stages</span>
            </div>
          </div>
        </div>

      </div>

      <div className="agent-network-section-heading">
        <div>
          <span className="card-kicker">
            SPECIALISTS
          </span>
          <h2>Domain intelligence</h2>
        </div>

        <span className="section-count">
          {specialistNames.length} agents
        </span>
      </div>

      <div className="agent-network-grid">
        {specialistNames.map((name) => {
          const metric = getSpecialistMetric(name);
          const hasRuns =
            Number(metric.run_count || 0) > 0;

          return (
            <div
              className={`network-agent-card ${
                hasRuns
                  ? "network-agent-active"
                  : "network-agent-idle"
              }`}
              key={name}
            >
              <div className="network-agent-top">
                <div className="network-agent-icon">
                  <Network size={16} />
                </div>

                <span
                  className={`network-agent-status-dot ${
                    hasRuns
                      ? "network-dot-active"
                      : "network-dot-idle"
                  }`}
                />
              </div>

              <strong>{name}</strong>

              <span>Specialist Agent</span>

              <div className="network-agent-stats network-agent-stats-compact">
                <div>
                  <span>Runs</span>
                  <strong>
                    {metric.run_count ?? 0}
                  </strong>
                </div>

                <div>
                  <span>Completed</span>
                  <strong>
                    {metric.completed_count ?? 0}
                  </strong>
                </div>
              </div>

              <div
                className={`agent-online ${
                  hasRuns
                    ? "agent-online-active"
                    : "agent-online-idle"
                }`}
              >
                <span />
                {hasRuns ? "Executed" : "Available"}
              </div>
            </div>
          );
        })}
      </div>

      <div className="agent-network-section-heading">
        <div>
          <span className="card-kicker">
            CORE EXECUTION
          </span>
          <h2>Orchestrator stages</h2>
        </div>

        <span className="section-count">
          {coreMetrics.length} stages
        </span>
      </div>

      <div className="agent-core-table-card">
        <div className="agent-core-table">
          <div className="agent-core-row agent-core-header">
            <span>Stage</span>
            <span>Runs</span>
            <span>Completed</span>
            <span>Failed</span>
            <span>Score</span>
          </div>

          {coreMetrics.map((agent) => (
            <div
              className="agent-core-row"
              key={agent.agent_name}
            >
              <div className="agent-core-name">
                <div className="analytics-agent-icon">
                  <Brain size={13} />
                </div>
                <strong>
                  {formatAgentName(agent.agent_name)}
                </strong>
              </div>

              <span>{agent.run_count ?? 0}</span>
              <span>{agent.completed_count ?? 0}</span>
              <span>{agent.failed_count ?? 0}</span>
              <span>
                {agent.average_score != null
                  ? Number(
                      agent.average_score
                    ).toFixed(1)
                  : "—"}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}



const QUESTION_TYPES = [
  "INVESTIGATE",
  "ANALYZE",
  "DECIDE",
  "RECOMMEND",
  "COMPARE",
  "PREDICT",
  "EXPLAIN",
  "OPTIMIZE",
];

const BUSINESS_AREAS = [
  "GENERAL",
  "OPERATIONS",
  "SALES",
  "FINANCE",
  "PROCUREMENT",
  "CUSTOMER",
  "RISK",
  "TECHNOLOGY",
  "HR",
  "MARKETING",
];

function normalizeRuleValue(value) {
  if (typeof value !== "string") {
    return value;
  }

  const trimmed = value.trim();

  if (!trimmed) {
    return "";
  }

  if (trimmed === "true") {
    return true;
  }

  if (trimmed === "false") {
    return false;
  }

  if (/^-?\d+(\.\d+)?$/.test(trimmed)) {
    return Number(trimmed);
  }

  return trimmed;
}

function BusinessRules() {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [areaFilter, setAreaFilter] = useState("ALL");
  const [severityFilter, setSeverityFilter] = useState("ALL");
  const [enabledFilter, setEnabledFilter] = useState("ALL");

  const [showForm, setShowForm] = useState(false);
  const [editingRuleId, setEditingRuleId] = useState(null);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");

  const emptyForm = {
    name: "",
    description: "",
    business_area: "GENERAL",
    question_types: ["INVESTIGATE"],
    priority: 100,
    severity: "INFO",
    conditions: [
      { field: "", customField: "", operator: ">", value: "" },
    ],
    actions: [
      { action_type: "FLAG", value: "", message: "" },
    ],
    enabled: true,
  };

  const [form, setForm] = useState(emptyForm);

  async function loadRules(showRefreshState = false) {
    try {
      if (showRefreshState) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      setError("");

      const response = await fetch(
        `${API_BASE_URL}/api/v1/rules?limit=100`
      );

      if (!response.ok) {
        throw new Error("Unable to load business rules.");
      }

      const data = await response.json();

      setRules(data.items || []);
    } catch (err) {
      setError(
        err.message || "Unable to load business rules."
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    loadRules(false);
  }, []);

  function openCreateForm() {
    setEditingRuleId(null);
    setForm(emptyForm);
    setFormError("");
    setShowForm(true);
  }

  function openEditForm(rule) {
    setEditingRuleId(rule.rule_id);

    setForm({
      name: rule.name || "",
      description: rule.description || "",
      business_area: rule.business_area || "GENERAL",
      question_types: Array.isArray(rule.question_types)
        ? rule.question_types
        : [],
      priority: rule.priority ?? 100,
      severity: rule.severity || "INFO",
      conditions: Array.isArray(rule.conditions) && rule.conditions.length
        ? rule.conditions.map((condition) => {
            const knownField = [
              "delay_rate",
              "revenue",
              "cost",
              "profit_margin",
              "order_value",
              "delivery_time",
              "customer_risk_score",
              "supplier_risk_score",
              "inventory_level",
              "error_rate",
              "incident_count",
            ].includes(condition?.field);

            return {
              field: knownField ? condition.field : "custom",
              customField: knownField ? "" : condition?.field || "",
              operator: condition?.operator || ">",
              value: condition?.value ?? "",
            };
          })
        : [{ field: "", customField: "", operator: ">", value: "" }],
      actions: Array.isArray(rule.actions) && rule.actions.length
        ? rule.actions.map((action) => ({
            action_type: action?.action_type || "FLAG",
            value: action?.value ?? "",
            message: action?.message || "",
          }))
        : [{ action_type: "FLAG", value: "", message: "" }],
      enabled: Boolean(rule.enabled),
    });

    setFormError("");
    setShowForm(true);
  }

  function closeForm() {
    setShowForm(false);
    setEditingRuleId(null);
    setFormError("");
  }

  function updateForm(field, value) {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  }

  async function saveRule(event) {
    event.preventDefault();

    try {
      setSaving(true);
      setFormError("");

      const conditions = form.conditions
        .map((condition) => ({
          ...condition,
          field: condition.field === "custom"
            ? String(condition.customField || "").trim()
            : String(condition.field || "").trim(),
        }))
        .filter((condition) => condition.field)
        .map((condition) => ({
          field: condition.field,
          operator: condition.operator || ">",
          value: normalizeRuleValue(condition.value),
        }));

      const actions = form.actions
        .filter((action) => action.action_type)
        .map((action) => ({
          action_type: action.action_type,
          value: normalizeRuleValue(action.value),
          ...(String(action.message || "").trim()
            ? { message: String(action.message).trim() }
            : {}),
        }));

      if (!conditions.length) {
        throw new Error("Add at least one valid condition.");
      }

      if (!actions.length) {
        throw new Error("Add at least one action.");
      }

      const payload = {
        name: form.name.trim(),
        description: form.description.trim(),
        business_area:
          form.business_area.trim().toUpperCase() ||
          "GENERAL",
        question_types: form.question_types
          .map((item) => String(item).trim().toUpperCase())
          .filter(Boolean),
        priority: Number(form.priority) || 100,
        severity:
          form.severity.trim().toUpperCase() ||
          "INFO",
        conditions,
        actions,
        enabled: Boolean(form.enabled),
      };

      if (!payload.name || !payload.description) {
        throw new Error(
          "Rule name and description are required."
        );
      }

      const isEditing = Boolean(editingRuleId);

      const response = await fetch(
        isEditing
          ? `${API_BASE_URL}/api/v1/rules/${editingRuleId}`
          : `${API_BASE_URL}/api/v1/rules`,
        {
          method: isEditing ? "PUT" : "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        }
      );

      if (!response.ok) {
        let message =
          "Unable to save business rule.";

        try {
          const errorData = await response.json();

          if (typeof errorData?.detail === "string") {
            message = errorData.detail;
          }
        } catch {
          // Keep generic error message.
        }

        throw new Error(message);
      }

      await loadRules(true);
      setSaving(false);
      closeForm();
      return;
    } catch (err) {
      setFormError(
        err.message || "Unable to save business rule."
      );
      setSaving(false);
      return;
    }

    setSaving(false);
  }

  async function toggleRule(rule) {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/rules/${rule.rule_id}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            enabled: !rule.enabled,
          }),
        }
      );

      if (!response.ok) {
        throw new Error(
          "Unable to update rule status."
        );
      }

      await loadRules(true);
    } catch (err) {
      setError(
        err.message || "Unable to update rule status."
      );
    }
  }

  async function deleteRule(rule) {
    const confirmed = window.confirm(
      `Delete "${rule.name}"? This action cannot be undone.`
    );

    if (!confirmed) {
      return;
    }

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/rules/${rule.rule_id}`,
        {
          method: "DELETE",
        }
      );

      if (!response.ok) {
        throw new Error(
          "Unable to delete business rule."
        );
      }

      await loadRules(true);
    } catch (err) {
      setError(
        err.message || "Unable to delete business rule."
      );
    }
  }

  const areas = [
    "ALL",
    ...Array.from(
      new Set(
        rules
          .map((rule) => rule.business_area)
          .filter(Boolean)
      )
    ),
  ];

  const severities = [
    "ALL",
    ...Array.from(
      new Set(
        rules
          .map((rule) => rule.severity)
          .filter(Boolean)
      )
    ),
  ];

  const normalizedSearch = search
    .trim()
    .toLowerCase();

  const filteredRules = rules.filter((rule) => {
    if (
      areaFilter !== "ALL" &&
      rule.business_area !== areaFilter
    ) {
      return false;
    }

    if (
      severityFilter !== "ALL" &&
      rule.severity !== severityFilter
    ) {
      return false;
    }

    if (enabledFilter === "ENABLED" && !rule.enabled) {
      return false;
    }

    if (
      enabledFilter === "DISABLED" &&
      rule.enabled
    ) {
      return false;
    }

    if (normalizedSearch) {
      const haystack = [
        rule.rule_id,
        rule.name,
        rule.description,
        rule.business_area,
        ...(rule.question_types || []),
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      if (!haystack.includes(normalizedSearch)) {
        return false;
      }
    }

    return true;
  });

  const enabledCount = rules.filter(
    (rule) => rule.enabled
  ).length;

  const disabledCount =
    rules.length - enabledCount;

  if (loading) {
    return (
      <div className="empty-state full-page-empty">
        <GitBranch size={22} />
        Loading business rules...
      </div>
    );
  }

  return (
    <>
      <style>{`
        .page-container:has(.business-rules-page) {
          max-width: none !important;
          width: 100% !important;
          margin: 0 !important;
          box-sizing: border-box;
        }

        .business-rules-page {
          width: 100%;
          max-width: none;
          margin: 0;
          box-sizing: border-box;
        }

        .business-rules-page .rules-catalog,
        .business-rules-page .rules-toolbar {
          width: 100%;
        }
      `}</style>

      <div className="business-rules-page">
      <div
        className="page-heading"
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-end",
          gap: "24px",
          flexWrap: "wrap",
        }}
      >
        <div>
          <div className="hero-eyebrow">
            <GitBranch size={14} />
            BUSINESS RULES
          </div>

          <h1>Decision policy management</h1>

          <p>
            Configure reusable business policies,
            constraints and actions that can guide
            decisions across different business
            domains.
          </p>
        </div>

        <div
          style={{
            display: "flex",
            gap: "10px",
            alignItems: "center",
          }}
        >
          <button
            className="secondary-action"
            onClick={() => loadRules(true)}
            disabled={refreshing}
          >
            <RefreshCw
              size={15}
              className={
                refreshing
                  ? "analytics-spin"
                  : ""
              }
            />
            {refreshing
              ? "Refreshing..."
              : "Refresh"}
          </button>

          <button
            className="primary-action"
            onClick={openCreateForm}
            style={{
              marginTop: 0,
              height: "40px",
            }}
          >
            <Plus size={16} />
            Create Rule
          </button>
        </div>
      </div>

      {error && (
        <div
          style={{
            marginBottom: "16px",
            padding: "12px 14px",
            border: "1px solid #4b2a32",
            borderRadius: "10px",
            background: "#1c1116",
            color: "#df9aa6",
            fontSize: "11px",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <AlertTriangle size={14} />
          <span>{error}</span>
        </div>
      )}

      <section
        style={{
          display: "grid",
          gridTemplateColumns:
            "repeat(3, minmax(0, 1fr))",
          gap: "12px",
          marginBottom: "18px",
        }}
      >
        <RuleSummaryCard
          label="Total Rules"
          value={rules.length}
          caption="Configured policies"
          icon={GitBranch}
        />

        <RuleSummaryCard
          label="Enabled"
          value={enabledCount}
          caption="Currently active"
          icon={CheckCircle2}
        />

        <RuleSummaryCard
          label="Disabled"
          value={disabledCount}
          caption="Currently inactive"
          icon={Circle}
        />
      </section>

      <section
        className="rules-toolbar"
        style={{
          border: "1px solid #1c2735",
          borderRadius: "12px",
          background: "#0d141d",
          padding: "12px",
          marginBottom: "16px",
          display: "grid",
          gridTemplateColumns:
            "minmax(240px, 1fr) repeat(3, minmax(150px, 190px))",
          gap: "10px",
        }}
      >
        <div
          style={{
            minHeight: "38px",
            display: "flex",
            alignItems: "center",
            gap: "8px",
            padding: "0 11px",
            border: "1px solid #202b3a",
            borderRadius: "8px",
            background: "#0b1119",
            color: "#718197",
          }}
        >
          <Search size={14} />

          <input
            value={search}
            onChange={(event) =>
              setSearch(event.target.value)
            }
            placeholder="Search rules..."
            style={{
              width: "100%",
              minWidth: 0,
              border: 0,
              outline: 0,
              background: "transparent",
              color: "#dce4ee",
              fontSize: "11px",
            }}
          />
        </div>

        <RuleFilter
          value={areaFilter}
          onChange={setAreaFilter}
          options={areas}
          placeholder="Business area"
        />

        <RuleFilter
          value={severityFilter}
          onChange={setSeverityFilter}
          options={severities}
          placeholder="Severity"
        />

        <RuleFilter
          value={enabledFilter}
          onChange={setEnabledFilter}
          options={[
            "ALL",
            "ENABLED",
            "DISABLED",
          ]}
          placeholder="Status"
        />
      </section>

      <section
        style={{
          border: "1px solid #1c2735",
          borderRadius: "13px",
          background: "#0d141d",
          overflow: "hidden",
        }}
      >
        <div
          className="card-header"
          style={{
            paddingBottom: "14px",
          }}
        >
          <div>
            <span className="card-kicker">
              POLICY CATALOG
            </span>

            <h2>
              {filteredRules.length} rules shown
            </h2>
          </div>

          <span className="section-count">
            Priority ordered
          </span>
        </div>

        {filteredRules.length === 0 ? (
          <div className="empty-state">
            <GitBranch size={22} />

            <span>
              No rules match the current filters.
            </span>

            <button
              className="text-button"
              onClick={openCreateForm}
            >
              Create the first rule
              <ChevronRight size={14} />
            </button>
          </div>
        ) : (
          <div
            style={{
              display: "grid",
              gap: "0",
            }}
          >
            {filteredRules.map((rule) => (
              <BusinessRuleRow
                key={rule.rule_id}
                rule={rule}
                onEdit={openEditForm}
                onToggle={toggleRule}
                onDelete={deleteRule}
              />
            ))}
          </div>
        )}
      </section>

      {showForm && (
        <BusinessRuleModal
          form={form}
          setForm={setForm}
          updateForm={updateForm}
          editingRuleId={editingRuleId}
          saving={saving}
          formError={formError}
          onSubmit={saveRule}
          onClose={closeForm}
        />
      )}
      </div>
    </>
  );
}


function RuleSummaryCard({
  label,
  value,
  caption,
  icon: Icon,
}) {
  return (
    <div
      className="metric-card"
      style={{
        minHeight: "100px",
      }}
    >
      <div className="metric-icon">
        <Icon size={17} />
      </div>

      <div>
        <span className="metric-label">
          {label}
        </span>

        <div className="metric-value">
          {value}
        </div>

        <span className="metric-caption">
          {caption}
        </span>
      </div>
    </div>
  );
}


function RuleFilter({
  value,
  onChange,
  options,
}) {
  return (
    <select
      value={value}
      onChange={(event) =>
        onChange(event.target.value)
      }
      style={{
        width: "100%",
        height: "38px",
        padding: "0 10px",
        border: "1px solid #202b3a",
        borderRadius: "8px",
        background: "#0b1119",
        color: "#aebaca",
        outline: 0,
        fontSize: "10px",
      }}
    >
      {options.map((option) => (
        <option
          value={option}
          key={option}
        >
          {option === "ALL"
            ? "All"
            : option}
        </option>
      ))}
    </select>
  );
}


function BusinessRuleRow({
  rule,
  onEdit,
  onToggle,
  onDelete,
}) {
  const severity = String(
    rule.severity || "INFO"
  ).toUpperCase();

  const severityStyles = {
    INFO: {
      border: "#2c394a",
      background: "#121a24",
      color: "#98a7ba",
    },
    WARNING: {
      border: "#4e4325",
      background: "#201b0f",
      color: "#d5bc72",
    },
    HIGH: {
      border: "#51332f",
      background: "#211513",
      color: "#d59a8e",
    },
    CRITICAL: {
      border: "#5a2e39",
      background: "#241217",
      color: "#df94a4",
    },
  };

  const badge =
    severityStyles[severity] ||
    severityStyles.INFO;

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns:
          "minmax(0, 1fr) 120px 105px 170px",
        gap: "18px",
        alignItems: "center",
        padding: "17px 18px",
        borderBottom:
          "1px solid #17212d",
      }}
    >
      <div
        style={{
          minWidth: 0,
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            marginBottom: "5px",
          }}
        >
          <strong
            style={{
              color: "#cfd8e4",
              fontSize: "12px",
            }}
          >
            {rule.name}
          </strong>

          <span
            style={{
              padding: "3px 7px",
              border:
                `1px solid ${badge.border}`,
              borderRadius: "999px",
              background:
                badge.background,
              color: badge.color,
              fontSize: "8px",
              fontWeight: 700,
              letterSpacing: "0.06em",
            }}
          >
            {severity}
          </span>
        </div>

        <div
          style={{
            color: "#69798f",
            fontSize: "9px",
            lineHeight: 1.55,
            marginBottom: "7px",
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {rule.description}
        </div>

        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "6px",
            color: "#5e6d81",
            fontSize: "8px",
            textTransform: "uppercase",
          }}
        >
          <span>{rule.rule_id}</span>
          <span>•</span>
          <span>{rule.business_area}</span>

          {rule.question_types?.length > 0 && (
            <>
              <span>•</span>
              <span>
                {rule.question_types.join(", ")}
              </span>
            </>
          )}
        </div>
      </div>

      <div
        style={{
          textAlign: "center",
        }}
      >
        <span
          style={{
            display: "block",
            color: "#64748a",
            fontSize: "8px",
            textTransform: "uppercase",
            letterSpacing: "0.08em",
            marginBottom: "4px",
          }}
        >
          Priority
        </span>

        <strong
          style={{
            color: "#cbd5e1",
            fontSize: "13px",
          }}
        >
          {rule.priority}
        </strong>
      </div>

      <div>
        <button
          type="button"
          onClick={() => onToggle(rule)}
          style={{
            width: "100%",
            height: "30px",
            border:
              `1px solid ${
                rule.enabled
                  ? "#244536"
                  : "#2a3545"
              }`,
            borderRadius: "8px",
            background:
              rule.enabled
                ? "#102019"
                : "#111923",
            color:
              rule.enabled
                ? "#6fca9b"
                : "#8795a8",
            fontSize: "9px",
            fontWeight: 700,
            cursor: "pointer",
          }}
        >
          {rule.enabled
            ? "ENABLED"
            : "DISABLED"}
        </button>
      </div>

      <div
        style={{
          display: "flex",
          justifyContent: "flex-end",
          gap: "7px",
        }}
      >
        <button
          type="button"
          className="secondary-action"
          onClick={() => onEdit(rule)}
          style={{
            height: "31px",
            padding: "0 11px",
            fontSize: "9px",
          }}
        >
          Edit
        </button>

        <button
          type="button"
          onClick={() => onDelete(rule)}
          style={{
            height: "31px",
            padding: "0 11px",
            border:
              "1px solid #4b2b35",
            borderRadius: "8px",
            background: "#1a1116",
            color: "#c98d9a",
            fontSize: "9px",
            fontWeight: 700,
            cursor: "pointer",
          }}
        >
          Delete
        </button>
      </div>
    </div>
  );
}


function BusinessRuleModal({
  form,
  updateForm,
  editingRuleId,
  saving,
  formError,
  onSubmit,
  onClose,
}) {
  const inputStyle = {
    width: "100%",
    height: "40px",
    padding: "0 11px",
    border: "1px solid #263244",
    borderRadius: "8px",
    background: "#0b1119",
    color: "#d7e0eb",
    outline: 0,
    fontSize: "11px",
  };

  const textareaStyle = {
    width: "100%",
    minHeight: "90px",
    padding: "10px 11px",
    border: "1px solid #263244",
    borderRadius: "8px",
    background: "#0b1119",
    color: "#d7e0eb",
    outline: 0,
    resize: "vertical",
    fontSize: "10px",
    lineHeight: 1.5,
  };

  const selectStyle = {
    ...inputStyle,
    cursor: "pointer",
  };

  const conditionFields = [
    "delay_rate",
    "revenue",
    "cost",
    "profit_margin",
    "order_value",
    "delivery_time",
    "customer_risk_score",
    "supplier_risk_score",
    "inventory_level",
    "error_rate",
    "incident_count",
    "custom",
  ];

  const operators = [
    { value: ">", label: "Greater than (>)" },
    { value: ">=", label: "Greater than or equal (>=)" },
    { value: "<", label: "Less than (<)" },
    { value: "<=", label: "Less than or equal (<=)" },
    { value: "==", label: "Equals (=)" },
    { value: "!=", label: "Not equal (!=)" },
    { value: "CONTAINS", label: "Contains" },
    { value: "IN", label: "Is one of" },
  ];

  const actionTypes = [
    { value: "FLAG", label: "Flag decision" },
    { value: "REQUIRE_REVIEW", label: "Require human review" },
    { value: "ESCALATE", label: "Escalate" },
    { value: "NOTIFY", label: "Send notification" },
    { value: "BLOCK", label: "Block / stop decision" },
    { value: "SET_PRIORITY", label: "Set priority" },
    { value: "ROUTE_TO_AGENT", label: "Route to specialist" },
  ];

  function updateCondition(index, field, value) {
    const next = form.conditions.map((condition, currentIndex) =>
      currentIndex === index
        ? { ...condition, [field]: value }
        : condition
    );
    updateForm("conditions", next);
  }

  function addCondition() {
    updateForm("conditions", [
      ...form.conditions,
      { field: "", customField: "", operator: ">", value: "" },
    ]);
  }

  function removeCondition(index) {
    if (form.conditions.length === 1) {
      updateForm("conditions", [
        { field: "", customField: "", operator: ">", value: "" },
      ]);
      return;
    }
    updateForm(
      "conditions",
      form.conditions.filter((_, currentIndex) => currentIndex !== index)
    );
  }

  function updateAction(index, field, value) {
    const next = form.actions.map((action, currentIndex) =>
      currentIndex === index
        ? { ...action, [field]: value }
        : action
    );
    updateForm("actions", next);
  }

  function addAction() {
    updateForm("actions", [
      ...form.actions,
      { action_type: "FLAG", value: "", message: "" },
    ]);
  }

  function removeAction(index) {
    if (form.actions.length === 1) {
      updateForm("actions", [
        { action_type: "FLAG", value: "", message: "" },
      ]);
      return;
    }
    updateForm(
      "actions",
      form.actions.filter((_, currentIndex) => currentIndex !== index)
    );
  }

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 100,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "24px",
        background: "rgba(0, 0, 0, 0.66)",
        backdropFilter: "blur(6px)",
      }}
    >
      <div
        style={{
          width: "min(860px, 100%)",
          maxHeight: "calc(100vh - 48px)",
          overflow: "auto",
          border: "1px solid #263243",
          borderRadius: "15px",
          background: "#0c131d",
          boxShadow: "0 24px 80px rgba(0,0,0,0.45)",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "16px",
            padding: "18px 20px",
            borderBottom: "1px solid #1b2633",
            position: "sticky",
            top: 0,
            zIndex: 2,
            background: "#0c131d",
          }}
        >
          <div>
            <span className="card-kicker">
              {editingRuleId ? "EDIT RULE" : "NEW RULE"}
            </span>
            <h2
              style={{
                margin: 0,
                color: "#e0e7f0",
                fontSize: "17px",
              }}
            >
              {editingRuleId
                ? "Update business rule"
                : "Create business rule"}
            </h2>
          </div>

          <button
            type="button"
            onClick={onClose}
            disabled={saving}
            style={{
              width: "32px",
              height: "32px",
              border: "1px solid #293547",
              borderRadius: "8px",
              background: "#111923",
              color: "#9aa7b8",
              cursor: "pointer",
            }}
          >
            ×
          </button>
        </div>

        <form onSubmit={onSubmit} style={{ padding: "20px" }}>
          {formError && (
            <div
              style={{
                marginBottom: "14px",
                padding: "10px 12px",
                border: "1px solid #4b2a32",
                borderRadius: "8px",
                background: "#1b1116",
                color: "#dc9aa6",
                fontSize: "10px",
              }}
            >
              {formError}
            </div>
          )}

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "minmax(0, 1fr) minmax(220px, 280px)",
              gap: "14px",
            }}
          >
            <RuleField label="Rule Name">
              <input
                value={form.name}
                onChange={(event) => updateForm("name", event.target.value)}
                placeholder="e.g. High delay escalation"
                style={inputStyle}
                required
              />
            </RuleField>

            <RuleField label="Business Area">
              <select
                value={form.business_area}
                onChange={(event) => updateForm("business_area", event.target.value)}
                style={selectStyle}
              >
                {BUSINESS_AREAS.map((area) => (
                  <option key={area} value={area}>
                    {area}
                  </option>
                ))}
              </select>
            </RuleField>

            <RuleField label="Description" full>
              <textarea
                value={form.description}
                onChange={(event) => updateForm("description", event.target.value)}
                placeholder="Describe when this policy should apply and why."
                style={{ ...textareaStyle, minHeight: "78px", fontFamily: "inherit" }}
                required
              />
            </RuleField>

            <RuleField label="Question Types" full>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
                  gap: "8px",
                  padding: "10px",
                  border: "1px solid #263244",
                  borderRadius: "8px",
                  background: "#0b1119",
                }}
              >
                {QUESTION_TYPES.map((type) => {
                  const checked = form.question_types.includes(type);
                  return (
                    <label
                      key={type}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "7px",
                        minHeight: "30px",
                        padding: "0 7px",
                        border: checked ? "1px solid #356da8" : "1px solid #1d2937",
                        borderRadius: "6px",
                        background: checked ? "#102238" : "#0e151f",
                        color: checked ? "#d9e7f8" : "#8e9bad",
                        fontSize: "9px",
                        cursor: "pointer",
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={(event) => {
                          const next = event.target.checked
                            ? [...form.question_types, type]
                            : form.question_types.filter((item) => item !== type);
                          updateForm("question_types", next);
                        }}
                      />
                      {type}
                    </label>
                  );
                })}
              </div>
              <span
                style={{
                  marginTop: "5px",
                  display: "block",
                  color: "#5f6f84",
                  fontSize: "8px",
                }}
              >
                Select one or more question types.
              </span>
            </RuleField>

            <RuleField label="Priority">
              <input
                type="number"
                min="1"
                value={form.priority}
                onChange={(event) => updateForm("priority", event.target.value)}
                style={inputStyle}
              />
            </RuleField>

            <RuleField label="Severity">
              <select
                value={form.severity}
                onChange={(event) => updateForm("severity", event.target.value)}
                style={selectStyle}
              >
                <option value="INFO">INFO</option>
                <option value="WARNING">WARNING</option>
                <option value="HIGH">HIGH</option>
                <option value="CRITICAL">CRITICAL</option>
              </select>
            </RuleField>

            <RuleField label="Status">
              <label
                style={{
                  minHeight: "40px",
                  display: "flex",
                  alignItems: "center",
                  gap: "9px",
                  color: "#abb7c7",
                  fontSize: "10px",
                }}
              >
                <input
                  type="checkbox"
                  checked={form.enabled}
                  onChange={(event) => updateForm("enabled", event.target.checked)}
                />
                Rule enabled
              </label>
            </RuleField>

            <RuleField label="Conditions" full>
              <div
                style={{
                  display: "grid",
                  gap: "9px",
                }}
              >
                {form.conditions.map((condition, index) => (
                  <div
                    key={`condition-${index}`}
                    style={{
                      display: "grid",
                      gridTemplateColumns: "minmax(170px, 1.1fr) minmax(210px, 1fr) minmax(120px, 0.8fr) 34px",
                      gap: "8px",
                      alignItems: "center",
                      padding: "10px",
                      border: "1px solid #1f2c3b",
                      borderRadius: "8px",
                      background: "#0b1119",
                    }}
                  >
                    <select
                      value={condition.field || ""}
                      onChange={(event) => updateCondition(index, "field", event.target.value)}
                      style={selectStyle}
                    >
                      <option value="">Select field</option>
                      {conditionFields.map((field) => (
                        <option key={field} value={field}>
                          {field === "custom" ? "Custom field..." : field}
                        </option>
                      ))}
                    </select>

                    <select
                      value={condition.operator || ">"}
                      onChange={(event) => updateCondition(index, "operator", event.target.value)}
                      style={selectStyle}
                    >
                      {operators.map((operator) => (
                        <option key={operator.value} value={operator.value}>
                          {operator.label}
                        </option>
                      ))}
                    </select>

                    <input
                      value={condition.value ?? ""}
                      onChange={(event) => updateCondition(index, "value", event.target.value)}
                      placeholder="Value"
                      style={inputStyle}
                    />

                    <button
                      type="button"
                      onClick={() => removeCondition(index)}
                      title="Remove condition"
                      style={{
                        width: "34px",
                        height: "34px",
                        border: "1px solid #2a3748",
                        borderRadius: "7px",
                        background: "#121a24",
                        color: "#a4afbd",
                        cursor: "pointer",
                      }}
                    >
                      ×
                    </button>

                    {condition.field === "custom" && (
                      <input
                        value={condition.customField || ""}
                        onChange={(event) => updateCondition(index, "customField", event.target.value)}
                        placeholder="Type custom field name"
                        style={{
                          ...inputStyle,
                          gridColumn: "1 / -1",
                        }}
                      />
                    )}
                  </div>
                ))}
              </div>

              <button
                type="button"
                onClick={addCondition}
                className="secondary-action"
                style={{ marginTop: "9px", height: "34px" }}
              >
                <Plus size={13} />
                Add Condition
              </button>

              <span
                style={{
                  display: "block",
                  marginTop: "5px",
                  color: "#5f6f84",
                  fontSize: "8px",
                }}
              >
                The rule triggers when all configured conditions match.
              </span>
            </RuleField>

            <RuleField label="Actions" full>
              <div style={{ display: "grid", gap: "9px" }}>
                {form.actions.map((action, index) => (
                  <div
                    key={`action-${index}`}
                    style={{
                      display: "grid",
                      gridTemplateColumns: "minmax(190px, 1fr) minmax(130px, 0.7fr) minmax(220px, 1.4fr) 34px",
                      gap: "8px",
                      alignItems: "center",
                      padding: "10px",
                      border: "1px solid #1f2c3b",
                      borderRadius: "8px",
                      background: "#0b1119",
                    }}
                  >
                    <select
                      value={action.action_type || "FLAG"}
                      onChange={(event) => updateAction(index, "action_type", event.target.value)}
                      style={selectStyle}
                    >
                      {actionTypes.map((type) => (
                        <option key={type.value} value={type.value}>
                          {type.label}
                        </option>
                      ))}
                    </select>

                    <input
                      value={action.value ?? ""}
                      onChange={(event) => updateAction(index, "value", event.target.value)}
                      placeholder="Value / code"
                      style={inputStyle}
                    />

                    <input
                      value={action.message || ""}
                      onChange={(event) => updateAction(index, "message", event.target.value)}
                      placeholder="Optional user-facing message"
                      style={inputStyle}
                    />

                    <button
                      type="button"
                      onClick={() => removeAction(index)}
                      title="Remove action"
                      style={{
                        width: "34px",
                        height: "34px",
                        border: "1px solid #2a3748",
                        borderRadius: "7px",
                        background: "#121a24",
                        color: "#a4afbd",
                        cursor: "pointer",
                      }}
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>

              <button
                type="button"
                onClick={addAction}
                className="secondary-action"
                style={{ marginTop: "9px", height: "34px" }}
              >
                <Plus size={13} />
                Add Action
              </button>

              <span
                style={{
                  display: "block",
                  marginTop: "5px",
                  color: "#5f6f84",
                  fontSize: "8px",
                }}
              >
                You do not need to write JSON. The engine will store the rule in structured format automatically.
              </span>
            </RuleField>
          </div>

          <div
            style={{
              display: "flex",
              justifyContent: "flex-end",
              gap: "9px",
              marginTop: "20px",
              paddingTop: "15px",
              borderTop: "1px solid #1b2633",
            }}
          >
            <button
              type="button"
              className="secondary-action"
              onClick={onClose}
              disabled={saving}
            >
              Cancel
            </button>

            <button
              type="submit"
              className="primary-action"
              disabled={saving}
              style={{ marginTop: 0, height: "40px" }}
            >
              {saving
                ? "Saving..."
                : editingRuleId
                  ? "Save Changes"
                  : "Create Rule"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}


function RuleField({
  label,
  children,
  full = false,
}) {
  return (
    <div
      style={{
        gridColumn: full ? "1 / -1" : undefined,
      }}
    >
      <label
        style={{
          display: "block",
          marginBottom: "6px",
          color: "#7d8da2",
          fontSize: "9px",
          fontWeight: 700,
          letterSpacing: "0.08em",
          textTransform: "uppercase",
        }}
      >
        {label}
      </label>
      {children}
    </div>
  );
}


function AuditTrail() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [eventFilter, setEventFilter] = useState("ALL");
  const [agentFilter, setAgentFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [search, setSearch] = useState("");

  async function loadAudit(showRefreshState = false) {
    try {
      if (showRefreshState) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      setError("");

      const response = await fetch(
        `${API_BASE_URL}/api/v1/audit-trail?limit=200`
      );

      if (!response.ok) {
        throw new Error("Unable to load audit trail.");
      }

      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err.message || "Unable to load audit trail.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    loadAudit(false);
  }, []);

  if (loading) {
    return (
      <div className="empty-state full-page-empty">
        <ShieldCheck size={22} />
        Loading audit trail...
      </div>
    );
  }

  if (error) {
    return (
      <div className="empty-state full-page-empty">
        <AlertTriangle size={22} />
        <span>{error}</span>
        <button
          className="text-button"
          onClick={() => loadAudit(true)}
        >
          Try again <RefreshCw size={14} />
        </button>
      </div>
    );
  }

  const events = data?.events || [];

  const eventTypes = [
    "ALL",
    ...Array.from(
      new Set(
        events
          .map((event) => event.event_type)
          .filter(Boolean)
      )
    ),
  ];

  const agentNames = [
    "ALL",
    ...Array.from(
      new Set(
        events
          .map((event) => event.agent_name)
          .filter(Boolean)
      )
    ),
  ];

  const statuses = [
    "ALL",
    ...Array.from(
      new Set(
        events
          .map((event) => event.status)
          .filter(Boolean)
      )
    ),
  ];

  const normalizedSearch = search.trim().toLowerCase();

  const filteredEvents = events.filter((event) => {
    if (
      eventFilter !== "ALL" &&
      event.event_type !== eventFilter
    ) {
      return false;
    }

    if (
      agentFilter !== "ALL" &&
      event.agent_name !== agentFilter
    ) {
      return false;
    }

    if (
      statusFilter !== "ALL" &&
      event.status !== statusFilter
    ) {
      return false;
    }

    if (normalizedSearch) {
      const haystack = [
        event.request_id,
        event.question,
        event.business_area,
        event.question_type,
        event.event_type,
        event.agent_name,
        event.status,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      if (!haystack.includes(normalizedSearch)) {
        return false;
      }
    }

    return true;
  });

  const completedEvents = events.filter(
    (event) =>
      String(event.status || "").toUpperCase() ===
      "COMPLETED"
  ).length;

  const uniqueRequests = new Set(
    events
      .map((event) => event.request_id)
      .filter(Boolean)
  ).size;

  const latestEvent = events[0];

  return (
    <div className="audit-page-v2">
      <div className="audit-heading-v2">
        <div>
          <div className="hero-eyebrow">
            <ShieldCheck size={14} />
            AUDIT TRAIL
          </div>

          <h1>Decision activity history</h1>

          <p>
            Review every persisted request, agent execution,
            critique and synthesis event across the DecisionOS
            engine.
          </p>
        </div>

        <button
          className="secondary-action"
          onClick={() => loadAudit(true)}
          disabled={refreshing}
        >
          <RefreshCw
            size={16}
            className={
              refreshing ? "analytics-spin" : ""
            }
          />
          {refreshing ? "Refreshing..." : "Refresh audit"}
        </button>
      </div>

      <section className="audit-summary-grid-v2">
        <div className="audit-summary-card-v2">
          <span>Total Events</span>
          <strong>{data?.total ?? events.length}</strong>
          <small>Persisted audit records</small>
        </div>

        <div className="audit-summary-card-v2">
          <span>Requests Covered</span>
          <strong>{uniqueRequests}</strong>
          <small>Business question runs</small>
        </div>

        <div className="audit-summary-card-v2">
          <span>Completed Events</span>
          <strong>{completedEvents}</strong>
          <small>Events marked completed</small>
        </div>

        <div className="audit-summary-card-v2">
          <span>Latest Activity</span>
          <strong>
            {latestEvent
              ? formatDateTime(latestEvent.created_at)
              : "—"}
          </strong>
          <small>
            {latestEvent?.event_type || "No events"}
          </small>
        </div>
      </section>

      <section className="audit-control-card-v2">
        <div className="audit-control-search-v2">
          <Search size={15} />
          <input
            value={search}
            onChange={(event) =>
              setSearch(event.target.value)
            }
            placeholder="Search request, question, agent or event..."
          />
        </div>

        <select
          value={eventFilter}
          onChange={(event) =>
            setEventFilter(event.target.value)
          }
        >
          {eventTypes.map((value) => (
            <option value={value} key={value}>
              {value === "ALL" ? "All events" : value}
            </option>
          ))}
        </select>

        <select
          value={agentFilter}
          onChange={(event) =>
            setAgentFilter(event.target.value)
          }
        >
          {agentNames.map((value) => (
            <option value={value} key={value}>
              {value === "ALL"
                ? "All agents"
                : formatAgentName(value)}
            </option>
          ))}
        </select>

        <select
          value={statusFilter}
          onChange={(event) =>
            setStatusFilter(event.target.value)
          }
        >
          {statuses.map((value) => (
            <option value={value} key={value}>
              {value === "ALL" ? "All statuses" : value}
            </option>
          ))}
        </select>
      </section>

      <section className="audit-events-card-v2">
        <div className="audit-events-header-v2">
          <div>
            <span className="card-kicker">EVENT STREAM</span>
            <h2>Audit events</h2>
          </div>

          <span className="section-count">
            {filteredEvents.length} shown
          </span>
        </div>

        {filteredEvents.length === 0 ? (
          <div className="empty-state audit-empty-v2">
            <ShieldCheck size={22} />
            <span>No audit events match the current filters.</span>
          </div>
        ) : (
          <div className="audit-event-list-v2">
            {filteredEvents.map((event) => (
              <AuditEventRow
                key={event.id}
                event={event}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function AuditEventRow({ event }) {
  const [expanded, setExpanded] = useState(false);
  const normalizedStatus = String(
    event.status || "UNKNOWN"
  ).toUpperCase();

  return (
    <div className="audit-event-row-v2">
      <div className="audit-event-marker-v2">
        <ShieldCheck size={15} />
      </div>

      <div className="audit-event-main-v2">
        <div className="audit-event-top-v2">
          <div>
            <strong>
              {formatAuditEventName(event.event_type)}
            </strong>

            <div className="audit-event-meta-v2">
              <span>{event.request_id}</span>
              <span>•</span>
              <span>{event.business_area}</span>
              {event.agent_name && (
                <>
                  <span>•</span>
                  <span>
                    {formatAgentName(event.agent_name)}
                  </span>
                </>
              )}
            </div>
          </div>

          <div className="audit-event-right-v2">
            <StatusBadge status={event.status || "INFO"} />
            <span className="audit-event-time-v2">
              {formatDateTime(event.created_at)}
            </span>
          </div>
        </div>

        <div className="audit-event-question-v2">
          {event.question}
        </div>

        <div className="audit-event-actions-v2">
          <span>{event.question_type}</span>

          {event.details &&
            Object.keys(event.details).length > 0 && (
              <button
                className="text-button"
                onClick={() =>
                  setExpanded((current) => !current)
                }
              >
                {expanded ? "Hide details" : "View details"}
                <ChevronRight
                  size={13}
                  className={
                    expanded
                      ? "audit-chevron-open-v2"
                      : ""
                  }
                />
              </button>
            )}
        </div>

        {expanded && (
          <pre className="audit-event-details-v2">
            {JSON.stringify(event.details, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}

function SystemStatus() {
  const [backendStatus, setBackendStatus] = useState("Checking...");

  useEffect(() => {
    let mounted = true;

    async function checkBackend() {
      try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (!response.ok) throw new Error();
        if (mounted) setBackendStatus("Healthy");
      } catch {
        if (mounted) setBackendStatus("Unavailable");
      }
    }

    checkBackend();
    return () => { mounted = false; };
  }, []);

  return (
    <div className="system-page">
      <div className="page-heading">
        <div>
          <div className="hero-eyebrow"><Activity size={14} />SYSTEM STATUS</div>
          <h1>Engine health</h1>
          <p>Current health of the DecisionOS runtime.</p>
        </div>
      </div>

      <div className="system-grid">
        <SystemCard title="Backend API" value={backendStatus} healthy={backendStatus === "Healthy"} />
        <SystemCard title="PostgreSQL" value="Connected" healthy />
        <SystemCard title="Gemini" value="Configured" healthy />
        <SystemCard title="Specialist Registry" value="13 Agents" healthy />
      </div>
    </div>
  );
}

function SystemCard({ title, value, healthy }) {
  return (
    <div className="system-card">
      <div className="system-card-icon">
        {healthy ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
      </div>
      <div><span>{title}</span><strong>{value}</strong></div>
    </div>
  );
}

function PlaceholderPage({ title, description, icon: Icon }) {
  return (
    <div className="placeholder-page">
      <div className="placeholder-icon"><Icon size={24} /></div>
      <h1>{title}</h1>
      <p>{description}</p>
      <span>This module is part of the DecisionOS roadmap.</span>
    </div>
  );
}

function StatusBadge({ status }) {
  const normalized = String(status || "UNKNOWN").toUpperCase();
  let className = "status-badge";

  if (normalized === "COMPLETED" || normalized === "PASS" || normalized === "HEALTHY") {
    className += " status-positive";
  } else if (normalized === "FAILED" || normalized === "ERROR") {
    className += " status-negative";
  } else {
    className += " status-neutral";
  }

  return <span className={className}>{normalized}</span>;
}

function formatAuditEventName(value) {
  if (!value) return "Unknown Event";

  return String(value)
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatAgentName(value) {
  if (!value) return "Unknown Agent";
  return value
    .replace(/_agent$/, "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatConfidence(value) {
  if (value === null || value === undefined) return "—";
  const number = Number(value);
  if (Number.isNaN(number)) return "—";
  return `${Math.round(number * 100)}%`;
}

function formatDateTime(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

export default App;
