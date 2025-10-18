"""Example demonstrating artifact hierarchical storage system.

This example shows how to use artifacts for hierarchical data storage,
commonly used for ML models, datasets, experimental results, and document versioning.

Run with: fastapi dev examples/artifact_storage_api.py
"""

from __future__ import annotations

from typing import NotRequired, TypedDict

from fastapi import FastAPI
from servicekit import Database
from ulid import ULID

from servicekit.artifact import (
    ArtifactHierarchy,
    ArtifactIn,
    ArtifactManager,
    ArtifactOut,
    ArtifactRepository,
    ArtifactRouter,
)
from servicekit.api import BaseServiceBuilder, ServiceInfo


class ArtifactNodeSeed(TypedDict):
    """TypedDict for seeding artifact hierarchies with parent-child relationships."""

    id: str
    data: dict[str, object]
    children: NotRequired[list["ArtifactNodeSeed"]]


# Define artifact hierarchy for document versioning
DOCUMENT_HIERARCHY = ArtifactHierarchy(
    name="document_versions",
    level_labels={0: "project", 1: "document", 2: "version"},
)

# Seed data: project -> documents -> versions
SEED_DATA: tuple[ArtifactNodeSeed, ...] = (
    {
        "id": "01JSEED00PROJECT00000001",
        "data": {"name": "Product Requirements", "owner": "Engineering Team"},
        "children": [
            {
                "id": "01JSEED00DOC00000000001",
                "data": {"title": "API Specification", "format": "markdown"},
                "children": [
                    {
                        "id": "01JSEED00VER00000000001",
                        "data": {"version": "1.0", "status": "draft", "content": "# API v1.0\nInitial draft"},
                    },
                    {
                        "id": "01JSEED00VER00000000002",
                        "data": {"version": "1.1", "status": "review", "content": "# API v1.1\nUpdated endpoints"},
                    },
                ],
            },
            {
                "id": "01JSEED00DOC00000000002",
                "data": {"title": "Database Schema", "format": "sql"},
                "children": [
                    {
                        "id": "01JSEED00VER00000000003",
                        "data": {"version": "1.0", "status": "published", "schema": "CREATE TABLE users..."},
                    },
                ],
            },
        ],
    },
)


async def create_artifact_tree(
    manager: ArtifactManager,
    seed: ArtifactNodeSeed,
    parent_id: ULID | None = None,
) -> ULID:
    """Recursively creates artifact tree from seed data with parent-child relationships."""
    artifact_id = ULID.from_str(seed["id"])
    artifact = await manager.save(
        ArtifactIn(
            id=artifact_id,
            parent_id=parent_id,
            data=seed["data"],
        )
    )

    for child in seed.get("children", []) or []:
        await create_artifact_tree(manager, child, parent_id=artifact.id)

    return artifact.id


async def seed_demo_data(app: FastAPI) -> None:
    """Startup hook that seeds the database with demo artifact hierarchies."""
    database: Database | None = getattr(app.state, "database", None)
    if database is None:
        return

    async with database.session() as session:
        artifact_repo = ArtifactRepository(session)
        artifact_manager = ArtifactManager(artifact_repo, hierarchy=DOCUMENT_HIERARCHY)

        # Clear existing data
        await artifact_manager.delete_all()

        # Seed hierarchical data
        for project_seed in SEED_DATA:
            await create_artifact_tree(artifact_manager, project_seed)

        print("✓ Seeded artifact hierarchy: projects → documents → versions")


# Build service with artifact storage
info = ServiceInfo(
    display_name="Artifact Storage Service",
    summary="Hierarchical artifact storage demonstration",
    description="Example service showing artifact trees for document versioning",
)

app: FastAPI = (
    BaseServiceBuilder(info=info)
    .with_landing_page()
    .with_health()
    .with_system()
    .on_startup(seed_demo_data)
    .build()
)

# Manually add artifact router (servicekit doesn't have .with_artifacts())
from fastapi import Depends
from servicekit.api.dependencies import get_session
from sqlalchemy.ext.asyncio import AsyncSession


async def get_artifact_manager(session: AsyncSession = Depends(get_session)) -> ArtifactManager:
    """Provide artifact manager for dependency injection."""
    return ArtifactManager(ArtifactRepository(session), hierarchy=DOCUMENT_HIERARCHY)


artifact_router = ArtifactRouter.create(
    prefix="/api/v1/artifacts",
    tags=["Artifacts"],
    manager_factory=get_artifact_manager,
    entity_in_type=ArtifactIn,
    entity_out_type=ArtifactOut,
)
app.include_router(artifact_router)


if __name__ == "__main__":
    from servicekit.api.utilities import run_app

    run_app("artifact_storage_api:app")
