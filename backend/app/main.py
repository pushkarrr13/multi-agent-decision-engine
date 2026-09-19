from uuid import uuid4

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .config import settings
from .database import Base, engine, get_db

from . import models
from . import models_business
from . import models_rules

from .schemas.decision_request import DecisionRequest
from .schemas.decision_response import DecisionResponse
from .schemas.audit_response import AuditHistoryResponse

from .schemas.business_question import BusinessQuestion
from .schemas.business_question_response import BusinessQuestionResponse

from .schemas.business_question_history_response import (
    BusinessDecisionHistory,
    BusinessAgentRunHistory,
    BusinessAuditHistory,
)

from .schemas.business_question_history_list_response import (
    BusinessQuestionHistoryItem,
    BusinessQuestionHistoryListResponse,
)

from .schemas.analytics_response import AnalyticsResponse

from .schemas.business_rule import (
    BusinessRuleCreate,
    BusinessRuleUpdate,
    BusinessRuleResponse,
    BusinessRuleListResponse,
)

from .services.decision_service import DecisionService
from .services.business_question_service import (
    BusinessQuestionService,
)
from .services.analytics_service import AnalyticsService


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# SERVICES
# ============================================================

decision_service = DecisionService()

business_question_service = BusinessQuestionService()

analytics_service = AnalyticsService()


# ============================================================
# BASIC ENDPOINTS
# ============================================================

@app.get("/")
def root():
    return {
        "application": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


# ============================================================
# GENERIC BUSINESS QUESTION
# ============================================================

@app.post(
    "/api/v1/business-questions",
    response_model=BusinessQuestionResponse,
)
def ask_business_question(
    request: BusinessQuestion,
    db: Session = Depends(get_db),
):
    """
    Generic business decision endpoint.

    Workflow:

    Question
        ↓
    Router
        ↓
    Evidence
        ↓
    Specialists
        ↓
    Critic
        ↓
    Synthesis
        ↓
    PostgreSQL
    """

    return business_question_service.ask(
        request,
        db,
    )


# ============================================================
# BUSINESS QUESTION HISTORY LIST
# ============================================================

@app.get(
    "/api/v1/business-questions",
    response_model=BusinessQuestionHistoryListResponse,
)
def list_business_questions(
    db: Session = Depends(get_db),
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    business_area: str | None = None,
    question_type: str | None = None,
    status: str | None = None,
):
    """
    Return previously processed business questions.
    """

    query = (
        db.query(
            models_business.BusinessQuestionRequestModel,
            models_business.BusinessDecisionResultModel,
        )
        .outerjoin(
            models_business.BusinessDecisionResultModel,
            models_business.BusinessDecisionResultModel.request_id
            == models_business.BusinessQuestionRequestModel.request_id,
        )
    )

    if business_area:
        query = query.filter(
            models_business.BusinessQuestionRequestModel.business_area
            == business_area.upper()
        )

    if question_type:
        query = query.filter(
            models_business.BusinessQuestionRequestModel.question_type
            == question_type.upper()
        )

    if status:
        query = query.filter(
            models_business.BusinessQuestionRequestModel.status
            == status.upper()
        )

    total = query.count()

    records = (
        query
        .order_by(
            models_business.BusinessQuestionRequestModel.id.desc()
        )
        .offset(offset)
        .limit(limit)
        .all()
    )

    items = []

    for request_record, decision_record in records:

        if decision_record is not None:
            answer = decision_record.answer
            recommendation = decision_record.recommendation
            confidence = decision_record.confidence
            key_factors = decision_record.key_factors or []
        else:
            answer = None
            recommendation = None
            confidence = None
            key_factors = []

        items.append(
            BusinessQuestionHistoryItem(
                request_id=request_record.request_id,
                question=request_record.question,
                question_type=request_record.question_type,
                business_area=request_record.business_area,
                status=request_record.status,
                answer=answer,
                recommendation=recommendation,
                confidence=confidence,
                key_factors=key_factors,
                created_at=request_record.created_at,
            )
        )

    return BusinessQuestionHistoryListResponse(
        total=total,
        items=items,
    )


# ============================================================
# BUSINESS QUESTION INVESTIGATION
# ============================================================

@app.get(
    "/api/v1/business-questions/{request_id}",
    response_model=BusinessDecisionHistory,
)
def get_business_question_history(
    request_id: str,
    db: Session = Depends(get_db),
):
    """
    Retrieve complete investigation history for a
    previously processed business question.
    """

    request_record = (
        db.query(
            models_business.BusinessQuestionRequestModel
        )
        .filter(
            models_business.BusinessQuestionRequestModel.request_id
            == request_id
        )
        .first()
    )

    if request_record is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No business question found for "
                f"request {request_id}"
            ),
        )

    decision_record = (
        db.query(
            models_business.BusinessDecisionResultModel
        )
        .filter(
            models_business.BusinessDecisionResultModel.request_id
            == request_id
        )
        .first()
    )

    agent_records = (
        db.query(
            models_business.BusinessAgentRunModel
        )
        .filter(
            models_business.BusinessAgentRunModel.request_id
            == request_id
        )
        .order_by(
            models_business.BusinessAgentRunModel.id.asc()
        )
        .all()
    )

    audit_records = (
        db.query(
            models_business.BusinessAuditLogModel
        )
        .filter(
            models_business.BusinessAuditLogModel.request_id
            == request_id
        )
        .order_by(
            models_business.BusinessAuditLogModel.id.asc()
        )
        .all()
    )

    agents = []

    for agent in agent_records:
        agents.append(
            BusinessAgentRunHistory(
                id=agent.id,
                request_id=agent.request_id,
                agent_name=agent.agent_name,
                status=agent.status,
                score=agent.score,
                recommendation=agent.recommendation,
                findings=agent.findings or [],
                created_at=agent.created_at,
            )
        )

    audit_events = []

    for event in audit_records:
        audit_events.append(
            BusinessAuditHistory(
                id=event.id,
                request_id=event.request_id,
                event_type=event.event_type,
                agent_name=event.agent_name,
                status=event.status,
                details=event.details or {},
                created_at=event.created_at,
            )
        )

    if decision_record is not None:

        answer = decision_record.answer

        recommendation = (
            decision_record.recommendation
        )

        confidence = (
            decision_record.confidence
        )

        key_factors = (
            decision_record.key_factors or []
        )

        risks = (
            decision_record.risks or []
        )

        assumptions = (
            decision_record.assumptions or []
        )

        evidence = (
            decision_record.evidence or []
        )

        agent_conflicts = (
            decision_record.agent_conflicts or []
        )

        created_at = (
            decision_record.created_at
        )

    else:

        answer = None
        recommendation = None
        confidence = None
        key_factors = []
        risks = []
        assumptions = []
        evidence = []
        agent_conflicts = []

        created_at = (
            request_record.created_at
        )

    return BusinessDecisionHistory(
        request_id=request_record.request_id,
        question=request_record.question,
        question_type=request_record.question_type,
        business_area=request_record.business_area,
        status=request_record.status,
        request_data=request_record.request_data or {},

        answer=answer,
        recommendation=recommendation,
        confidence=confidence,

        key_factors=key_factors,
        risks=risks,
        assumptions=assumptions,
        evidence=evidence,
        agent_conflicts=agent_conflicts,

        created_at=created_at,

        agents=agents,
        audit_events=audit_events,
    )


