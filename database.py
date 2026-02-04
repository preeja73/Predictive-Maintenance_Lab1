"""
Database module for the Data Streaming and Visualization Workshop.

Handles connection to Neon (PostgreSQL), schema for robot trait measurements,
and bulk load / query of CSV streaming data into the trait_measurements table.
"""

import os
from typing import Iterable

import pandas as pd
import psycopg2
import sqlalchemy as sa

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Float, DateTime, func


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all ORM models in this module."""

    pass


class TraitMeasurement(Base):
    """
    ORM model for a single robot trait measurement (e.g. current) at a timestamp.

    Stores trait name, 14 axis values (e.g. motor currents), and recorded_at (UTC).
    """

    __tablename__ = "trait_measurements"

    id: Mapped[int] = mapped_column(primary_key=True)
    trait: Mapped[str] = mapped_column(String(100), index=True)

    # Axis 1–14: sensor/axis values (e.g. current per axis); nullable for missing data
    axis_1: Mapped[float | None] = mapped_column(Float)
    axis_2: Mapped[float | None] = mapped_column(Float)
    axis_3: Mapped[float | None] = mapped_column(Float)
    axis_4: Mapped[float | None] = mapped_column(Float)
    axis_5: Mapped[float | None] = mapped_column(Float)
    axis_6: Mapped[float | None] = mapped_column(Float)
    axis_7: Mapped[float | None] = mapped_column(Float)
    axis_8: Mapped[float | None] = mapped_column(Float)
    axis_9: Mapped[float | None] = mapped_column(Float)
    axis_10: Mapped[float | None] = mapped_column(Float)
    axis_11: Mapped[float | None] = mapped_column(Float)
    axis_12: Mapped[float | None] = mapped_column(Float)
    axis_13: Mapped[float | None] = mapped_column(Float)
    axis_14: Mapped[float | None] = mapped_column(Float)

    # Timestamp when the measurement was recorded (UTC)
    recorded_at: Mapped[str] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


def get_database_url() -> str:
    """Read Neon PostgreSQL connection URL from environment (NEON_DATABASE_URL)."""
    db_url = os.getenv("NEON_DATABASE_URL", "").strip()
    if not db_url:
        raise ValueError("NEON_DATABASE_URL is not set.")
    return db_url


def get_engine(db_url: str) -> sa.Engine:
    """Create a SQLAlchemy engine for the given database URL."""
    return sa.create_engine(db_url)


def init_db(engine: sa.Engine) -> None:
    """Create all tables (e.g. trait_measurements) if they do not exist."""
    Base.metadata.create_all(engine)


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map CSV column names to database column names and enforce required columns.

    Expects CSV columns: Trait, Axis #1..Axis #14, Time.
    Returns DataFrame with columns: trait, axis_1..axis_14, recorded_at.
    """
    renamed = {
        "Trait": "trait",
        "Time": "recorded_at",
    }
    for axis in range(1, 15):
        renamed[f"Axis #{axis}"] = f"axis_{axis}"

    df = df.rename(columns=renamed)
    ordered_columns = ["trait"] + [f"axis_{i}" for i in range(1, 15)] + ["recorded_at"]
    expected = set(ordered_columns)
    missing = expected - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing columns: {sorted(missing)}")
    return df[ordered_columns]


def _coerce_rows(df: pd.DataFrame) -> Iterable[dict]:
    """
    Convert normalized DataFrame rows into dicts suitable for bulk insert.

    Parses recorded_at as UTC datetime and axis_* as float; invalid values become None.
    """
    df = df.copy()
    df["recorded_at"] = pd.to_datetime(df["recorded_at"], errors="coerce", utc=True)
    for axis in range(1, 15):
        col = f"axis_{axis}"
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Use None instead of NaN for SQLAlchemy
    df = df.where(pd.notnull(df), None)
    return df.to_dict(orient="records")


def insert_csv_to_database(
    csv_path: str,
    db_url: str | None = None,
    chunk_size: int = 2000,
) -> int:
    """
    Load a CSV of trait measurements and insert all rows into the database.

    Uses NEON_DATABASE_URL if db_url is not provided. Reads the CSV in chunks
    to limit memory use. Creates the table if it does not exist.
    Returns the total number of rows inserted.
    """
    if not db_url:
        db_url = get_database_url()

    engine = get_engine(db_url)
    init_db(engine)

    total_inserted = 0
    with sa.orm.Session(engine) as session:
        for chunk in pd.read_csv(csv_path, chunksize=chunk_size):
            normalized = _normalize_columns(chunk)
            rows = list(_coerce_rows(normalized))
            if not rows:
                continue
            session.bulk_insert_mappings(TraitMeasurement, rows)
            session.commit()
            total_inserted += len(rows)

    return total_inserted

def get_data_from_database(db_url: str | None = None):
    """
    Fetch all TraitMeasurement rows from the database.

    Uses NEON_DATABASE_URL if db_url is not provided.
    Returns a list of TraitMeasurement ORM objects.
    """
    if not db_url:
        db_url = get_database_url()

    engine = get_engine(db_url)
    with sa.orm.Session(engine) as session:
        result = session.query(TraitMeasurement).all()
    return result