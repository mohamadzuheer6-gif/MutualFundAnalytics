"""Chart utility functions (stubbed for future layout construction)."""
import plotly.graph_objects as go
import pandas as pd

def create_blank_chart(title: str) -> go.Figure:
    """Create a styled empty chart placeholder.
    
    Args:
        title (str): Title of the chart.
        
    Returns:
        go.Figure: A plotly figure.
    """
    fig = go.Figure()
    fig.update_layout(
        title=title,
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[{
            "text": "No data available",
            "xref": "paper",
            "yref": "paper",
            "showarrow": False,
            "font": {"size": 20}
        }]
    )
    return fig