# ============================================================
# ANALYTICS
# ============================================================

@app.get(
    "/api/v1/analytics",
    response_model=AnalyticsResponse,
)
def get_analytics(
    db: Session = Depends(get_db),
):
    """
    Return analytics calculated from persisted
    business-question and agent data.
    """

    return analytics_service.get_analytics(
        db
    )


# ============================================================
# GENERIC AUDIT TRAIL
# ============================================================

@app.get("/api/v1/audit-trail")
def get_business_audit_trail(
    db: Session = Depends(get_db),
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    request_id: str | None = None,
    event_type: str | None = None,
    agent_name: str | None = None,
    status: str | None = None,
):
    """
    Return the persisted audit trail for the generic
    business decision engine.
    """

    query = (
        db.query(
            models_business.BusinessAuditLogModel,
            models_business.BusinessQuestionRequestModel,
        )
        .join(
            models_business.BusinessQuestionRequestModel,
            models_business.BusinessQuestionRequestModel.request_id
            == models_business.BusinessAuditLogModel.request_id,
        )
    )

    if request_id:
        query = query.filter(
            models_business.BusinessAuditLogModel.request_id
            == request_id
        )

    if event_type:
        query = query.filter(
            models_business.BusinessAuditLogModel.event_type
            == event_type.upper()
        )

    if agent_name:
        query = query.filter(
            models_business.BusinessAuditLogModel.agent_name
            == agent_name
        )

    if status:
        query = query.filter(
            models_business.BusinessAuditLogModel.status
            == status.upper()
        )

    total = query.count()

    records = (
        query
        .order_by(
            models_business.BusinessAuditLogModel.id.desc()
        )
        .offset(offset)
        .limit(limit)
        .all()
    )

    events = []

    for audit_record, request_record in records:

        events.append(
            {
                "id": audit_record.id,
                "request_id": audit_record.request_id,
                "event_type": audit_record.event_type,
                "agent_name": audit_record.agent_name,
                "status": audit_record.status,
                "details": audit_record.details or {},
                "question": request_record.question,
                "question_type": request_record.question_type,
                "business_area": request_record.business_area,
                "request_status": request_record.status,
                "created_at": audit_record.created_at,
            }
        )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "filters": {
            "request_id": request_id,
            "event_type": event_type,
            "agent_name": agent_name,
            "status": status,
        },
        "events": events,
    }


