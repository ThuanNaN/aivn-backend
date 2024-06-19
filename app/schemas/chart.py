from typing import Any, Literal, List
from pydantic import BaseModel

class FigureInfo(BaseModel):
    template: Literal["plotly", "plotly_white", "plotly_dark",
                      "ggplot2", "seaborn", "simple_white", "none"]
    title: str
    xlabel: str
    ylabel: str


class ChartInfo(BaseModel):
    x_data: str
    y_data: str
    label: str


class PlotCharts(BaseModel):
    figure_info: FigureInfo
    chart_info: List[ChartInfo]


class ResponseModel(BaseModel):
    status: int
    data: Any
    message: str