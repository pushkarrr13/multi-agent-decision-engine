from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models_business import (
    BusinessQuestionRequestModel,
    BusinessAgentRunModel,
    BusinessDecisionResultModel,
)

from ..schemas.analytics_response import (
    AnalyticsOverview,
    BusinessAreaMetric,
    QuestionTypeMetric,
    AgentMetric,
    AnalyticsResponse,
)


class AnalyticsService:
    """
    Calculates analytics from persisted business-question data.

    All values are derived from PostgreSQL.
    No dashboard metrics are hardcoded.
    """

    def get_analytics(
        self,
        db: Session
    ) -> AnalyticsResponse:

        # ============================================================
        # REQUEST COUNTS
        # ============================================================

        total_questions = (
            db.query(
                func.count(
                    BusinessQuestionRequestModel.id
                )
            )
            .scalar()
            or 0
        )

        completed_questions = (
            db.query(
                func.count(
                    BusinessQuestionRequestModel.id
                )
            )
            .filter(
                BusinessQuestionRequestModel.status
                == "COMPLETED"
            )
            .scalar()
            or 0
        )

        failed_questions = (
            db.query(
                func.count(
                    BusinessQuestionRequestModel.id
                )
            )
            .filter(
                BusinessQuestionRequestModel.status
                == "FAILED"
            )
            .scalar()
            or 0
        )

        # ============================================================
        # AVERAGE CONFIDENCE
        # ============================================================

        average_confidence = (
            db.query(
                func.avg(
                    BusinessDecisionResultModel.confidence
                )
            )
            .scalar()
        )

        if average_confidence is not None:
            average_confidence = round(
                float(average_confidence),
                4
            )

        # ============================================================
        # QUESTION TYPE COUNTS
        # ============================================================

        question_type_rows = (
            db.query(
                BusinessQuestionRequestModel.question_type,
                func.count(
                    BusinessQuestionRequestModel.id
                )
            )
            .group_by(
                BusinessQuestionRequestModel.question_type
            )
            .all()
        )

        question_type_counts = {
            str(question_type).upper(): int(count)
            for question_type, count
            in question_type_rows
        }

        # ============================================================
        # BUSINESS AREA COUNTS
        # ============================================================

        business_area_rows = (
            db.query(
                BusinessQuestionRequestModel.business_area,
                func.count(
                    BusinessQuestionRequestModel.id
                )
            )
            .group_by(
                BusinessQuestionRequestModel.business_area
            )
            .all()
        )

        business_area_counts = {
            str(business_area).upper(): int(count)
            for business_area, count
            in business_area_rows
        }

        # ============================================================
        # BUSINESS AREA CONFIDENCE
        # ============================================================

        business_area_confidence_rows = (
            db.query(
                BusinessQuestionRequestModel.business_area,
                func.avg(
                    BusinessDecisionResultModel.confidence
                )
            )
            .join(
                BusinessDecisionResultModel,
                BusinessDecisionResultModel.request_id
                == BusinessQuestionRequestModel.request_id
            )
            .group_by(
                BusinessQuestionRequestModel.business_area
            )
            .all()
        )

        business_area_confidence = {}

        for business_area, confidence in (
            business_area_confidence_rows
        ):
            key = str(
                business_area
            ).upper()

            business_area_confidence[key] = (
                round(
                    float(confidence),
                    4
                )
                if confidence is not None
                else None
            )

        # ============================================================
        # BUSINESS AREA METRICS
        # ============================================================

        business_areas = []

        for business_area, count in sorted(
            business_area_counts.items(),
            key=lambda item: item[1],
            reverse=True
        ):
            business_areas.append(
                BusinessAreaMetric(
                    business_area=business_area,
                    question_count=count,
                    average_confidence=(
                        business_area_confidence.get(
                            business_area
                        )
                    )
                )
            )

        # ============================================================
        # QUESTION TYPE METRICS
        # ============================================================

        question_types = []

        for question_type, count in sorted(
            question_type_counts.items(),
            key=lambda item: item[1],
            reverse=True
        ):
            question_types.append(
                QuestionTypeMetric(
                    question_type=question_type,
                    question_count=count
                )
            )

        # ============================================================
        # AGENT METRICS
        # ============================================================

        agent_rows = (
            db.query(
                BusinessAgentRunModel
            )
            .order_by(
                BusinessAgentRunModel.agent_name.asc()
            )
            .all()
        )

        agent_stats = {}

        for agent in agent_rows:

            name = agent.agent_name

            if name not in agent_stats:
                agent_stats[name] = {
                    "run_count": 0,
                    "completed_count": 0,
                    "failed_count": 0,
                    "scores": []
                }

            stats = agent_stats[name]

            stats["run_count"] += 1

            if agent.status == "COMPLETED":
                stats["completed_count"] += 1

            if agent.status == "FAILED":
                stats["failed_count"] += 1

            if agent.score is not None:
                try:
                    stats["scores"].append(
                        float(agent.score)
                    )
                except (
                    TypeError,
                    ValueError
                ):
                    pass

        agents = []

        for agent_name, stats in sorted(
            agent_stats.items()
        ):

            scores = stats["scores"]

            average_score = (
                round(
                    sum(scores) / len(scores),
                    2
                )
                if scores
                else None
            )

            agents.append(
                AgentMetric(
                    agent_name=agent_name,
                    run_count=stats["run_count"],
                    completed_count=stats["completed_count"],
                    failed_count=stats["failed_count"],
                    average_score=average_score
                )
            )

        # ============================================================
        # TOP BUSINESS AREA
        # ============================================================

        top_business_area = None

        if business_area_counts:
            top_business_area = max(
                business_area_counts,
                key=business_area_counts.get
            )

        # ============================================================
        # OVERVIEW
        # ============================================================

        overview = AnalyticsOverview(
            total_questions=total_questions,
            completed_questions=completed_questions,
            failed_questions=failed_questions,
            average_confidence=average_confidence,

            investigate_count=question_type_counts.get(
                "INVESTIGATE",
                0
            ),

            decide_count=question_type_counts.get(
                "DECIDE",
                0
            ),

            recommend_count=question_type_counts.get(
                "RECOMMEND",
                0
            ),

            analyze_count=question_type_counts.get(
                "ANALYZE",
                0
            ),

            compare_count=question_type_counts.get(
                "COMPARE",
                0
            ),

            predict_count=question_type_counts.get(
                "PREDICT",
                0
            ),

            explain_count=question_type_counts.get(
                "EXPLAIN",
                0
            ),

            optimize_count=question_type_counts.get(
                "OPTIMIZE",
                0
            ),

            top_business_area=top_business_area
        )

        # ============================================================
        # RECENT ACTIVITY
        # ============================================================

        recent_requests = (
            db.query(
                BusinessQuestionRequestModel
            )
            .order_by(
                BusinessQuestionRequestModel.id.desc()
            )
            .limit(10)
            .all()
        )

        recent_activity = []

        for request in recent_requests:

            decision = (
                db.query(
                    BusinessDecisionResultModel
                )
                .filter(
                    BusinessDecisionResultModel.request_id
                    == request.request_id
                )
                .first()
            )

            recent_activity.append(
                {
                    "request_id": request.request_id,
                    "question": request.question,
                    "question_type": request.question_type,
                    "business_area": request.business_area,
                    "status": request.status,
                    "confidence": (
                        decision.confidence
                        if decision is not None
                        else None
                    ),
                    "created_at": request.created_at
                }
            )

        # ============================================================
        # FINAL RESPONSE
        # ============================================================

        return AnalyticsResponse(
            overview=overview,
            business_areas=business_areas,
            question_types=question_types,
            agents=agents,
            recent_activity=recent_activity
        )