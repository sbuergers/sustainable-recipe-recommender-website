from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.models import HoverTool
import numpy as np


def make_plot(title, hist, edges, x):
    p = figure(title=title, tools='', background_fill_color="#fafafa",
               width=150, height=100, sizing_mode='scale_width',
               x_range=(-1.55, 2.55))
    p.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:],
           fill_color="black", line_color="white", alpha=0.5)
    p.line([x, x+0.00001], [0, max(hist)], line_color="black", line_width=1)
    p.y_range.start = 0
    p.xaxis.axis_label = 'Emissions log10(kg CO2)'
    p.yaxis.axis_label = 'Density'
    p.grid.grid_line_color = "white"

    hover = HoverTool()
    p.add_tools(hover)
    return p


def make_histogram(recipeID, df):
    hist, edges = np.histogram(df['ghg_log10'], density=True, bins=300)
    p = make_plot("Emissions", hist, edges, df.loc[recipeID, 'ghg_log10'])
    script, div = components(p)
    return script, div


# eof
