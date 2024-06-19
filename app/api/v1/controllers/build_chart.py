import plotly.graph_objects as go
import plotly.io as pio
from app.utils.logger import Logger

logger = Logger("controller/build_chart", log_file="build-chart.log")

class PlotlyChart:
    def __init__(self,
                 template: str,
                 title: str,
                 xlabel: str = "x",
                 ylabel: str = "y",
                 width: int = 1000,
                 height: int = 800,
                 chart_info: list = None,
                 ) -> None:

        self.template = template
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.width = width
        self.height = height
        self.chart_info = chart_info

    def build_chart(self):
        import numpy as np
        fig = go.Figure()

        min_x, max_x = 0, 0
        min_y, max_y = 0, 0


        for chart in self.chart_info:

            x_local_vars = {}
            x_global_vars = {
                "np": np,
            }
            try:
                exec(chart.x_data, x_global_vars, x_local_vars)
                x = x_local_vars['x']
            except Exception as e:
                logger.error(f"Error in exec x_data: {e}")

            y_local_vars = {}
            y_global_vars = {
                "np": np,
                "x": x
            }
            try:
                exec(chart.y_data, y_global_vars, y_local_vars)
                y = y_local_vars['y']
            except Exception as e:
                logger.error(f"Error in exec y_data: {e}")

            fig.add_trace(go.Scatter(x=x, y=y, mode='lines', name=chart.label))

            min_x = min(min_x, min(x))
            max_x = max(max_x, max(x))
            min_y = min(min_y, min(y))
            max_y = max(max_y, max(y))

        fig.update_layout(
            title=self.title,
            xaxis_title=self.xlabel,
            yaxis_title=self.ylabel,
            template=self.template,
            width=self.width,
            height=self.height,
            margin=dict(l=50, r=50, b=50, t=50, pad=4), 
            xaxis=dict(range=[min_x,  max_x]),
            yaxis=dict(range=[min_y,  max_y]),
            legend=dict(x=0, y=1, traceorder='normal')
        )
        fig_json = pio.to_json(fig)
        return fig_json
