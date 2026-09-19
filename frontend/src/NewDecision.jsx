import { useState } from "react";
import {
  ArrowRight,
  Brain,
  Database,
  GitBranch,
  Loader2,
  ShieldCheck,
  Sparkles,
  Target,
} from "lucide-react";

import "./NewDecision.css";


const API_BASE_URL = "http://localhost:8000";


function NewDecision({ onComplete }) {
  const [question, setQuestion] = useState("");

  const [questionType, setQuestionType] = useState("AUTO");

  const [businessArea, setBusinessArea] = useState("AUTO");

  const [context, setContext] = useState("");

  const [objectives, setObjectives] = useState("");

  const [constraints, setConstraints] = useState("");

  const [requestedOutput, setRequestedOutput] = useState(
    "RECOMMENDATION"
  );

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");


  const parseLines = (value) => {
    return value
      .split("\n")
      .map((item) => item.trim())
      .filter(Boolean);
  };


  const parseContext = () => {
    if (!context.trim()) {
      return {};
    }

    try {
      return JSON.parse(context);
    } catch {
      throw new Error(
        "Context must be valid JSON. Example: {\"revenue\": 1200000}"
      );
    }
  };


  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");

    if (!question.trim()) {
      setError("Enter a business question before submitting.");
      return;
    }

    let parsedContext;

    try {
      parsedContext = parseContext();
    } catch (err) {
      setError(err.message);
      return;
    }

    const payload = {
      question: question.trim(),
      question_type: questionType,
      business_area: businessArea,
      context: parsedContext,
      objectives: parseLines(objectives),
      constraints: parseLines(constraints),
      data_sources: [],
      success_criteria: [],
      requested_output: requestedOutput,
    };

    try {
      setLoading(true);

      const response = await fetch(
        `${API_BASE_URL}/api/v1/business-questions`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        }
      );

      const result = await response.json();

      if (!response.ok) {
        throw new Error(
          result?.detail ||
            "The business question could not be processed."
        );
      }

      if (onComplete) {
        onComplete(result);
      }

    } catch (err) {
      setError(
        err.message ||
          "Unable to connect to the Decision Engine."
      );

    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="new-decision-page">

      <div className="decision-header">

        <div>
          <div className="eyebrow">
            <Sparkles size={14} />
            BUSINESS DECISION ENGINE
          </div>

          <h1>
            Ask a business question.
          </h1>

          <p>
            Let the engine determine which specialists,
            evidence and reasoning are required.
          </p>
        </div>

      </div>


      <div className="decision-layout">

        <form
          className="decision-form-card"
          onSubmit={handleSubmit}
        >

          <div className="form-section">

            <label>
              Business Question
            </label>

            <textarea
              value={question}
              onChange={(event) =>
                setQuestion(event.target.value)
              }
              placeholder="Example: Why did delivery delays increase this month?"
              rows={5}
            />

          </div>


          <div className="form-grid">

            <div className="form-section">

              <label>
                Question Type
              </label>

              <select
                value={questionType}
                onChange={(event) =>
                  setQuestionType(event.target.value)
                }
              >
                <option value="AUTO">
                  Auto Detect
                </option>

                <option value="ANALYZE">
                  Analyze
                </option>

                <option value="COMPARE">
                  Compare
                </option>

                <option value="INVESTIGATE">
                  Investigate
                </option>

                <option value="PREDICT">
                  Predict
                </option>

                <option value="RECOMMEND">
                  Recommend
                </option>

                <option value="DECIDE">
                  Decide
                </option>

                <option value="EXPLAIN">
                  Explain
                </option>

                <option value="OPTIMIZE">
                  Optimize
                </option>

              </select>

            </div>


            <div className="form-section">

              <label>
                Business Area
              </label>

              <select
                value={businessArea}
                onChange={(event) =>
                  setBusinessArea(event.target.value)
                }
              >
                <option value="AUTO">
                  Auto Detect
                </option>

                <option value="FINANCE">
                  Finance
                </option>

                <option value="SALES">
                  Sales
                </option>

                <option value="MARKETING">
                  Marketing
                </option>

                <option value="CUSTOMER">
                  Customer
                </option>

                <option value="OPERATIONS">
                  Operations
                </option>

                <option value="PRODUCT">
                  Product
                </option>

                <option value="HR">
                  HR
                </option>

                <option value="PROCUREMENT">
                  Procurement
                </option>

                <option value="STRATEGY">
                  Strategy
                </option>

                <option value="RISK">
                  Risk
                </option>

                <option value="TECHNOLOGY">
                  Technology
                </option>

                <option value="COMPLIANCE">
                  Compliance
                </option>

                <option value="MARKET">
                  Market
                </option>

              </select>

            </div>

          </div>


          <div className="form-section">

            <label>
              Business Context
            </label>

            <textarea
              value={context}
              onChange={(event) =>
                setContext(event.target.value)
              }
              placeholder={`{
  "current_month_delay_rate": 18,
  "previous_month_delay_rate": 11
}`}
              rows={7}
            />

            <span className="field-help">
              Optional JSON containing the facts,
              metrics or structured data available to the engine.
            </span>

          </div>


          <div className="form-grid">

            <div className="form-section">

              <label>
                Objectives
              </label>

              <textarea
                value={objectives}
                onChange={(event) =>
                  setObjectives(event.target.value)
                }
                placeholder={
                  "Identify the main causes\nFind actionable improvements"
                }
                rows={5}
              />

              <span className="field-help">
                One objective per line.
              </span>

            </div>


            <div className="form-section">

              <label>
                Constraints
              </label>

              <textarea
                value={constraints}
                onChange={(event) =>
                  setConstraints(event.target.value)
                }
                placeholder={
                  "Use only supplied data\nDo not invent missing metrics"
                }
                rows={5}
              />

              <span className="field-help">
                One constraint per line.
              </span>

            </div>

          </div>


          <div className="form-section">

            <label>
              Requested Output
            </label>

            <select
              value={requestedOutput}
              onChange={(event) =>
                setRequestedOutput(event.target.value)
              }
            >
              <option value="ANSWER">
                Answer
              </option>

              <option value="ANALYSIS">
                Analysis
              </option>

              <option value="RECOMMENDATION">
                Recommendation
              </option>

              <option value="DECISION">
                Decision
              </option>

              <option value="COMPARISON">
                Comparison
              </option>

              <option value="INVESTIGATION">
                Investigation
              </option>

            </select>

          </div>


          {error && (
            <div className="form-error">
              {error}
            </div>
          )}


          <button
            type="submit"
            className="decision-submit"
            disabled={loading}
          >

            {loading ? (
              <>
                <Loader2
                  size={18}
                  className="spin"
                />

                Running multi-agent analysis...
              </>
            ) : (
              <>
                Run Decision Engine

                <ArrowRight size={18} />
              </>
            )}

          </button>

        </form>


        <aside className="decision-side-panel">

          <div className="side-panel-title">
            <Brain size={17} />

            How the engine works
          </div>


          <div className="workflow-item">

            <div className="workflow-icon">
              <GitBranch size={17} />
            </div>

            <div>
              <strong>
                Semantic Routing
              </strong>

              <span>
                Gemini understands the question and
                selects relevant specialists.
              </span>
            </div>

          </div>


          <div className="workflow-item">

            <div className="workflow-icon">
              <Database size={17} />
            </div>

            <div>
              <strong>
                Evidence Review
              </strong>

              <span>
                Available information and evidence gaps
                are identified before reasoning.
              </span>
            </div>

          </div>


          <div className="workflow-item">

            <div className="workflow-icon">
              <Target size={17} />
            </div>

            <div>
              <strong>
                Specialist Analysis
              </strong>

              <span>
                Relevant business-domain agents analyze
                the question independently.
              </span>
            </div>

          </div>


          <div className="workflow-item">

            <div className="workflow-icon">
              <ShieldCheck size={17} />
            </div>

            <div>
              <strong>
                Critic Review
              </strong>

              <span>
                Agent reasoning is checked for conflicts,
                gaps and unsupported conclusions.
              </span>
            </div>

          </div>


          <div className="workflow-item">

            <div className="workflow-icon">
              <Sparkles size={17} />
            </div>

            <div>
              <strong>
                Final Synthesis
              </strong>

              <span>
                Gemini produces an explainable answer,
                recommendation, risks and evidence.
              </span>
            </div>

          </div>

        </aside>

      </div>

    </div>
  );
}


export default NewDecision;