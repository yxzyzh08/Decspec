"""
DevSpec Database Models - SQLModel 数据模型定义。

定义 SpecGraph 的 Node 和 Edge 表结构，用于关系查询和反向索引。
"""

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from sqlmodel import Field, Relationship, SQLModel, create_engine, Session


class NodeType(str, Enum):
    """节点类型枚举。"""
    PRODUCT = "Product"
    FEATURE = "Feature"
    SUBSTRATE = "Substrate"
    API = "API"
    COMPONENT = "Component"
    DESIGN = "Design"
    DATA_MODEL = "DataModel"


class EdgeType(str, Enum):
    """边类型枚举。"""
    DEPENDS_ON = "DEPENDS_ON"
    REALIZED_BY = "REALIZED_BY"
    BELONGS_TO = "BELONGS_TO"
    REFERENCES = "REFERENCES"


class Node(SQLModel, table=True):
    """
    节点表 - 存储 YAML 文件解析后的实体。

    Attributes:
        id: 节点唯一标识符 (来自 meta.id)
        type: 节点类型 (Feature, API, Component 等)
        domain: 所属领域 (来自 meta.domain)
        file_path: 源 YAML 文件相对路径
        content: 完整 YAML 内容的 JSON 序列化
        search_text: 用于全文搜索的文本
        created_at: 创建时间
        updated_at: 更新时间
    """
    __tablename__ = "nodes"

    id: str = Field(primary_key=True)
    type: str = Field(index=True)
    domain: str | None = Field(default=None, index=True)
    file_path: str = Field(index=True)
    content: str = Field(default="{}")
    search_text: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    outgoing_edges: list["Edge"] = Relationship(
        back_populates="source_node",
        sa_relationship_kwargs={"foreign_keys": "Edge.source_id"},
    )
    incoming_edges: list["Edge"] = Relationship(
        back_populates="target_node",
        sa_relationship_kwargs={"foreign_keys": "Edge.target_id"},
    )

    def get_content(self) -> dict[str, Any]:
        """反序列化 content 字段。"""
        return json.loads(self.content)

    def set_content(self, data: dict[str, Any]) -> None:
        """序列化并设置 content 字段。"""
        self.content = json.dumps(data, ensure_ascii=False)


class Edge(SQLModel, table=True):
    """
    边表 - 存储节点之间的关系。

    Attributes:
        id: 自增主键
        source_id: 源节点 ID
        target_id: 目标节点 ID
        type: 边类型 (DEPENDS_ON, REALIZED_BY 等)
        created_at: 创建时间
    """
    __tablename__ = "edges"

    id: int | None = Field(default=None, primary_key=True)
    source_id: str = Field(foreign_key="nodes.id", index=True)
    target_id: str = Field(foreign_key="nodes.id", index=True)
    type: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    source_node: Node | None = Relationship(
        back_populates="outgoing_edges",
        sa_relationship_kwargs={"foreign_keys": "[Edge.source_id]"},
    )
    target_node: Node | None = Relationship(
        back_populates="incoming_edges",
        sa_relationship_kwargs={"foreign_keys": "[Edge.target_id]"},
    )


def get_db_path(spec_root: Path) -> Path:
    """
    获取数据库文件路径。

    Args:
        spec_root: .specgraph 目录路径

    Returns:
        数据库文件路径
    """
    return spec_root / ".runtime" / "index.db"


def init_database(spec_root: Path) -> Session:
    """
    初始化数据库，创建表结构。

    Args:
        spec_root: .specgraph 目录路径

    Returns:
        数据库会话
    """
    runtime_dir = spec_root / ".runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)

    db_path = get_db_path(spec_root)
    engine = create_engine(f"sqlite:///{db_path}", echo=False)

    SQLModel.metadata.create_all(engine)

    return Session(engine)


def get_session(spec_root: Path) -> Session:
    """
    获取数据库会话。

    Args:
        spec_root: .specgraph 目录路径

    Returns:
        数据库会话
    """
    db_path = get_db_path(spec_root)
    if not db_path.exists():
        return init_database(spec_root)

    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    return Session(engine)
