"""Authenticated streaming entrypoint for the career LangGraph."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.deps import get_current_user
from app.core.agent_runtime import get_agent_runtime
from app.models.user import User
from app.schema.workflow import WorkflowStreamRequest
from app.services.workflow_stream import iter_workflow_sse

router = APIRouter()


@router.post("/stream")
def post_workflow_stream(
    body: WorkflowStreamRequest,
    user: Annotated[User, Depends(get_current_user)],
) -> StreamingResponse:
    """
    Run one workflow turn; SSE ``data:`` lines carry each node's ``patch`` until ``event: done``.
    Input size + prompt guard run inside the graph before planner/research.
    """
    rt = get_agent_runtime()
    return StreamingResponse(
        iter_workflow_sse(body, user, runtime=rt),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
