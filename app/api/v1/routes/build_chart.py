from fastapi import APIRouter, status, HTTPException
from app.api.v1.controllers.build_chart import PlotlyChart

from app.schemas.chart import (
    PlotCharts,
    ResponseModel
)

router = APIRouter()

@router.post("/build_chart")
async def plot_chart(plot_chart_request: PlotCharts):
    try:
        fig_info = plot_chart_request.figure_info
        chart_info = plot_chart_request.chart_info

        plot_act_func = PlotlyChart(template=fig_info.template,
                                      title=fig_info.title,
                                      xlabel=fig_info.xlabel,
                                      ylabel=fig_info.ylabel,
                                      chart_info=chart_info)
        fig_json = plot_act_func.build_chart()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"{str(e)}")

    return ResponseModel(
        status=status.HTTP_200_OK,
        data=fig_json,
        message="success"
    )
