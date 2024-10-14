import geopandas as gpd
import pandas as pd  
import os
import unicodedata
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

def normalize_region_name(name):
    name = ' '.join(name.strip().split())
    name = unicodedata.normalize('NFKD', name)
    return name

geojson_folder = 'Regions'

gdf_list = []

simplify_tolerance = 0.00001

# Для папки Regions с https://github.com/timurkanaz/Russia_geojson_OSM также я поправил некоторые названия в ручную
for root, dirs, files in os.walk(geojson_folder):
    for filename in files:
        if filename.endswith('.geojson'):
            filepath = os.path.join(root, filename)
            try:
                gdf = gpd.read_file(filepath)
                gdf['geometry'] = gdf['geometry'].simplify(tolerance=simplify_tolerance, preserve_topology=True)
                region_name = filename.split('_')[0].strip()
                gdf['region_name'] = region_name
                gdf_list.append(gdf)
            except Exception as e:
                print(f"Ошибка при обработке файла {filepath}: {e}")

regions = gpd.GeoDataFrame(pd.concat(gdf_list, ignore_index=True))

# Загружаем данные из Приложение к сборнику Демографическому Ежегоднику России 2023 
# (Информация в разрезе субъектов России) Раздел 4.5.
# Его мануально я тоже подредачил оставил только колонки на 100
data = pd.read_csv('Pril_Demogr_ejegodnik_2023.csv', sep=';')
data['region_name'] = data['region_name'].apply(normalize_region_name)

data['region_name'] = data['region_name'].str.strip()
regions['region_name'] = regions['region_name'].str.strip()

merged = regions.merge(data, on='region_name', how='inner')

print(f"\Количество регионов после объединения: {len(merged)}")

# c 2014 по 2023
years = list(range(2014, 2023))


fig, ax = plt.subplots(1, 1, figsize=(9, 6))

vmin = merged[[str(year) for year in years]].min().min()
vmax = merged[[str(year) for year in years]].max().max()

sm = plt.cm.ScalarMappable(cmap='OrRd', norm=plt.Normalize(vmin=vmin, vmax=vmax))
sm._A = []
cbar = fig.colorbar(sm, ax=ax, orientation='horizontal', pad=0.05) 
cbar.set_label('Число абортов на 100 родов среди Женщин (15-49 лет) ©KirilHSE', fontsize=12)

def update(year):
    ax.clear()
    merged.plot(column=str(year), ax=ax, cmap='OrRd', vmin=vmin, vmax=vmax,
                missing_kwds={"color": "lightgrey", "label": "Нет данных"})
    ax.set_title(f'\nДинамика числа абортов на 100 родов по регионам России ({year} год)', fontsize=13,pad=-10)
    ax.axis('off')

plt.tight_layout()

ani = FuncAnimation(fig, update, frames=years, repeat=False)

ani.save('abortions_dynamic_itog.gif', writer='pillow', fps=1)