# ============================================================
# GENERIC AUDIT TRAIL FOR ONE REQUEST
# ============================================================

@app.get("/api/v1/audit-trail/{request_id}")
def get_business_audit_trail_for_request(
    request_id: str,
    db: Session = Depends(get_db),
):
    """
    Return the complete audit trail for one
    generic business question request.
    """

    request_record = (
        db.query(
            models_business.BusinessQuestionRequestModel
        )
        .filter(
            models_business.BusinessQuestionRequestModel.request_id
            == request_id
        )
        .first()
    )

    if request_record is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No business question found for "
                f"request {request_id}"
            ),
        )

    audit_records = (
        db.query(
            models_business.BusinessAuditLogModel
        )
        .filter(
            models_business.BusinessAuditLogModel.request_id
            == request_id
        )
        .order_by(
            models_business.BusinessAuditLogModel.id.asc()
        )
        .all()
    )

    events = []

    for event in audit_records:

        events.append(
            {
                "id": event.id,
                "request_id": event.request_id,
                "event_type": event.event_type,
                "agent_name": event.agent_name,
                "status": event.status,
                "details": event.details or {},
                "created_at": event.created_at,
            }
        )

    return {
        "request_id": request_record.request_id,
        "question": request_record.question,
        "question_type": request_record.question_type,
        "business_area": request_record.business_area,
        "request_status": request_record.status,
        "total": len(events),
        "events": events,
    }


# ============================================================
# BUSINESS RULES
# ============================================================

