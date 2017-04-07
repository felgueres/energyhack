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

axis_map = {
    "Market Size in kW": "underserved_mkt_size_kW",
    "Market Size in USD": "underserved_mkt_size_USD",
    "Income per Capita (yr)": "income_per_capita_yr",
    "Mobile Phones per Houshold": "mobile_phone_per_HH",
    "Population Density per km2": "density_per_km2",
    "Car Access per Household": "car_access_per_HH",
    "People to Gain Access per Usd":"access_per_capita_per_usd",
    "Government Revenue":"gov_revenue"
}

desc = Div(text=open(join(dirname(__file__), "description.html")).read(), width=800)

# Create Input controls
min_market_size_kW = Slider(title="Minimum market size (KW)", value=data.underserved_mkt_size_kW.mean(), start=0, end=450, step=10)
min_income_per_capita = Slider(title="Minimum Income per Capita (K)", start=0, end=950, value=data.income_per_capita_yr.mean(), step=50)
min_market_size_USD = Slider(title="Minimum Market size (USD)", start=0, end=2700, value=data.underserved_mkt_size_USD.mean(), step=10)
gov_revenue = Slider(title="Government Revenue (K)", start=0, end=175000, value=data.gov_revenue.mean(), step=10000)
access_to_comm = Slider(title="Communication Access (Phones/Household)", start=0, end=1, value=data.mobile_phone_per_HH.mean(), step=0.01)
Access_by_car = Slider(title="Communication Access (Cars/Household)", start = 0, end=0.36, value=data.car_access_per_HH.mean(), step=0.0001 )

x_axis = Select(title="X Axis", options=sorted(axis_map.keys()), value="Market Size in kW")
y_axis = Select(title="Y Axis", options=sorted(axis_map.keys()), value="Income per Capita (yr)")

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

p.circle(x="x", y="y", source=source, size='blob_size', color="color", line_color=None, fill_alpha=0.5)

def select():

    selected = data.ix[
                       (data.underserved_mkt_size_kW >= min_market_size_kW.value) &
                       (data.underserved_mkt_size_USD >= min_market_size_USD.value)&
                       (data.income_per_capita_yr >= min_income_per_capita.value) &
                       (data.gov_revenue >= gov_revenue.value)&
                       (data.mobile_phone_per_HH >= access_to_comm.value)&
                       (data.car_access_per_HH >= Access_by_car.value)].copy()

    return selected

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

controls = [min_market_size_kW, min_market_size_USD, min_income_per_capita, gov_revenue, access_to_comm,Access_by_car, x_axis, y_axis]

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
