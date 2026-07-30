# -*- coding: utf-8 -*-
"""Precomputa dos insumos para el mapa realista del simulador NetLogo:

1) netlogo_mapa_upz.csv  -> rasteriza los poligonos REALES de las 112 UPZ (IndUPZ.gpkg)
   sobre la MISMA grilla de patches que arma el simulador (misma proyeccion, mismo centro,
   misma escala), de modo que cada patch queda etiquetado con la UPZ real que lo contiene.
   Reemplaza el mosaico Voronoi (formas arbitrarias) por las formas reales, alineadas 112/112.

2) netlogo_ase_upz.csv   -> asignacion oficial ASE -> localidad -> UPZ (Nuevo Esquema de Aseo,
   UAESP 2018): 5 areas de servicio exclusivo. Usada para dar territorio real a cada camion.

Ejecutar:  python -m abm.preparar_mapa_netlogo
"""
import csv
from pathlib import Path
import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point

PROY = Path(__file__).resolve().parent.parent
GPKG = PROY / "data" / "raw" / "Demograficas" / "IndUPZ.gpkg"
ZONAS = PROY / "abm" / "netlogo" / "datos" / "netlogo_zonas.csv"
OUT = PROY / "abm" / "netlogo" / "datos"

# Debe coincidir con el codigo NetLogo (setup): escala-mapa y margen-mundo.
ESCALA = 1.75
MARGEN = 6
METROS_POR_PATCH_BASE = 150.0   # export original: 1 unidad de centroide = 150 m

# Asignacion oficial ASE -> codigo de localidad (UAESP, Nuevo Esquema de Aseo 2018).
ASE_POR_LOCALIDAD = {
    1: "ASE 1 Promoambiental", 2: "ASE 1 Promoambiental", 3: "ASE 1 Promoambiental",
    4: "ASE 1 Promoambiental", 5: "ASE 1 Promoambiental", 17: "ASE 1 Promoambiental",
    6: "ASE 2 LIME", 15: "ASE 2 LIME", 14: "ASE 2 LIME",
    16: "ASE 2 LIME", 18: "ASE 2 LIME", 19: "ASE 2 LIME",
    7: "ASE 3 Ciudad Limpia", 8: "ASE 3 Ciudad Limpia",
    9: "ASE 4 Bogotá Limpia", 10: "ASE 4 Bogotá Limpia",
    11: "ASE 5 Área Limpia", 12: "ASE 5 Área Limpia", 13: "ASE 5 Área Limpia",
}
ASE_NUM = {"ASE 1 Promoambiental": 1, "ASE 2 LIME": 2, "ASE 3 Ciudad Limpia": 3,
           "ASE 4 Bogotá Limpia": 4, "ASE 5 Área Limpia": 5}


def main():
    z = [r for r in csv.DictReader(open(ZONAS, encoding="utf-8-sig")) if r["anio"] == "2024"]
    loc_por_upz = {int(r["codigo_upz"]): int(r["codigo_localidad"]) for r in z}
    cent_csv = {int(r["codigo_upz"]): (float(r["x_centroide"]), float(r["y_centroide"])) for r in z}

    g = gpd.read_file(GPKG).to_crs("EPSG:3116")
    g["CODIGO_UPZ"] = g["CODIGO_UPZ"].astype(int)
    g = g[g["CODIGO_UPZ"].isin(cent_csv)].reset_index(drop=True)
    cent = g.geometry.centroid

    # Resolver cx, cy exactos para que los centroides reales caigan donde el CSV los tiene:
    # x_centroide = (x_m - cx) / 150  ->  cx = x_m - x_centroide*150
    cxs, cys = [], []
    for _, row in g.iterrows():
        c = int(row["CODIGO_UPZ"])
        cc = row.geometry.centroid
        cxs.append(cc.x - cent_csv[c][0] * METROS_POR_PATCH_BASE)
        cys.append(cc.y - cent_csv[c][1] * METROS_POR_PATCH_BASE)
    cx, cy = float(np.median(cxs)), float(np.median(cys))

    # Bounds del mundo, replicando NetLogo (centroides/escala, +/- margen).
    xs = [v[0] / ESCALA for v in cent_csv.values()]
    ys = [v[1] / ESCALA for v in cent_csv.values()]
    min_x, max_x = int(np.floor(min(xs))) - MARGEN, int(np.ceil(max(xs))) + MARGEN
    min_y, max_y = int(np.floor(min(ys))) - MARGEN, int(np.ceil(max(ys))) + MARGEN

    # Un punto por patch (centro), en metros EPSG:3116.
    metros_por_patch = METROS_POR_PATCH_BASE * ESCALA  # 262.5 m
    filas_pts = []
    for px in range(min_x, max_x + 1):
        for py in range(min_y, max_y + 1):
            xm = px * metros_por_patch + cx
            ym = py * metros_por_patch + cy
            filas_pts.append((px, py, xm, ym))
    pts = gpd.GeoDataFrame(
        {"px": [f[0] for f in filas_pts], "py": [f[1] for f in filas_pts]},
        geometry=[Point(f[2], f[3]) for f in filas_pts], crs="EPSG:3116",
    )
    joined = gpd.sjoin(pts, g[["CODIGO_UPZ", "geometry"]], how="inner", predicate="within")
    joined = joined.drop_duplicates(subset=["px", "py"])

    out1 = OUT / "netlogo_mapa_upz.csv"
    with open(out1, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["px", "py", "codigo_upz", "codigo_localidad"])
        for _, r in joined.iterrows():
            upz = int(r["CODIGO_UPZ"])
            w.writerow([int(r["px"]), int(r["py"]), upz, loc_por_upz.get(upz, -1)])
    print(f"  {out1.name}: {len(joined)} patches etiquetados con UPZ real "
          f"({joined['CODIGO_UPZ'].nunique()} UPZ)")

    out2 = OUT / "netlogo_ase_upz.csv"
    with open(out2, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["codigo_upz", "codigo_localidad", "ase_num", "ase_nombre"])
        for upz, loc in sorted(loc_por_upz.items()):
            nombre = ASE_POR_LOCALIDAD.get(loc, "ASE 1 Promoambiental")
            w.writerow([upz, loc, ASE_NUM[nombre], nombre])
    print(f"  {out2.name}: {len(loc_por_upz)} UPZ asignadas a 5 ASE")
    print(f"  Mundo: x[{min_x},{max_x}] y[{min_y},{max_y}]  cx={cx:.1f} cy={cy:.1f}")


if __name__ == "__main__":
    main()
