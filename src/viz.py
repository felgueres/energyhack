from os.path import dirname, join
import pandas as pd
import numpy as np
import pandas.io.sql as psql
import sqlite3 as sql

from bokeh.plotting import figure
from bokeh.layouts import layout, widgetbox
from bokeh.models import ColumnDataSource, HoverTool, Div
from bokeh.models.widgets import Slider, Select, TextInput
from bokeh.io import curdoc
from bokeh.sampledata.movies_data import movie_path
from bokeh.palettes import Dark2_5 as palette
import itertools

data = pd.read_pickle('myanmar_data.pickle')
data.dropna(inplace = True)

#FORMATTING
# movies["color"] = np.where(movies["Oscars"] > 0, "orange", "grey")
# movies["alpha"] = np.where(movies["Oscars"] > 0, 0.9, 0.25)
# movies.fillna(0, inplace=True)  # just replace missing values with zero
# movies["revenue"] = movies.BoxOffice.apply(lambda x: '{:,d}'.format(int(x)))

#DONT KNOW WHAT THIS IS.
# with open(join(dirname(__file__), "razzies-clean.csv")) as f:
#     razzies = f.read().splitlines()
# movies.loc[movies.imdbID.isin(razzies), "color"] = "purple"
# movies.loc[movies.imdbID.isin(razzies), "alpha"] = 0.9


# axis_map = {
#     "Tomato Meter": "Meter",
#     "Numeric Rating": "numericRating",
#     "Number of Reviews": "Reviews",
#     "Box Office (dollars)": "BoxOffice",
#     "Length (minutes)": "Runtime",
#     "Year": "Year",
# }

axis_map = {
    "Market Size in kW": "underserved_mkt_size_kW",
    "Market Size in USD": "underserved_mkt_size_USD",
    "Income per Capita (yr)": "income_per_capita_yr",
    "Mobile Phones per Houshold": "mobile_phone_per_HH",
    "Population Density per km2": "density_per_km2",
    "Car Access per Household": "car_access_per_HH",
}

desc = Div(text=open(join(dirname(__file__), "description.html")).read(), width=800)

# Create Input controls
min_market_size_kW = Slider(title="Minimum market size (KW)", value=data.underserved_mkt_size_kW.mean(), start=0, end=450, step=10)
min_income_per_capita = Slider(title="Minimum Income per Capita (K)", start=0, end=950, value=data.income_per_capita_yr.mean(), step=50)
min_market_size_USD = Slider(title="Minimum Market size (USD)", start=0, end=2700000, value=data.underserved_mkt_size_USD.mean(), step=10000)
gov_revenue = Slider(title="Government Revenue (K)", start=0, end=175000, value=data.gov_revenue.mean(), step=10000)
access_to_comm = Slider(title="Communication Access (Phones/Household)", start=0, end=1, value=data.mobile_phone_per_HH.mean(), step=0.01)

# reviews = Slider(title="Minimum number of reviews", value=80, start=10, end=300, step=10)
# min_year = Slider(title="Year released", start=1940, end=2014, value=1970, step=1)
# max_year = Slider(title="End Year released", start=1940, end=2014, value=2014, step=1)
# oscars = Slider(title="Minimum number of Oscar wins", start=0, end=4, value=0, step=1)
# boxoffice = Slider(title="Dollars at Box Office (millions)", start=0, end=800, value=0, step=1)

#This could be used for filtering
# genre = Select(title="Genre", value="All",
#                options=open(join(dirname(__file__), 'genres.txt')).read().split())

# director = TextInput(title="Director name contains")
# cast = TextInput(title="Cast names contains")

x_axis = Select(title="X Axis", options=sorted(axis_map.keys()), value="Market Size in kW")
y_axis = Select(title="Y Axis", options=sorted(axis_map.keys()), value="Income per Capita (yr)")

# Create Column Data Source that will be used by the plot
# source = ColumnDataSource(data=dict(x=[],
#                                     y=[],
#                                     color=[],
#                                     title=[],
#                                     year=[],
#                                     revenue=[],
#                                     alpha=[]))

