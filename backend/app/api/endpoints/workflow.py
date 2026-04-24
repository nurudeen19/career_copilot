"""Authenticated streaming entrypoint for the career LangGraph."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.agent_runtime import get_agent_runtime
from app.core.rate_limit import limiter, limit_workflow_stream
from app.db.session import get_db
from app.models.user import User
from app.schema.workflow import WorkflowStreamRequest
from app.services.workflow_stream import aiter_workflow_sse
from app.services.workflow_thread import delete_workflow_thread_for_user

router = APIRouter()


@router.post("/stream")
@limiter.limit(limit_workflow_stream)
async def post_workflow_stream(
    request: Request,
    body: WorkflowStreamRequest,
    user: Annotated[User, Depends(get_current_user)],
) -> StreamingResponse:
    """
    Run one workflow turn; SSE ``data:`` lines carry each node's ``patch`` until ``event: done``.
    Input size + prompt guard run inside the graph before planner/research.
    """
    _ = request.app
    rt = get_agent_runtime()
    return StreamingResponse(
        aiter_workflow_sse(body, user, runtime=rt),
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.delete("/thread/{thread_id}", status_code=204)
async def delete_workflow_thread(
    thread_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """Remove LangGraph checkpoints for this thread when it belongs to the authenticated user."""
    delete_workflow_thread_for_user(db, user, str(thread_id))
    return Response(status_code=204)
