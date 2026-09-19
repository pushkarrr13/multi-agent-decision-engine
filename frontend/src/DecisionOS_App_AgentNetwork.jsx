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

          {activePage === "rules" && (
            <PlaceholderPage
              title="Business Rules"
              description="Manage configurable policies and decision constraints across business domains."
              icon={GitBranch}
            />
          )}

          {activePage === "audit" && (
            <PlaceholderPage
              title="Audit Trail"
              description="Review every request, agent execution, critique and synthesis event."
              icon={ShieldCheck}
            />
          )}

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

function AgentNetwork() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const specialistAgents = [
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
    {
      key: "question_router_agent",
      name: "Question Router",
      description: "Semantic classification",
      icon: GitBranch,
    },
    {
      key: "evidence_agent",
      name: "Evidence Agent",
      description: "Evidence validation",
      icon: Database,
    },
    {
      key: "critic_agent",
      name: "Critic",
      description: "Reasoning validation",
      icon: ShieldCheck,
    },
    {
      key: "synthesis_agent",
      name: "Synthesis",
      description: "Final business answer",
      icon: Sparkles,
    },
  ];

  useEffect(() => {
    let mounted = true;

    async function loadAgentAnalytics() {
      try {
        setLoading(true);
        setError("");

        const response = await fetch(
          `${API_BASE_URL}/api/v1/analytics`
        );

        if (!response.ok) {
          throw new Error(
            "Unable to load agent analytics."
          );
        }

        const data = await response.json();

        if (mounted) {
          setAnalytics(data);
        }
      } catch (err) {
        if (mounted) {
          setError(
            err.message ||
              "Unable to load agent analytics."
          );
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    loadAgentAnalytics();

    return () => {
      mounted = false;
    };
  }, []);

  const agentMetrics = analytics?.agents || [];

  const metricsByName = agentMetrics.reduce(
    (map, item) => {
      map[item.agent_name] = item;
      return map;
    },
    {}
  );

  const getMetric = (agentName) => {
    return (
      metricsByName[agentName] || {
        run_count: 0,
        completed_count: 0,
        failed_count: 0,
        average_score: null,
      }
    );
  };

  const totalRuns = agentMetrics.reduce(
    (sum, item) => sum + (Number(item.run_count) || 0),
    0
  );

  const activeAgents = agentMetrics.filter(
    (item) => Number(item.run_count) > 0
  ).length;

  const completedRuns = agentMetrics.reduce(
    (sum, item) =>
      sum + (Number(item.completed_count) || 0),
    0
  );

  return (
    <div className="agent-network-page">
      <div className="page-heading">
        <div>
          <div className="hero-eyebrow">
            <Network size={14} />
            AGENT NETWORK
          </div>

          <h1>Specialist intelligence layer</h1>

          <p>
            Domain specialists are selected dynamically for each business
            question. Execution metrics below are loaded from the DecisionOS
            analytics service and persisted agent runs.
          </p>
        </div>
      </div>

      {loading ? (
        <div className="empty-state full-page-empty">
          <Network size={22} />
          Loading agent network...
        </div>
      ) : error ? (
        <div className="empty-state full-page-empty">
          <AlertTriangle size={22} />
          <span>{error}</span>
        </div>
      ) : (
        <>
          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                "repeat(3, minmax(0, 1fr))",
              gap: "13px",
              marginBottom: "18px",
            }}
          >
            <div className="metric-card">
              <div className="metric-icon">
                <Activity size={17} />
              </div>
              <div>
                <span className="metric-label">
                  Agent Runs
                </span>
                <div className="metric-value">
                  {totalRuns}
                </div>
                <span className="metric-caption">
                  Persisted executions
                </span>
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-icon">
                <Network size={17} />
              </div>
              <div>
                <span className="metric-label">
                  Active Agents
                </span>
                <div className="metric-value">
                  {activeAgents}
                </div>
                <span className="metric-caption">
                  Agents with recorded runs
                </span>
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-icon">
                <CheckCircle2 size={17} />
              </div>
              <div>
                <span className="metric-label">
                  Completed Runs
                </span>
                <div className="metric-value">
                  {completedRuns}
                </div>
                <span className="metric-caption">
                  Successful agent executions
                </span>
              </div>
            </div>
          </div>

          <div className="agent-network-grid">
            <div className="network-core-card">
              <div className="network-core">
                <Brain size={28} />
              </div>

              <strong>Gemini Orchestrator</strong>

              <span>
                Routing, evidence, critique and synthesis
              </span>

              <div
                style={{
                  display: "flex",
                  gap: "8px",
                  marginTop: "14px",
                  flexWrap: "wrap",
                  justifyContent: "center",
                }}
              >
                {coreAgents.map((agent) => {
                  const metric = getMetric(agent.key);
                  const Icon = agent.icon;

                  return (
                    <div
                      key={agent.key}
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "6px",
                        padding: "6px 9px",
                        border:
                          "1px solid rgba(255,255,255,0.08)",
                        borderRadius: "999px",
                        background:
                          "rgba(255,255,255,0.025)",
                        fontSize: "9px",
                        color: "#94a3b8",
                      }}
                    >
                      <Icon size={11} />
                      {agent.name}
                      <strong
                        style={{
                          color: "#dbe4ef",
                          fontSize: "9px",
                        }}
                      >
                        {metric.run_count}
                      </strong>
                    </div>
                  );
                })}
              </div>
            </div>

            {specialistAgents.map((agent) => {
              const key = `${agent.toLowerCase()}_agent`;
              const metric = getMetric(key);
              const hasRuns = Number(metric.run_count) > 0;

              return (
                <div
                  className="network-agent-card"
                  key={agent}
                >
                  <div className="network-agent-icon">
                    <Network size={16} />
                  </div>

                  <strong>{agent}</strong>

                  <span>Specialist Agent</span>

                  <div className="agent-online">
                    <span />
                    {hasRuns ? "Executed" : "Available"}
                  </div>

                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns:
                        "repeat(2, minmax(0, 1fr))",
                      gap: "8px",
                      marginTop: "12px",
                    }}
                  >
                    <div
                      style={{
                        padding: "7px 8px",
                        border:
                          "1px solid rgba(255,255,255,0.06)",
                        borderRadius: "8px",
                        background:
                          "rgba(255,255,255,0.018)",
                      }}
                    >
                      <div
                        style={{
                          fontSize: "8px",
                          color: "#637287",
                          textTransform: "uppercase",
                          letterSpacing: "0.08em",
                        }}
                      >
                        Runs
                      </div>
                      <strong
                        style={{
                          display: "block",
                          marginTop: "3px",
                          fontSize: "12px",
                          color: "#d7e0eb",
                        }}
                      >
                        {metric.run_count}
                      </strong>
                    </div>

                    <div
                      style={{
                        padding: "7px 8px",
                        border:
                          "1px solid rgba(255,255,255,0.06)",
                        borderRadius: "8px",
                        background:
                          "rgba(255,255,255,0.018)",
                      }}
                    >
                      <div
                        style={{
                          fontSize: "8px",
                          color: "#637287",
                          textTransform: "uppercase",
                          letterSpacing: "0.08em",
                        }}
                      >
                        Score
                      </div>
                      <strong
                        style={{
                          display: "block",
                          marginTop: "3px",
                          fontSize: "12px",
                          color: "#d7e0eb",
                        }}
                      >
                        {metric.average_score != null
                          ? Number(
                              metric.average_score
                            ).toFixed(1)
                          : "—"}
                      </strong>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <section
            className="dashboard-card"
            style={{ marginTop: "18px" }}
          >
            <div className="card-header">
              <div>
                <span className="card-kicker">
                  LIVE METRICS
                </span>
                <h2>Agent execution summary</h2>
              </div>

              <span className="section-count">
                {agentMetrics.length} agents with recorded data
              </span>
            </div>

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
                  {agentMetrics.map((agent) => (
                    <tr key={agent.agent_name}>
                      <td>
                        <div className="analytics-agent-name">
                          <div className="analytics-agent-icon">
                            <Brain size={13} />
                          </div>
                          <span>
                            {formatAgentName(
                              agent.agent_name
                            )}
                          </span>
                        </div>
                      </td>

                      <td>{agent.run_count ?? 0}</td>
                      <td>{agent.completed_count ?? 0}</td>
                      <td>{agent.failed_count ?? 0}</td>
                      <td>
                        {agent.average_score != null
                          ? Number(
                              agent.average_score
                            ).toFixed(1)
                          : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
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
