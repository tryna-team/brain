from __future__ import annotations

from datetime import date, time

from pydantic import BaseModel, ConfigDict, Field


class OcrEventExtraction(BaseModel):
    """OCR 텍스트에서 추출한 일정 정보."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(
        default=None,
        description="행사 또는 일정 제목",
    )

    start_date: date | None = Field(
        default=None,
        description="일정 시작 날짜",
    )

    end_date: date | None = Field(
        default=None,
        description="일정 종료 날짜",
    )

    start_time: time | None = Field(
        default=None,
        description="일정 시작 시간",
    )

    end_time: time | None = Field(
        default=None,
        description="일정 종료 시간",
    )

    location: str | None = Field(
        default=None,
        description="행사 장소",
    )

    description: str | None = Field(
        default=None,
        description="일정 관련 추가 정보",
    )