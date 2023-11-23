import json
import os
import time
from pathlib import Path

import ipyleaflet
import wikipedia

import geopandas as gpd
import numpy as np
import math

import solara
import requests
from bs4 import BeautifulSoup

HERE = Path(__file__).parent

center_default = (0, 0)
zoom_default = 2

messages = solara.reactive([])
zoom_level = solara.reactive(zoom_default)
center = solara.reactive(center_default)
markers = solara.reactive([])

url = ipyleaflet.basemaps.OpenStreetMap.Mapnik.build_url()
app_style = (HERE / "style.css").read_text()

def compute_zoom_level(gdf):
    xmin, ymin, xmax, ymax = gdf.to_crs('EPSG:32647').total_bounds
    n_tile = 2
    latitude = gdf.to_crs('EPSG:4326').centroid.y.values[0]
    radius = np.max([np.abs(xmax-xmin),np.abs(ymax-ymin)])
    return (np.floor(math.log2((math.cos(latitude *math.pi/180) * 2*math.pi* 6371008*n_tile)/radius)))

def compute_zoom_center(gdf):
    return (gdf.to_crs('EPSG:4326').centroid.y.values[0], gdf.to_crs('EPSG:4326').centroid.x.values[0])

def update_country():
    update_country_gdf =  countries_gdf[countries_gdf.name==country_name.value]
    update_zoom_level = compute_zoom_level(update_country_gdf)
    update_zoom_center = compute_zoom_center(update_country_gdf)
    update_image = scrap_gg_image(country_name.value)
    country_gdf.set(update_country_gdf)
    zoom_level.set(update_zoom_level)
    zoom_center.set(update_zoom_center)
    image.set(update_image)

def scrap_gg_image(keyword):
    params = {"q": 'travel '+keyword,
              "tbm": "isch", 
              "content-type": "image/png",
             }
    html = requests.get("https://www.google.com/search", params=params)
    soup = BeautifulSoup(html.text, 'html.parser')
    image_list = []
    for img in soup.select("img"):
        if 'googlelogo' not in img['src']:
            image_list.append(img['src'])
    return(image_list)


#initial admin_data boundary
countries_gdf = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

countries_name = countries_gdf.name.tolist()
initial_country_name = 'Thailand'
country_name = solara.reactive(initial_country_name)

initial_country_gdf =  countries_gdf[countries_gdf.name==country_name.value]
initial_zoom_level = compute_zoom_level(initial_country_gdf)
initial_zoom_center = compute_zoom_center(initial_country_gdf)
initial_image = scrap_gg_image(country_name.value)
country_gdf = solara.reactive(initial_country_gdf)
zoom_level = solara.reactive(initial_zoom_level)
zoom_center = solara.reactive(initial_zoom_center)
image = solara.reactive(initial_image)

@solara.component
def Map():
    country_layer = ipyleaflet.GeoData.element(geo_dataframe = country_gdf.value,
                   style={'color': 'black', 'fillColor': '#3366cc', 'opacity':0.05, 'weight':1.9, 'dashArray':'2', 'fillOpacity':0.6},
                   hover_style={'fillColor': 'red' , 'fillOpacity': 0.2},
                   name = 'Countries')
    ipyleaflet.Map.element(  # type: ignore
        zoom=zoom_level.value,
        center=zoom_center.value,
        scroll_wheel_zoom=True,
        layers=[
            ipyleaflet.TileLayer.element(url=url),
            country_layer,
        ],
    )

@solara.component
def Page():

    with solara.Column(
        classes=["ui-container"],
        gap="5vh",
    ):
        with solara.Row(justify="space-between"):
            with solara.Row(gap="10px", style={"align-items": "center"}):
                solara.v.Icon(children=["mdi-airplane"], size="36px")
                solara.HTML(
                    tag="h2",
                    unsafe_innerHTML="Travel Assistant",
                    style={"display": "inline-block"},
                )
            with solara.Row(
                gap="30px",
                style={"align-items": "center"},
                classes=["link-container"],
                justify="end",
            ):
                with solara.Row(gap="5px", style={"align-items": "center"}):
                    solara.Text("Source Code:", style="font-weight: bold;")
                    # target="_blank" links are still easiest to do via ipyvuetify
                    with solara.v.Btn(
                        icon=True,
                        tag="a",
                        attributes={
                            "href": "https://github.com/widgetti/wanderlust",
                            "title": "Wanderlust Source Code",
                            "target": "_blank",
                        },
                    ):
                        solara.v.Icon(children=["mdi-github-circle"])
                with solara.Row(gap="5px", style={"align-items": "center"}):
                    solara.Text("Powered by Solara:", style="font-weight: bold;")
                    with solara.v.Btn(
                        icon=True,
                        tag="a",
                        attributes={
                            "href": "https://solara.dev/",
                            "title": "Solara",
                            "target": "_blank",
                        },
                    ):
                        solara.HTML(
                            tag="img",
                            attributes={
                                "src": "https://solara.dev/static/public/logo.svg",
                                "width": "24px",
                            },
                        )
                    with solara.v.Btn(
                        icon=True,
                        tag="a",
                        attributes={
                            "href": "https://github.com/widgetti/solara",
                            "title": "Solara Source Code",
                            "target": "_blank",
                        },
                    ):
                        solara.v.Icon(children=["mdi-github-circle"])
                        
        with solara.Columns([1, 2, 2]):
            with solara.Column():
                solara.Select(label="Select Country", value=country_name, values=countries_name, on_value=update_country())
                try:
                    wiki_keyword = wikipedia.search( country_name.value+'Travel', results=1)
                    solara.Markdown(wikipedia.summary(wiki_keyword, sentences=4))
                except:
                    print("wiki error")

            if image.value:
                with solara.GridFixed(columns=4, align_items="end", justify_items="stretch"):
                    for img in image.value:
                        solara.Image(img, width='300')

            with solara.Column(classes=["map-container"]):
                Map()

        solara.Style(app_style)
