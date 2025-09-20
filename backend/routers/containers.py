from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import aliased
from pydantic import BaseModel

from database import get_db_session
from db_models import DockerEventsModel


# Pydantic response model
class ContainerResponse(BaseModel):
    container: str
    last_event_time: str
    last_action: str
    status: str


# Create router
router = APIRouter()


def compute_status(last_action: str) -> str:
    """
    Compute container status based on the last action.
    
    Args:
        last_action: The most recent action from docker events
        
    Returns:
        Status string: "running", "stopped", or "unknown"
    """
    if not last_action:
        return "unknown"
    
    action_lower = last_action.lower().strip()
    
    if action_lower == "start":
        return "running"
    elif action_lower in ["stop", "die"]:
        return "stopped"
    else:
        return "unknown"


@router.get("/containers", response_model=List[ContainerResponse])
async def get_containers(
    db: AsyncSession = Depends(get_db_session)
) -> List[ContainerResponse]:
    """
    GET /containers
    
    Returns a list of containers with their latest event information.
    Groups docker_events by container and fetches:
    - container name
    - last_event_time (MAX timestamp)
    - last_action (most recent action)
    - status (computed from last_action)
    """
    try:
        # Create a subquery to find the latest timestamp for each container
        latest_timestamp_subquery = (
            select(
                DockerEventsModel.container,
                func.max(DockerEventsModel.timestamp).label('max_timestamp')
            )
            .where(DockerEventsModel.container.isnot(None))
            .group_by(DockerEventsModel.container)
            .subquery()
        )
        
        # Join with the main table to get the full record for the latest timestamp
        # This handles cases where multiple events might have the same timestamp
        query = (
            select(DockerEventsModel)
            .join(
                latest_timestamp_subquery,
                (DockerEventsModel.container == latest_timestamp_subquery.c.container) &
                (DockerEventsModel.timestamp == latest_timestamp_subquery.c.max_timestamp)
            )
            .order_by(DockerEventsModel.container)
        )
        
        result = await db.execute(query)
        events = result.scalars().all()
        
        # Convert to response models and compute status
        containers_list = []
        for event in events:
            if event.container:  # Skip events without container names
                status = compute_status(event.action)
                containers_list.append(ContainerResponse(
                    container=event.container,
                    last_event_time=event.timestamp.isoformat(),
                    last_action=event.action or "",
                    status=status
                ))
        
        return containers_list
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving containers: {str(e)}")