@app.post(
    "/api/v1/rules",
    response_model=BusinessRuleResponse,
)
def create_business_rule(
    request: BusinessRuleCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new generic business rule.
    """

    rule_id = f"RULE-{uuid4().hex[:8].upper()}"

    rule = models_rules.BusinessRuleModel(
        rule_id=rule_id,
        name=request.name,
        description=request.description,
        business_area=request.business_area.upper(),
        question_types=[
            item.upper()
            for item in request.question_types
        ],
        priority=request.priority,
        severity=request.severity.upper(),
        conditions=[
            condition.model_dump()
            for condition in request.conditions
        ],
        actions=[
            action.model_dump()
            for action in request.actions
        ],
        enabled=request.enabled,
    )

    db.add(rule)
    db.commit()
    db.refresh(rule)

    return BusinessRuleResponse(
        id=rule.id,
        rule_id=rule.rule_id,
        name=rule.name,
        description=rule.description,
        business_area=rule.business_area,
        question_types=rule.question_types or [],
        priority=rule.priority,
        severity=rule.severity,
        conditions=rule.conditions or [],
        actions=rule.actions or [],
        enabled=rule.enabled,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


@app.get(
    "/api/v1/rules",
    response_model=BusinessRuleListResponse,
)
def list_business_rules(
    db: Session = Depends(get_db),
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    business_area: str | None = None,
    severity: str | None = None,
    enabled: bool | None = None,
):
    """
    Return business rules with optional filters.
    """

    query = db.query(
        models_rules.BusinessRuleModel
    )

    if business_area:
        query = query.filter(
            models_rules.BusinessRuleModel.business_area
            == business_area.upper()
        )

    if severity:
        query = query.filter(
            models_rules.BusinessRuleModel.severity
            == severity.upper()
        )

    if enabled is not None:
        query = query.filter(
            models_rules.BusinessRuleModel.enabled
            == enabled
        )

    total = query.count()

    rules = (
        query
        .order_by(
            models_rules.BusinessRuleModel.priority.asc(),
            models_rules.BusinessRuleModel.id.desc(),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )

    items = []

    for rule in rules:
        items.append(
            BusinessRuleResponse(
                id=rule.id,
                rule_id=rule.rule_id,
                name=rule.name,
                description=rule.description,
                business_area=rule.business_area,
                question_types=rule.question_types or [],
                priority=rule.priority,
                severity=rule.severity,
                conditions=rule.conditions or [],
                actions=rule.actions or [],
                enabled=rule.enabled,
                created_at=rule.created_at,
                updated_at=rule.updated_at,
            )
        )

    return BusinessRuleListResponse(
        total=total,
        items=items,
    )


@app.get(
    "/api/v1/rules/{rule_id}",
    response_model=BusinessRuleResponse,
)
def get_business_rule(
    rule_id: str,
    db: Session = Depends(get_db),
):
    """
    Return one business rule.
    """

    rule = (
        db.query(
            models_rules.BusinessRuleModel
        )
        .filter(
            models_rules.BusinessRuleModel.rule_id
            == rule_id
        )
        .first()
    )

    if rule is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No business rule found for "
                f"rule {rule_id}"
            ),
        )

    return BusinessRuleResponse(
        id=rule.id,
        rule_id=rule.rule_id,
        name=rule.name,
        description=rule.description,
        business_area=rule.business_area,
        question_types=rule.question_types or [],
        priority=rule.priority,
        severity=rule.severity,
        conditions=rule.conditions or [],
        actions=rule.actions or [],
        enabled=rule.enabled,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


@app.put(
    "/api/v1/rules/{rule_id}",
    response_model=BusinessRuleResponse,
)
def update_business_rule(
    rule_id: str,
    request: BusinessRuleUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an existing business rule.
    """

    rule = (
        db.query(
            models_rules.BusinessRuleModel
        )
        .filter(
            models_rules.BusinessRuleModel.rule_id
            == rule_id
        )
        .first()
    )

    if rule is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No business rule found for "
                f"rule {rule_id}"
            ),
        )

    update_data = request.model_dump(
        exclude_unset=True
    )

    if "name" in update_data:
        rule.name = update_data["name"]

    if "description" in update_data:
        rule.description = update_data["description"]

    if "business_area" in update_data:
        rule.business_area = (
            update_data["business_area"].upper()
        )

    if "question_types" in update_data:
        rule.question_types = [
            item.upper()
            for item in (
                update_data["question_types"]
                or []
            )
        ]

    if "priority" in update_data:
        rule.priority = update_data["priority"]

    if "severity" in update_data:
        rule.severity = (
            update_data["severity"].upper()
        )

    if "conditions" in update_data:
        rule.conditions = [
            condition.model_dump()
            if hasattr(condition, "model_dump")
            else condition
            for condition in (
                update_data["conditions"] or []
            )
        ]

    if "actions" in update_data:
        rule.actions = [
            action.model_dump()
            if hasattr(action, "model_dump")
            else action
            for action in (
                update_data["actions"] or []
            )
        ]

    if "enabled" in update_data:
        rule.enabled = update_data["enabled"]

    db.commit()
    db.refresh(rule)

    return BusinessRuleResponse(
        id=rule.id,
        rule_id=rule.rule_id,
        name=rule.name,
        description=rule.description,
        business_area=rule.business_area,
        question_types=rule.question_types or [],
        priority=rule.priority,
        severity=rule.severity,
        conditions=rule.conditions or [],
        actions=rule.actions or [],
        enabled=rule.enabled,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


@app.delete("/api/v1/rules/{rule_id}")
def delete_business_rule(
    rule_id: str,
    db: Session = Depends(get_db),
):
    """
    Delete a business rule.
    """

    rule = (
        db.query(
            models_rules.BusinessRuleModel
        )
        .filter(
            models_rules.BusinessRuleModel.rule_id
            == rule_id
        )
        .first()
    )

    if rule is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No business rule found for "
                f"rule {rule_id}"
            ),
        )

    db.delete(rule)
    db.commit()

    return {
        "rule_id": rule_id,
        "status": "DELETED",
    }


# ============================================================
# LEGACY CREDIT DECISION
# ============================================================

@app.post(
    "/api/v1/decisions",
    response_model=DecisionResponse,
)
def create_decision(
    request: DecisionRequest,
    db: Session = Depends(get_db),
):
    """
    Legacy credit decision endpoint.
    """

    return decision_service.make_decision(
        request,
        db,
    )


# ============================================================
# LEGACY CREDIT AUDIT HISTORY
# ============================================================

@app.get(
    "/api/v1/decisions/{decision_id}/audit",
    response_model=AuditHistoryResponse,
)
def get_decision_audit(
    decision_id: str,
    db: Session = Depends(get_db),
):
    audit_events = (
        db.query(
            models.AuditLogModel
        )
        .filter(
            models.AuditLogModel.decision_id
            == decision_id
        )
        .order_by(
            models.AuditLogModel.id.asc()
        )
        .all()
    )

    if not audit_events:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No audit history found for "
                f"decision {decision_id}"
            ),
        )

    events = []

    for event in audit_events:
        events.append(
            {
                "id": event.id,
                "decision_id": event.decision_id,
                "event_type": event.event_type,
                "agent_name": event.agent_name,
                "status": event.status,
                "decision": event.decision,
                "details": event.details,
                "created_at": event.created_at,
            }
        )

    return {
        "decision_id": decision_id,
        "total_events": len(events),
        "events": events,
    }