source = ColumnDataSource(data=dict(x=[],
                                    y=[],
                                    # color=[],
                                    State = [],
                                    District =[],
                                    Township=[],
                                    Number_of_HH_wo_Electricity=[],
                                    Market_Size_USD=[],
                                    color=[],
                                    blob_size=[]))
hover = HoverTool(tooltips=[
    ("State", "@State"),
    ("District", "@District"),
    ("Township", "@Township"),
    ("# Unelectrified Households", "@Number_of_HH_wo_Electricity"),
    ("Market Size (USD)", "@Market_Size_USD")
])

p = figure(plot_height=600, plot_width=700, title="", toolbar_location=None, tools=[hover])
# p.circle(x="x", y="y", source=source, size=7, line_color=None)

p.circle(x="x", y="y", source=source, size='blob_size', color="color", line_color=None, fill_alpha=0.5)

def select():

    selected = data.ix[
                       (data.underserved_mkt_size_kW >= min_market_size_kW.value) &
                       (data.underserved_mkt_size_USD >= min_market_size_USD.value)&
                       (data.income_per_capita_yr >= min_income_per_capita.value) &
                       (data.gov_revenue >= gov_revenue.value)&
                       (data.mobile_phone_per_HH >= access_to_comm.value)
                        ].copy()

    return selected

# def select_movies():
#     genre_val = genre.value
#     director_val = director.value.strip()
#     cast_val = cast.value.strip()
#     selected = movies[
#         (movies.Reviews >= reviews.value) &
#         (movies.BoxOffice >= (boxoffice.value * 1e6)) &
#         (movies.Year >= min_year.value) &
#         (movies.Year <= max_year.value) &
#         (movies.Oscars >= oscars.value)
#     ]
#     if (genre_val != "All"):
#         selected = selected[selected.Genre.str.contains(genre_val)==True]
#     if (director_val != ""):
#         selected = selected[selected.Director.str.contains(director_val)==True]
#     if (cast_val != ""):
#         selected = selected[selected.Cast.str.contains(cast_val)==True]
#     return selected

def update():

    df = select()
    x_name = axis_map[x_axis.value]
    y_name = axis_map[y_axis.value]

    p.xaxis.axis_label = x_axis.value
    p.yaxis.axis_label = y_axis.value
    p.title.text = "%d Townships selected" % len(df)
    source.data = dict(
        x=df[x_name],
        y=df[y_name],
        # color=df["color"],
        State=df['st_name'],
        Township=df["name_ts"],
        District=df['name_dt'],
        Number_of_HH_wo_Electricity=df["underserved_HH"],
        Market_Size_USD=df["underserved_mkt_size_USD"],
        Market_Size_kW=df["underserved_mkt_size_kW"],
        color = df['color'],
        blob_size = df['blob_size'])

# def update():
#     df = select_movies()
#     x_name = axis_map[x_axis.value]
#     y_name = axis_map[y_axis.value]
#
#     p.xaxis.axis_label = x_axis.value
#     p.yaxis.axis_label = y_axis.value
#     p.title.text = "%d movies selected" % len(df)
#     source.data = dict(
#         x=df[x_name],
#         y=df[y_name],
#         color=df["color"],
#         title=df["Title"],
#         year=df["Year"],
#         revenue=df["revenue"],
#         alpha=df["alpha"],
#     )

controls = [min_market_size_kW, min_market_size_USD, min_income_per_capita, gov_revenue, access_to_comm, x_axis, y_axis]

# controls = [reviews, boxoffice, genre, min_year, max_year, oscars, director, cast, x_axis, y_axis]

for control in controls:
    control.on_change('value', lambda attr, old, new: update())

sizing_mode = 'fixed'  # 'scale_width' also looks nice with this example

inputs = widgetbox(*controls, sizing_mode=sizing_mode)
l = layout([
    [desc],
    [inputs, p],
], sizing_mode=sizing_mode)

update()  # initial load of the data

curdoc().add_root(l)
curdoc().title = "Solar Development in Myanmar"
