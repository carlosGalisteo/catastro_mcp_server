# DEPENDENCIAS --------------------
from __future__ import annotations # Las anotaciones de tipo son strings por defecto y no se evaluan hasta tiempo de ejecución.

import math # Operaciones matemáticas
import os # Interacción con el sistema operativo
import json # Manejo de JSON
import re
from fastmcp import FastMCP # Framework MCP
from typing import Any, Dict, List, Optional, Set, Tuple # Anotaciones de tipos
import requests # Para hacer peticiones HTTP

from xml.etree import ElementTree as ET # Para parsear XML

try:
    from pyproj import CRS, Transformer  # type: ignore
    _HAS_PYPROJ = True
except Exception:
    _HAS_PYPROJ = False


# Endpoints JSON oficiales (WCF) e INSPIRE WFS
BASE_COORD = "https://ovc.catastro.meh.es/OVCServWeb/OVCWcfCallejero/COVCCoordenadas.svc/json"
BASE_CALLEJERO = "https://ovc.catastro.meh.es/OVCServWeb/OVCWcfCallejero/COVCCallejero.svc/json"
BASE_WFS_CP = "https://ovc.catastro.meh.es/INSPIRE/wfsCP.aspx"

# Namespaces XML
WFS_NS = {
    "wfs": "http://www.opengis.net/wfs/2.0",
    "ows": "http://www.opengis.net/ows/1.1",
    "fes": "http://www.opengis.net/fes/2.0",
    "gml": "http://www.opengis.net/gml/3.2",
    "xs": "http://www.w3.org/2001/XMLSchema",
    "cp": "http://inspire.ec.europa.eu/schemas/cp/4.0",
}
# URL para GML 3.2
GML_NS = {"gml": "http://www.opengis.net/gml/3.2"}


# Creación del MCP  
mcp = FastMCP("Catastro")

# Constantes
DEFAULT_TIMEOUT_S = 20 # Timeout por defecto en segundos

# FUNCIONES AUXILIARES --------------------

def _get_json(url: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Uso:
        Helper robusto para hacer GET y devolver JSON.
    Entradas:
        url (str): endpoint absoluto
        params (dict): query params
    Salida:
        dict: respuesta JSON
    """
    headers = {"User-Agent": "mcp-catastro/0.1 (+https://example.local)"}
    r = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT_S, headers=headers)
    r.raise_for_status()
    return r.json()

# HERRAMIENTAS MCP --------------------

@mcp.tool()
def obtener_provincias() -> dict:
    """
    Uso:
        Lista provincias disponibles en los servicios del Catastro.
    Entradas:
        -
    Salida:
        dict: respuesta JSON del servicio
    """
    return _get_json(f"{BASE_CALLEJERO}/ObtenerProvincias", {})


@mcp.tool()
def obtener_municipios(provincia: str, municipio_filtro: str = "") -> dict:
    """
    Uso:
        Lista municipios de una provincia (puedes filtrar por nombre parcial).
    Entradas:
        provincia (str): nombre de provincia (según ObtenerProvincias)
        municipio_filtro (str): texto parcial opcional
    Salida:
        dict: respuesta JSON del servicio
    """
    return _get_json(
        f"{BASE_CALLEJERO}/ObtenerMunicipios",
        {"Provincia": provincia, "Municipio": municipio_filtro},
    )
    
@mcp.tool()
def obtener_vias(provincia: str, municipio: str, via_filtro: str = "", tipo_via: str = "") -> dict:
    """
    Uso:
        Lista las vías / calles  de un municipio (podemos filtrar por nombre parcial).
    Entradas:
        provincia (str): nombre de provincia (según ObtenerProvincias)
        municipio (str): nombre de municipio (según ObtenerMunicipios)
        tipo_via (str): tipo de vía opcional (idealmente código: CL, AV, PZ, etc. Anexo II)
        via_filtro (str): texto parcial opcional (nombre de vía / calle a buscar)
        
    Salida:
        dict: respuesta JSON del servicio
    """
    return _get_json(
        f"{BASE_CALLEJERO}/ObtenerCallejero",
        {"Provincia": provincia, "Municipio": municipio, "TipoVia": tipo_via, "NomVia": via_filtro},
    )

@mcp.tool()
def obtener_numeros(provincia: str, municipio: str, tipo_via: str, via: str, numero: str) -> dict:
    """
    Uso:
        Consulta número de una vía (devuelve RC del número si existe o aproximación).
    Entradas:
        provincia (str): nombre de provincia (según ObtenerProvincias)
        municipio (str): nombre de municipio (según ObtenerMunicipios)
        tipo_via (str): tipo de vía (idealmente código: CL, AV, PZ, etc. Anexo II)
        via (str): nombre de vía (según ObtenerVias)
        numero (str): número de la vía (puede ser parcial)
    Salida:
        dict: respuesta JSON del servicio
    """
    return _get_json(
        f"{BASE_CALLEJERO}/ObtenerNumerero",
        {"Provincia": provincia, "Municipio": municipio, "TipoVia": tipo_via, "NomVia": via, "Numero": numero},
    )  

@mcp.tool()
def dcnp_por_direccion(
    provincia: str,
    municipio: str,
    sigla: str,
    calle: str,
    numero: str,
    bloque: str = "",
    escalera: str = "",
    planta: str = "",
    puerta: str = "",    
) -> dict:
    """
    Uso:
        Consulta los datos catastrales no protegidos de un inmueble por su localización.
    Entradas:
        provincia (str): nombre de provincia (según ObtenerProvincias). Obligatorio.
        municipio (str): nombre de municipio (según ObtenerMunicipios). Obligatorio.
        sigla (str): tipo de vía (idealmente código: CL, AV, PZ, etc. Anexo II. Obligatorio.
        calle (str): nombre de vía (según ObtenerVias). Obligatorio.
        numero (str): número de la vía (según ObtenerNumeros). Obligatorio.
        bloque (str): opcional
        escalera (str): opcional
        planta (str): opcional
        puerta (str): opcional
        
    Salida:
        dict: respuesta JSON del servicio
    """
    return _get_json(
        f"{BASE_CALLEJERO}/Consulta_DNPLOC",
        {
            "Provincia": provincia,
            "Municipio": municipio,
            "Sigla": sigla,
            "Calle": calle,
            "Numero": numero,
            "Bloque": bloque,
            "Escalera": escalera,
            "Planta": planta,
            "Puerta": puerta,           
        },
    )   

@mcp.tool()
def dcnp_por_rc(refcat: str, provincia: str = "", municipio: str = "") -> dict:
    """
    Uso:
        Consulta los datos catastrales no protegidos de un inmueble por su Referencia Catastral.
    Entradas:
        refcat (str): Referencia Catastral. Obligatorio. Puede tener 14, 18 o 20 posiciones. En caso
        de que sean 14 posiciones (lo que se corresponde con la referencia de una
        finca), se devuelve una lista de todos los inmuebles de esa finca (es decir cuyos
        14 primeros caracteres de la RC coinciden con el parámetro). 
        provincia (str): opcional
        municipio (str): opcional
    Salida:
        dict: respuesta JSON del servicio
    """
    return _get_json(
        f"{BASE_CALLEJERO}/Consulta_DNPRC",
        {"Provincia": provincia, "Municipio": municipio, "RefCat": refcat},
    )

@mcp.tool()
def dcnp_por_poligono_parcela(provincia: str, municipio: str, poligono: str, parcela: str) -> dict:
    """
    Uso:
        Consulta los datos catastrales no protegidos de un inmueble por su polígono y parcela.
    Entradas:
        provincia (str): nombre de provincia (según ObtenerProvincias). Obligatorio.
        municipio (str): nombre de municipio (según ObtenerMunicipios). Obligatorio.
        poligono (str): polígono catastral. Obligatorio.
        parcela (str): parcela catastral. Obligatorio.
    Salida:
        dict: respuesta JSON del servicio
    """
    return _get_json(
        f"{BASE_CALLEJERO}/Consulta_DNPPP",
        {
            "Provincia": provincia,
            "Municipio": municipio,
            "Poligono": poligono,
            "Parcela": parcela,
        },
    )


@mcp.tool()
def rc_a_coordenadas(refcat: str, srs: str = "EPSG:4326", provincia: str = "", municipio: str = "") -> dict:
    """
    Uso:
        Convierte una Referencia Catastral a coordenadas.
    Entradas:
        refcat (str): Referencia Catastral (14/18/20 según caso)
        srs (str): sistema de referencia (p.ej. EPSG:4326)
        provincia (str): opcional
        municipio (str): opcional
    Salida:
        dict: respuesta JSON del servicio (incluye coordenadas y metadatos)
    """
    return _get_json(
        f"{BASE_COORD}/Consulta_CPMRC",
        {"Provincia": provincia, "Municipio": municipio, "SRS": srs, "RefCat": refcat},
    )


@mcp.tool()
def coordenadas_a_rc(x: float, y: float, srs: str = "EPSG:4326") -> dict:
    """
    Uso:
        Devuelve la(s) referencia(s) catastral(es) asociadas a unas coordenadas.
    Entradas:
        x (float): CoorX (si EPSG:4326 suele ser longitud)
        y (float): CoorY (si EPSG:4326 suele ser latitud)
        srs (str): sistema de referencia (p.ej. EPSG:4326)
    Salida:
        dict: respuesta JSON del servicio
    """
    return _get_json(
        f"{BASE_COORD}/Consulta_RCCOOR",
        {"CoorX": x, "CoorY": y, "SRS": srs},
    )


@mcp.tool()
def distancia_coordenadas_a_rc(x: float, y: float, srs: str = "EPSG:4326") -> dict:
    """
    Uso:
        Devuelve la(s) referencia(s) catastral(es) por proximidad a unas coordenadas.
        A partir de unas coordenadas (X e Y) y su sistema de referencia se obtiene la lista de
        referencias catastrales próximas a un punto así como el domicilio (municipio, calle y
        número o polígono, parcela y municipio), y la distancia a dicho punto.
    Entradas:
        x (float): CoorX (si EPSG:4326 suele ser longitud)
        y (float): CoorY (si EPSG:4326 suele ser latitud)
        srs (str): sistema de referencia (p.ej. EPSG:4326)
    Salida:
        dict: respuesta JSON del servicio
    """
    return _get_json(
        f"{BASE_COORD}/Consulta_RCCOOR_Distancia",
        {"CoorX": x, "CoorY": y, "SRS": srs},
    )

# HERRAMIENTAS WFS INSPIRE CATASTRO PARCELAS --------------------

# AUXILIARES (NO tools)
# ---------------------------------------------------------------------

def _http_get_text(url: str, params: Optional[Dict[str, Any]] = None, accept: str = "application/xml") -> str:
    """
    Uso:
        Helper robusto para hacer GET y devolver el cuerpo como texto.
    Entradas:
        url (str): endpoint absoluto
        params (dict|None): query params
        accept (str): cabecera Accept
    Salida:
        str: respuesta en texto (XML/HTML/etc.)
    """
    headers = {"User-Agent": "mcp-catastro/0.1", "Accept": accept}
    r = requests.get(url, params=params or {}, timeout=DEFAULT_TIMEOUT_S, headers=headers)
    r.raise_for_status()
    return r.text


def _is_wfs_exception(xml_text: str) -> bool:
    """
    Uso:
        Detecta si una respuesta XML contiene un ExceptionReport WFS/OWS.
    Entradas:
        xml_text (str): texto XML
    Salida:
        bool: True si parece un ExceptionReport
    """
    return "ExceptionReport" in xml_text or "ows:Exception" in xml_text


def _wfs_get_capabilities_xml(version: str = "2.0.0") -> str:
    """
    Uso:
        Descarga GetCapabilities del WFS INSPIRE de Parcelas.
    Entradas:
        version (str): versión WFS
    Salida:
        str: XML de GetCapabilities
    """
    params = {"service": "WFS", "request": "GetCapabilities", "version": version}
    return _http_get_text(BASE_WFS_CP, params=params, accept="application/xml")


def _wfs_describe_feature_type_xsd(type_name: str, version: str = "2.0.0") -> str:
    """
    Uso:
        Descarga DescribeFeatureType (XSD) de un FeatureType.
    Entradas:
        type_name (str): nombre EXACTO del FeatureType (ej. cp:CadastralParcel)
        version (str): versión WFS
    Salida:
        str: XSD (XML)
    """
    params = {
        "service": "WFS",
        "request": "DescribeFeatureType",
        "version": version,
        "typeName": type_name,
    }
    return _http_get_text(BASE_WFS_CP, params=params, accept="application/xml")


def _xsd_extract_definitions(xsd_xml: str) -> Dict[str, Any]:
    """
    Uso:
        Extrae definiciones relevantes de un XSD: elements, complexTypes, attributes e includes/imports.
    Entradas:
        xsd_xml (str): contenido XSD en texto
    Salida:
        dict con sets y schema_locations
    """
    root = ET.fromstring(xsd_xml)

    elements: Set[str] = set()
    complex_types: Set[str] = set()
    attributes: Set[str] = set()
    schema_locations: List[str] = []

    for el in root.findall(".//xs:element", WFS_NS):
        name = (el.attrib.get("name") or "").strip()
        if name:
            elements.add(name)

    for ct in root.findall(".//xs:complexType", WFS_NS):
        name = (ct.attrib.get("name") or "").strip()
        if name:
            complex_types.add(name)

    for at in root.findall(".//xs:attribute", WFS_NS):
        name = (at.attrib.get("name") or "").strip()
        if name:
            attributes.add(name)

    for inc in root.findall(".//xs:include", WFS_NS):
        loc = (inc.attrib.get("schemaLocation") or "").strip()
        if loc:
            schema_locations.append(loc)

    for imp in root.findall(".//xs:import", WFS_NS):
        loc = (imp.attrib.get("schemaLocation") or "").strip()
        if loc:
            schema_locations.append(loc)

    return {
        "elements": elements,
        "complex_types": complex_types,
        "attributes": attributes,
        "schema_locations": schema_locations,
    }


def _normalize_srs_to_urn(srs: str) -> str:
    """
    Uso:
        Normaliza CRS/SRS a URN recomendado.
        Acepta:
            - EPSG:25830
            - EPSG::25830
            - urn:ogc:def:crs:EPSG::25830
            - http://www.opengis.net/def/crs/EPSG/0/25830
            - CRS:84 / CRS::84 / urn:ogc:def:crs:CRS::84   (lon/lat, GeoJSON-friendly)
    Entradas:
        srs (str)
    Salida:
        str: URN si es EPSG o CRS84; si no, devuelve lo original
    """
    s = (srs or "").strip()
    if not s:
        return s

    low = s.lower()
    
    # Acepta variantes típicas y normaliza a URN
    compact = s.upper().replace(" ", "")
    if compact in ("CRS:84", "CRS::84", "URN:OGC:DEF:CRS:CRS::84"):
        return "urn:ogc:def:crs:CRS::84"

    # Ya URN EPSG
    if low.startswith("urn:ogc:def:crs:epsg::"):
        return s

    # Ya URN CRS (por si llega algo tipo urn:ogc:def:crs:CRS::84)
    if low.startswith("urn:ogc:def:crs:crs::"):
        return s

    # URL OGC def
    # ej: http://www.opengis.net/def/crs/EPSG/0/25830
    m = re.search(r"/EPSG/\d+/(\d+)$", s)
    if m:
        code = m.group(1)
        return f"urn:ogc:def:crs:EPSG::{code}"

    # EPSG:25830
    if s.upper().startswith("EPSG:"):
        code = s.split(":")[-1].strip()
        if code.isdigit():
            return f"urn:ogc:def:crs:EPSG::{code}"

    # EPSG::25830
    if s.upper().startswith("EPSG::"):
        code = s.split("::")[-1].strip()
        if code.isdigit():
            return f"urn:ogc:def:crs:EPSG::{code}"

    return s  # lo dejamos tal cual si no sabemos convertir


def _epsg_from_any_srs(srs: str) -> Optional[int]:
    """
    Uso:
        Extrae el código EPSG si puede.
    Entradas:
        srs (str)
    Salida:
        int|None
    """
    s = (srs or "").strip()
    if not s:
        return None
    m = re.search(r"EPSG(?::|::|/0/)(\d+)$", s, flags=re.IGNORECASE)
    if m:
        try:
            return int(m.group(1))
        except Exception:
            return None
    return None


def _fes_filter_equals(prop_qname: str, literal: str) -> str:
    """
    Uso:
        Construye filtro FES 2.0 PropertyIsEqualTo con namespaces INSPIRE CP.
    """
    return f"""<fes:Filter xmlns:fes="http://www.opengis.net/fes/2.0"
    xmlns:cp="http://inspire.ec.europa.eu/schemas/cp/4.0">
  <fes:PropertyIsEqualTo>
    <fes:ValueReference>{prop_qname}</fes:ValueReference>
    <fes:Literal>{literal}</fes:Literal>
  </fes:PropertyIsEqualTo>
</fes:Filter>"""


def _wfs_get_feature_filtered(type_name: str, srs_urn: str, filter_xml: str, count: int = 5) -> str:
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": type_name,
        "SRSNAME": srs_urn,
        "count": str(count),
        "FILTER": filter_xml,
    }
    headers = {"User-Agent": "mcp-catastro/0.1", "Accept": "application/xml"}
    r = requests.get(BASE_WFS_CP, params=params, timeout=DEFAULT_TIMEOUT_S, headers=headers)
    r.raise_for_status()
    return r.text


def _wfs_get_feature_by_resource_id(type_name: str, srs_urn: str, resource_id: str) -> str:
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": type_name,
        "SRSNAME": srs_urn,
        "resourceId": resource_id,
    }
    headers = {"User-Agent": "mcp-catastro/0.1", "Accept": "application/xml"}
    r = requests.get(BASE_WFS_CP, params=params, timeout=DEFAULT_TIMEOUT_S, headers=headers)
    r.raise_for_status()
    return r.text


def _wfs_post(xml_body: str) -> str:
    headers = {
        "User-Agent": "mcp-catastro/0.1",
        "Content-Type": "application/xml",
        "Accept": "application/xml",
    }
    r = requests.post(BASE_WFS_CP, data=xml_body.encode("utf-8"), timeout=DEFAULT_TIMEOUT_S, headers=headers)
    r.raise_for_status()
    return r.text


def _wfs_getfeature_post_resourceid(type_name: str, srs_urn: str, resource_id: str) -> str:
    body = f"""<?xml version="1.0" encoding="UTF-8"?>
<wfs:GetFeature service="WFS" version="2.0.0"
  xmlns:wfs="http://www.opengis.net/wfs/2.0"
  xmlns:fes="http://www.opengis.net/fes/2.0"
  xmlns:cp="http://inspire.ec.europa.eu/schemas/cp/4.0"
  xmlns:gml="http://www.opengis.net/gml/3.2">
  <wfs:Query typeNames="{type_name}" srsName="{srs_urn}">
    <fes:Filter>
      <fes:ResourceId rid="{resource_id}"/>
    </fes:Filter>
  </wfs:Query>
</wfs:GetFeature>"""
    return _wfs_post(body)


# ----------------------------
# GML parsing (diagnóstico)
# ----------------------------

def _gml_first_srs_name(gml_text: str) -> Optional[str]:
    """
    Uso:
        Intenta localizar el primer atributo srsName en el GML.
    Salida:
        str|None
    """
    try:
        root = ET.fromstring(gml_text)
    except Exception:
        return None

    # posList suele tener srsName en INSPIRE
    pos = root.find(".//gml:posList", WFS_NS)
    if pos is not None and pos.attrib.get("srsName"):
        return pos.attrib.get("srsName")

    # fallback: cualquier geometría con srsName
    for el in root.iter():
        srs = el.attrib.get("srsName")
        if srs:
            return srs
    return None


def _gml_extract_first_poslist_coords(gml_text: str) -> Optional[List[Tuple[float, float]]]:
    """
    Uso:
        Extrae el primer gml:posList como lista de pares float.
        (Suele ser el anillo exterior de la parcela.)
    Salida:
        list[(a,b)]|None
    """
    try:
        root = ET.fromstring(gml_text)
    except Exception:
        return None

    pos = root.find(".//gml:LinearRing/gml:posList", WFS_NS)
    if pos is None or not (pos.text or "").strip():
        # fallback si no hay LinearRing (otro tipo geom.)
        pos = root.find(".//gml:posList", WFS_NS)
        if pos is None or not (pos.text or "").strip():
            return None

    nums = list(map(float, re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", pos.text)))
    if len(nums) < 4:
        return None

    # pares consecutivos
    coords = list(zip(nums[0::2], nums[1::2]))
    return coords


def _utm_zone_from_lon(lon: float) -> int:
    """
    Uso:
        Devuelve huso UTM (1..60) a partir de longitud (grados).
    """
    return int((lon + 180.0) // 6.0) + 1


def _etrs89_utm_epsg_from_lon(lon: float) -> int:
    """
    Uso:
        Convierte longitud → EPSG ETRS89 / UTM (258xx).
        Ej:
            Tenerife lon ~ -16.5 -> zona 28 -> EPSG:25828
            Madrid lon ~ -3.7 -> zona 30 -> EPSG:25830
    """
    zone = _utm_zone_from_lon(lon)
    return 25800 + zone


def _reproject_coords(
    coords: List[Tuple[float, float]],
    src_epsg: int,
    dst_epsg: int,
    src_axis_is_latlon: bool,
) -> Optional[List[Tuple[float, float]]]:
    """
    Uso:
        Reproyecta coordenadas con pyproj si está disponible.
    Entradas:
        coords: lista de pares
        src_epsg, dst_epsg
        src_axis_is_latlon: True si coords vienen como (lat,lon)
    Salida:
        list[(x,y)]|None
    """
    if not _HAS_PYPROJ:
        return None

    tf = Transformer.from_crs(CRS.from_epsg(src_epsg), CRS.from_epsg(dst_epsg), always_xy=True)

    out: List[Tuple[float, float]] = []
    for a, b in coords:
        if src_axis_is_latlon:
            lat, lon = a, b
            x, y = tf.transform(lon, lat)  # always_xy => (lon,lat)
        else:
            x, y = tf.transform(a, b)
        out.append((x, y))
    return out


def _request_getparcel_gml(ref14: str, srs: str) -> str:
    """
    Uso:
        Llama a StoredQuery GetParcel del WFS CP.
    Entradas:
        ref14 (str)
        srs (str): admite EPSG:xxxx, EPSG::xxxx, URN o URL.
    Salida:
        str: GML (FeatureCollection)
    """
    # Normaliza a URN para máxima compatibilidad
    srs_urn = _normalize_srs_to_urn(srs)

    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "storedquery_id": "GetParcel",
        "refcat": ref14,
        "srsName": srs_urn,   # <-- CORRECCIÓN: srsName y en URN
    }

    headers = {"User-Agent": "mcp-catastro/0.1", "Accept": "application/xml"}
    r = requests.get(BASE_WFS_CP, params=params, timeout=DEFAULT_TIMEOUT_S, headers=headers)
    r.raise_for_status()
    return r.text


def _coords_preview_stats(coords: List[Tuple[float, float]]) -> Dict[str, Any]:
    """
    Uso:
        Da estadísticas básicas para ver si hay variación real.
    """
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    return {
        "count": len(coords),
        "min_a": min(xs),
        "max_a": max(xs),
        "min_b": min(ys),
        "max_b": max(ys),
        "range_a": max(xs) - min(xs),
        "range_b": max(ys) - min(ys),
        "first_5": coords[:5],
    }


# ---------------------------------------------------------------------
# TOOLS MCP (WFS)
# ---------------------------------------------------------------------

@mcp.tool()
def wfs_cp_get_capabilities(version: str = "2.0.0") -> dict:
    """
    Uso:
        Obtiene el documento GetCapabilities del WFS INSPIRE de Parcelas del Catastro.
    """
    xml = _wfs_get_capabilities_xml(version=version)
    if _is_wfs_exception(xml):
        return {"ok": False, "endpoint": BASE_WFS_CP, "version": version, "error_xml": xml}
    return {"ok": True, "endpoint": BASE_WFS_CP, "version": version, "capabilities_xml": xml}


@mcp.tool()
def wfs_cp_list_feature_types(version: str = "2.0.0") -> dict:
    """
    Uso:
        Lista FeatureTypes y CRS soportados desde GetCapabilities.
    """
    xml = _wfs_get_capabilities_xml(version=version)
    if _is_wfs_exception(xml):
        return {"ok": False, "version": version, "error_xml": xml}

    root = ET.fromstring(xml)

    feature_types = []
    for ft in root.findall(".//wfs:FeatureTypeList/wfs:FeatureType", WFS_NS):
        name = (ft.findtext("wfs:Name", default="", namespaces=WFS_NS) or "").strip()
        title = (ft.findtext("ows:Title", default="", namespaces=WFS_NS) or "").strip()
        default_crs = (ft.findtext("wfs:DefaultCRS", default="", namespaces=WFS_NS) or "").strip()
        other_crs = [
            (e.text or "").strip()
            for e in ft.findall("wfs:OtherCRS", WFS_NS)
            if (e.text or "").strip()
        ]
        if name:
            feature_types.append(
                {
                    "name": name,
                    "title": title or None,
                    "default_crs": default_crs or None,
                    "other_crs": other_crs,
                }
            )

    return {"ok": True, "count": len(feature_types), "feature_types": feature_types}


@mcp.tool()
def wfs_cp_describe_feature_type_resolved(type_name: str, version: str = "2.0.0", max_includes: int = 5) -> dict:
    """
    Uso:
        DescribeFeatureType + resolución de includes/imports.
    """
    stub = _wfs_describe_feature_type_xsd(type_name=type_name, version=version)
    if _is_wfs_exception(stub):
        return {"ok": False, "type_name": type_name, "version": version, "error_xml": stub}

    sources = [{"url": "DescribeFeatureType(stub)", "len": len(stub)}]
    merged_elements: Set[str] = set()
    merged_ct: Set[str] = set()
    merged_attr: Set[str] = set()

    stub_info = _xsd_extract_definitions(stub)
    merged_elements |= stub_info["elements"]
    merged_ct |= stub_info["complex_types"]
    merged_attr |= stub_info["attributes"]

    to_fetch = list(dict.fromkeys(stub_info["schema_locations"]))
    fetched: Set[str] = set()
    includes_found: List[str] = []

    while to_fetch and len(fetched) < max_includes:
        url = to_fetch.pop(0)
        if url in fetched:
            continue
        fetched.add(url)
        includes_found.append(url)

        try:
            xsd = _http_get_text(url, params=None, accept="application/xml")
        except Exception:
            sources.append({"url": url, "len": 0, "error": "download_failed"})
            continue

        sources.append({"url": url, "len": len(xsd)})

        info = _xsd_extract_definitions(xsd)
        merged_elements |= info["elements"]
        merged_ct |= info["complex_types"]
        merged_attr |= info["attributes"]

        for loc in info["schema_locations"]:
            if loc not in fetched and loc not in to_fetch:
                to_fetch.append(loc)

    return {
        "ok": True,
        "type_name": type_name,
        "version": version,
        "sources": sources,
        "elements": sorted(merged_elements),
        "complexTypes": sorted(merged_ct)[:400],
        "attributes": sorted(merged_attr),
        "includes_found": includes_found,
        "note": "Si necesitas filtrar por RC, StoredQuery GetParcel es lo más directo.",
    }


@mcp.tool()
def parcela_gml_por_rc(refcat: str, srs: str = "AUTO") -> dict:
    """
    Uso:
        Obtiene el GML de UNA parcela por RC usando StoredQuery GetParcel (WFS CP Catastro),
        con modo AUTO para elegir un CRS UTM que el WFS realmente soporte.
        Nota importante:
            - Para Canarias (UTM 28N), este WFS NO ofrece EPSG:25828 pero SÍ ofrece EPSG:32628.
            - En Península suele funcionar con EPSG:25830 (y otros 25829/25831 según huso).
    Entradas:
        refcat (str): RC (14/18/20). Se usa base de 14.
        srs (str):
            - "AUTO" (recomendado): pide 4326, detecta huso, vuelve a pedir UTM soportado.
            - "EPSG:4326", "EPSG:25830", "EPSG:32628", "EPSG::25830", URN, etc.
    Salida:
        dict: {
            ok, used_refcat, requested_srs, resolved_srs, response_srsName,
            gml, note, diagnostic
        }
    """
    return _parcela_gml_por_rc_impl(refcat=refcat, srs=srs)  

@mcp.tool()
def parcela_vertices_por_rc(refcat: str, srs: str = "AUTO") -> dict:
    """
    Uso:
        Devuelve vértices de la parcela para pruebas rápidas.
        En AUTO:
          - pide 4326
          - calcula EPSG UTM correcto
          - si pyproj está disponible, reproyecta a UTM y devuelve metros
    Entradas:
        refcat (str): RC
        srs (str): "AUTO" o EPSG explícito
    Salida:
        dict con vertices_4326 y/o vertices_utm (si aplica)
    """
    ref14 = (refcat or "").strip().upper()[:14]
    if not ref14:
        return {"ok": False, "note": "RC vacía"}

    # 1) Siempre sacamos 4326 para diagnóstico
    gml_4326 = _request_getparcel_gml(ref14, "EPSG:4326")
    if _is_wfs_exception(gml_4326):
        return {"ok": False, "used_refcat": ref14, "note": gml_4326[:1200]}

    srs_name_4326 = _gml_first_srs_name(gml_4326) or "unknown"
    coords_4326 = _gml_extract_first_poslist_coords(gml_4326) or []
    if not coords_4326:
        return {"ok": False, "used_refcat": ref14, "note": "No se pudo extraer posList en 4326"}

    lat0, lon0 = coords_4326[0][0], coords_4326[0][1]
    epsg_utm = _etrs89_utm_epsg_from_lon(lon0)

    out: Dict[str, Any] = {
        "ok": True,
        "used_refcat": ref14,
        "response_srsName_4326": srs_name_4326,
        "epsg_utm_recommended": epsg_utm,
        "vertices_4326_latlon": coords_4326[:50],  # límite por tamaño
        "stats_4326": _coords_preview_stats(coords_4326),
        "pyproj_available": _HAS_PYPROJ,
    }

    # 2) Si se pide AUTO o UTM explícito y tenemos pyproj: devolvemos UTM en metros
    req = (srs or "").strip().upper()
    want_utm = req in ("AUTO", "AUTO_UTM", "UTM_AUTO") or ("258" in req)

    if want_utm and _HAS_PYPROJ:
        utm_coords = _reproject_coords(
            coords=coords_4326,
            src_epsg=4326,
            dst_epsg=epsg_utm,
            src_axis_is_latlon=True,  # importante: coords vienen como (lat,lon)
        )
        out["vertices_utm_m"] = (utm_coords or [])[:50]
        out["stats_utm"] = _coords_preview_stats(utm_coords) if utm_coords else None
        out["note"] = f"Vértices UTM reproyectados a EPSG:{epsg_utm} (metros)."
    else:
        out["note"] = "Devuelvo solo 4326 (lat,lon). Para UTM en servidor, instala pyproj."

    return out


# PARA DIAGNÓSTICO --------------------
@mcp.tool()
def wfs_cp_get_feature_sample(type_name: str = "cp:CadastralParcel", srs: str = "EPSG:4326", count: int = 1) -> dict:
    """
    Uso:
        GetFeature SIN filtro para inspeccionar salida real del WFS.
    """
    srs_urn = _normalize_srs_to_urn(srs)

    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": type_name,
        "SRSNAME": srs_urn,
        "count": str(count),
    }
    headers = {"User-Agent": "mcp-catastro/0.1", "Accept": "application/xml"}
    r = requests.get(BASE_WFS_CP, params=params, timeout=DEFAULT_TIMEOUT_S, headers=headers)
    r.raise_for_status()

    xml = r.text

    return {
        "ok": True,
        "type_name": type_name,
        "srs": srs_urn,
        "xml_head": xml[:8000],
    }

# EXPORTACION GEOJSON --------------------

# AUXILIARES (NO tools)
# ---------------------------------------------------------------------

def _gml_first_srs_name(gml_text: str) -> Optional[str]:
    """
    Uso:
        Intenta localizar el primer atributo srsName en el GML.
    """
    try:
        root = ET.fromstring(gml_text)
    except Exception:
        return None

    for path in [
        ".//gml:MultiSurface",
        ".//gml:Surface",
        ".//gml:Polygon",
        ".//gml:Point",
    ]:
        el = root.find(path, GML_NS)
        if el is not None and el.attrib.get("srsName"):
            return el.attrib["srsName"]

    for el in root.iter():
        srs = el.attrib.get("srsName")
        if srs:
            return srs
    return None


def _epsg_from_srs_name(srs_name: str) -> Optional[int]:
    """
    Uso:
        Extrae el código EPSG de un srsName tipo OGC.
    """
    if not srs_name:
        return None
    m = re.search(r"(?:EPSG/0/|EPSG::)(\d+)", srs_name)
    return int(m.group(1)) if m else None


def _is_crs84(srs_name: str) -> bool:
    """
    Uso:
        Detecta si srsName es CRS:84 (lon,lat).
    """
    return "CRS::84" in (srs_name or "")


def _is_epsg_4326(srs_name: str) -> bool:
    """
    Uso:
        Detecta si srsName es EPSG:4326.    
    """
    return (srs_name or "").endswith("/4326") or "EPSG::4326" in (srs_name or "")

def _parse_ring_coords(linearring_el: ET.Element) -> List[Tuple[float, float]]:
    """
    Uso:
        Extrae coordenadas de un gml:LinearRing.    
    """
    poslist = linearring_el.find("gml:posList", GML_NS)
    if poslist is not None and (poslist.text or "").strip():
        nums = list(map(float, re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", poslist.text)))
        return list(zip(nums[0::2], nums[1::2]))

    poses = linearring_el.findall("gml:pos", GML_NS)
    coords: List[Tuple[float, float]] = []
    for p in poses:
        txt = (p.text or "").strip()
        if not txt:
            continue
        nums = list(map(float, re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", txt)))
        if len(nums) >= 2:
            coords.append((nums[0], nums[1]))
    return coords


def _close_ring(ring: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """
    Uso:
        Asegura que el anillo está cerrado (primer punto = último punto).
    """
    if ring and ring[0] != ring[-1]:
        ring = ring + [ring[0]]
    return ring


def _gml_extract_polygons(gml_text: str) -> List[List[List[Tuple[float, float]]]]:
    """
    Devuelve:
      polygons = [
        [  # rings (0 exterior, >0 interiores)
          [(x,y), ...],
          [(x,y), ...],
        ],
        ...
      ]
    """
    try:
        root = ET.fromstring(gml_text)
    except Exception:
        return []

    polygons: List[List[List[Tuple[float, float]]]] = []

    # MultiSurface/Surface con surfaceMember
    surface_members = root.findall(".//gml:surfaceMember", GML_NS)
    if surface_members:
        for sm in surface_members:
            rings: List[List[Tuple[float, float]]] = []

            ext = sm.find(".//gml:exterior//gml:LinearRing", GML_NS)
            if ext is not None:
                r = _close_ring(_parse_ring_coords(ext))
                if r:
                    rings.append(r)

            for interior in sm.findall(".//gml:interior//gml:LinearRing", GML_NS):
                r = _close_ring(_parse_ring_coords(interior))
                if r:
                    rings.append(r)

            if rings:
                polygons.append(rings)

        return polygons

    # Fallback: gml:Polygon directo
    poly = root.find(".//gml:Polygon", GML_NS)
    if poly is not None:
        rings: List[List[Tuple[float, float]]] = []
        ext = poly.find(".//gml:exterior//gml:LinearRing", GML_NS)
        if ext is not None:
            r = _close_ring(_parse_ring_coords(ext))
            if r:
                rings.append(r)

        for interior in poly.findall(".//gml:interior//gml:LinearRing", GML_NS):
            r = _close_ring(_parse_ring_coords(interior))
            if r:
                rings.append(r)

        if rings:
            polygons.append(rings)

    return polygons

def _to_lonlat(coords: List[Tuple[float, float]], srs_name: str) -> List[Tuple[float, float]]:
    """
    Devuelve siempre (lon, lat) en EPSG:4326 para GeoJSON.
    - CRS::84: ya viene lon/lat
    - EPSG:4326: en este WFS suele venir lat/lon -> swap
    - UTM/proyectado: reproyecta a 4326 (requiere pyproj)
    """
    epsg = _epsg_from_srs_name(srs_name) if srs_name else None

    if _is_crs84(srs_name):
        return coords

    if _is_epsg_4326(srs_name):
        return [(y, x) for (x, y) in coords]  # lat/lon -> lon/lat

    if epsg is not None and (str(epsg).startswith("326") or str(epsg).startswith("258") or epsg in (3857, 3785, 3035)):
        if not _HAS_PYPROJ:
            raise RuntimeError("pyproj no disponible: no puedo reproyectar a EPSG:4326")
        tf = Transformer.from_crs(CRS.from_epsg(epsg), CRS.from_epsg(4326), always_xy=True)
        out: List[Tuple[float, float]] = []
        for x, y in coords:
            lon, lat = tf.transform(x, y)
            out.append((lon, lat))
        return out

    # Si no se reconoce CRS, devolvemos tal cual (no recomendado)
    return coords


def _round_lonlat(coords: List[Tuple[float, float]], nd: int = 7) -> List[List[float]]:
    """
    Uso:
        Redondea coordenadas lon/lat a nd decimales para GeoJSON.
    """
    return [[round(lon, nd), round(lat, nd)] for lon, lat in coords]


def _compute_bbox(polygons_lonlat: List[List[List[Tuple[float, float]]]]) -> Optional[List[float]]:
    """
    Uso:
        Calcula bbox [minx, miny, maxx, maxy] de lista
    """
    lons: List[float] = []
    lats: List[float] = []
    for poly in polygons_lonlat:
        for ring in poly:
            for lon, lat in ring:
                lons.append(lon)
                lats.append(lat)
    if not lons:
        return None
    return [min(lons), min(lats), max(lons), max(lats)]

def _geojson_feature_from_gml(gml_text: str, ref14: str) -> Dict[str, Any]:
    """
    Uso:
        Convierte GML de parcela a GeoJSON Feature.
    """
    srs_name = _gml_first_srs_name(gml_text) or "unknown"
    polygons = _gml_extract_polygons(gml_text)
    if not polygons:
        raise RuntimeError("No se encontraron polígonos en el GML")

    polygons_ll: List[List[List[Tuple[float, float]]]] = []
    for poly in polygons:
        rings_ll: List[List[Tuple[float, float]]] = []
        for ring in poly:
            rings_ll.append(_to_lonlat(ring, srs_name))
        polygons_ll.append(rings_ll)

    bbox = _compute_bbox(polygons_ll)

    if len(polygons_ll) == 1:
        geom = {"type": "Polygon", "coordinates": [_round_lonlat(r, 7) for r in polygons_ll[0]]}
    else:
        geom = {
            "type": "MultiPolygon",
            "coordinates": [[_round_lonlat(r, 7) for r in poly] for poly in polygons_ll],
        }
    
    axis_fix_applied = ("EPSG/0/4326" in (srs_name or "")) or ("EPSG::4326" in (srs_name or ""))

    feature: Dict[str, Any] = {
        "type": "Feature",
        "properties": {
            "refcat": ref14,
            "source_srsName": srs_name,
            "note": "GeoJSON en lon/lat WGS84 (estándar GeoJSON).",
            "crs_hint": "OGC:CRS84",  # solo como pista; GeoJSON no suele declarar CRS,
            "axis_fix_applied": axis_fix_applied,  # lon/lat             
        },
        "geometry": geom,
    }
    if bbox:
        feature["bbox"] = [round(b, 7) for b in bbox]
    return feature

def _parcela_gml_por_rc_impl(refcat: str, srs: str = "AUTO") -> dict:
    """
    Uso:
        Obtiene el GML de UNA parcela por RC usando StoredQuery GetParcel (WFS CP Catastro),
        con modo AUTO para elegir un CRS UTM que el WFS realmente soporte.
        Nota importante:
            - Para Canarias (UTM 28N), este WFS NO ofrece EPSG:25828 pero SÍ ofrece EPSG:32628.
            - En Península suele funcionar con EPSG:25830 (y otros 25829/25831 según huso).
    Entradas:
        refcat (str): RC (14/18/20). Se usa base de 14.
        srs (str):
            - "AUTO" (recomendado): pide 4326, detecta huso, vuelve a pedir UTM soportado.
            - "EPSG:4326", "EPSG:25830", "EPSG:32628", "EPSG::25830", URN, etc.
    Salida:
        dict: {
            ok, used_refcat, requested_srs, resolved_srs, response_srsName,
            gml, note, diagnostic
        }
    """
    ref14 = (refcat or "").strip().upper()[:14]
    if not ref14:
        return {"ok": False, "used_refcat": None, "gml": None, "note": "RC vacía"}

    req = (srs or "").strip().upper()

    # --- MODO AUTO ---
    if req in ("AUTO", "AUTO_UTM", "UTM_AUTO"):
        # 1) Pedimos en 4326 para obtener lon/lat seguro
        gml_4326 = _request_getparcel_gml(ref14, "EPSG:4326")
        if _is_wfs_exception(gml_4326):
            return {"ok": False, "used_refcat": ref14, "gml": None, "note": gml_4326[:1200]}

        srs_name_4326 = _gml_first_srs_name(gml_4326) or "unknown"
        coords_4326 = _gml_extract_first_poslist_coords(gml_4326) or []

        if not coords_4326:
            return {
                "ok": False,
                "used_refcat": ref14,
                "gml": None,
                "note": "No se pudo extraer posList del GML 4326",
                "diagnostic": {"response_srsName_4326": srs_name_4326},
            }

        # En WFS 2.0 + EPSG:4326, lo normal es eje (lat, lon)
        lat0, lon0 = coords_4326[0][0], coords_4326[0][1]

        # Elegir EPSG UTM soportado por este WFS:
        # - Zonas 27/28 -> 32627/32628 (WGS84 UTM) porque el WFS las anuncia
        # - Zonas 29/30/31 -> 25829/25830/25831 (ETRS89 UTM) porque el WFS las anuncia
        zone = int((lon0 + 180.0) // 6.0) + 1
        if zone in (27, 28):
            epsg_utm = 32600 + zone   # 32627 / 32628
        else:
            epsg_utm = 25800 + zone   # 25829 / 25830 / 25831

        # 2) Pedimos de nuevo en UTM elegido
        gml_utm = _request_getparcel_gml(ref14, f"EPSG:{epsg_utm}")
        if _is_wfs_exception(gml_utm):
            return {
                "ok": True,
                "used_refcat": ref14,
                "requested_srs": srs,
                "resolved_srs": f"EPSG:{epsg_utm}",
                "response_srsName": srs_name_4326,
                "gml": gml_4326,
                "note": f"AUTO: el servidor no aceptó EPSG:{epsg_utm}. Devuelvo 4326.",
                "diagnostic": {
                    "response_srsName_4326": srs_name_4326,
                    "coords_4326_preview": _coords_preview_stats(coords_4326),
                    "epsg_utm_recommended": epsg_utm,
                },
            }

        srs_name_utm = _gml_first_srs_name(gml_utm) or "unknown"
        if str(epsg_utm) not in srs_name_utm:
            return {
                "ok": True,
                "used_refcat": ref14,
                "requested_srs": srs,
                "resolved_srs": f"EPSG:{epsg_utm}",
                "response_srsName": srs_name_utm,
                "gml": gml_utm,
                "note": f"AUTO: el servidor ignoró EPSG:{epsg_utm} y devolvió {srs_name_utm}.",
                "diagnostic": {
                    "response_srsName_4326": srs_name_4326,
                    "coords_4326_preview": _coords_preview_stats(coords_4326),
                    "epsg_requested": epsg_utm,
                },
            }

        coords_utm = _gml_extract_first_poslist_coords(gml_utm) or []
        return {
            "ok": True,
            "used_refcat": ref14,
            "requested_srs": srs,
            "resolved_srs": f"EPSG:{epsg_utm}",
            "response_srsName": srs_name_utm,
            "gml": gml_utm,
            "note": f"AUTO OK: 4326→EPSG:{epsg_utm} (huso {zone}).",
            "diagnostic": {
                "response_srsName_4326": srs_name_4326,
                "coords_4326_preview": _coords_preview_stats(coords_4326),
                "coords_utm_preview": _coords_preview_stats(coords_utm) if coords_utm else None,
            },
        }
        
    # --- MODO MANUAL ---
    gml = _request_getparcel_gml(ref14, srs)
    if _is_wfs_exception(gml):
        return {"ok": False, "used_refcat": ref14, "gml": None, "note": gml[:1200]}

    if ref14 not in gml:
        return {"ok": False, "used_refcat": ref14, "gml": None, "note": "Respuesta no contiene la RC solicitada"}

    srs_name = _gml_first_srs_name(gml) or "unknown"
    coords = _gml_extract_first_poslist_coords(gml) or []

    return {
        "ok": True,
        "used_refcat": ref14,
        "requested_srs": srs,
        "resolved_srs": srs,
        "response_srsName": srs_name,
        "gml": gml,
        "note": "OK (StoredQuery GetParcel)",
        "diagnostic": {
            "coords_preview": _coords_preview_stats(coords) if coords else None,
        },
    }

# TOOL GEOJSON --------------------

@mcp.tool()
def parcela_geojson_por_rc(refcat: str, srs: str = "AUTO") -> dict:
    """
    Uso:
        Devuelve GeoJSON (FeatureCollection) de una parcela por RC.
        - GeoJSON siempre en lon/lat WGS84 (estándar GeoJSON).
        - Para evitar dependencias de reproyección (pyproj) y problemas de CRS en StoredQuery,
          fuerza la petición del GML en EPSG:4326 y realiza swap a lon/lat en la conversión.
    Entradas:
        refcat (str): RC (se usa base 14)
        srs (str): se mantiene por compatibilidad, pero esta tool fuerza EPSG:4326 internamente.
    Salida:
        dict: {ok, used_refcat, source, requested_srs, response_srsName, geojson, geojson_text, note}
    """
    import requests  # por si no está en el scope

    ref14 = (refcat or "").strip().upper()[:14]
    if not ref14:
        return {"ok": False, "used_refcat": None, "geojson": None, "note": "RC vacía"}

    forced_srs = "EPSG:4326"

    try:
        pack = _parcela_gml_por_rc_impl(ref14, forced_srs)
    except requests.exceptions.RequestException as e:
        return {
            "ok": False,
            "used_refcat": ref14,
            "geojson": None,
            "note": f"Error HTTP al obtener GML (forzado {forced_srs}): {e}",
        }

    if not pack.get("ok"):
        return {
            "ok": False,
            "used_refcat": ref14,
            "geojson": None,
            "note": pack.get("note", "Error al obtener GML"),
        }

    gml_text = pack.get("gml", "")
    if not gml_text:
        return {"ok": False, "used_refcat": ref14, "geojson": None, "note": "GML vacío"}

    try:
        feature = _geojson_feature_from_gml(gml_text, ref14)

        # --- envolver en FeatureCollection (más compatible con visores) ---
        collection = {
            "type": "FeatureCollection",
            "features": [feature],
        }
        if isinstance(feature, dict) and "bbox" in feature:
            collection["bbox"] = feature["bbox"]

        return {
            "ok": True,
            "used_refcat": ref14,
            "source": "gml-convert",
            "requested_srs": forced_srs,
            "response_srsName": _gml_first_srs_name(gml_text) or "unknown",
            "geojson": collection,
            "geojson_text": json.dumps(collection, ensure_ascii=False),
            "note": "Convertido desde GML a GeoJSON (lon/lat). Devuelvo FeatureCollection. Petición forzada a EPSG:4326 para evitar reproyección y errores OVC.",
        }
    except Exception as e:
        return {
            "ok": False,
            "used_refcat": ref14,
            "geojson": None,
            "note": f"Error GML→GeoJSON: {e}",
        }


# EXPORTACION ARCHIVOS --------------------

# AUXILIARES (NO tools)
# ---------------------------------------------------------------------

# Carpeta raíz permitida para exportaciones 
EXPORT_ROOT = r"C:\PROFESIONAL\Catastro"

def _safe_export_path(filename: str, out_dir: str = EXPORT_ROOT) -> str:
    """
    Uso:
        Construye una ruta segura dentro de EXPORT_ROOT/out_dir (sin permitir escapes con ..).
    """
    base = os.path.abspath(out_dir or EXPORT_ROOT)
    root = os.path.abspath(EXPORT_ROOT)

    # Restringimos SIEMPRE a EXPORT_ROOT (puedes relajarlo si quieres)
    if not base.startswith(root + os.sep) and base != root:
        raise ValueError(f"Directorio no permitido. Debe estar dentro de: {root}")

    path = os.path.abspath(os.path.join(base, filename))
    if not path.startswith(base + os.sep) and path != base:
        raise ValueError("Ruta no permitida (path traversal).")
    return path


def _write_text(path: str, content: str, overwrite: bool = True) -> int:
    """
    Uso:
        Escribe texto UTF-8 a disco y devuelve bytes escritos.
    """
    if (not overwrite) and os.path.exists(path):
        raise FileExistsError(f"El archivo ya existe: {path}")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    return len(content.encode("utf-8"))

# TOOL PRINCIPAL DE EXPORTACION GML + GEOJSON--------------------

@mcp.tool()
def exportar_parcela_gml_y_geojson(
    refcat: str,
    srs: str = "AUTO",
    out_dir: str = EXPORT_ROOT,
    basename: str = "",
    overwrite: bool = True,
) -> dict:
    """
    Uso:
        Exporta GML + GeoJSON de una parcela en una sola llamada.
        - GML: se pide con srs (AUTO o el que indiques)
        - GeoJSON: siempre se entrega en lon/lat (WGS84). Si pyproj no está, fuerza GML en EPSG:4326.
    Entradas:
        refcat (str): RC (se usa base 14)
        srs (str): "AUTO" o EPSG/URN para el GML
        out_dir (str): carpeta destino (debe estar dentro de EXPORT_ROOT)
        basename (str): nombre base sin extensión (si vacío usa ref14)
        overwrite (bool): sobrescribir si existe
    Salida:
        dict: rutas y métricas de escritura
    """
    ref14 = (refcat or "").strip().upper()[:14]
    if not ref14:
        return {"ok": False, "note": "RC vacía"}

    base = (basename or ref14).strip()
    if not base:
        base = ref14

    # -------- 1) Obtener y guardar GML (SRS solicitado) --------
    pack_gml = _parcela_gml_por_rc_impl(ref14, srs)
    if not pack_gml.get("ok"):
        return {"ok": False, "used_refcat": ref14, "note": pack_gml.get("note", "Error al obtener GML")}

    gml_text = pack_gml.get("gml") or ""
    if not gml_text:
        return {"ok": False, "used_refcat": ref14, "note": "GML vacío"}

    gml_path = _safe_export_path(f"{base}.gml", out_dir=out_dir)
    gml_bytes = _write_text(gml_path, gml_text, overwrite=overwrite)

    # -------- 2) GeoJSON (lon/lat) --------
    # Intento A: convertir desde el mismo GML (si CRS proyectado, requiere pyproj)
    geojson_from_same_gml_ok = True
    try:
        feature = _geojson_feature_from_gml(gml_text, ref14)
    except Exception:
        geojson_from_same_gml_ok = False
        feature = None

    # Intento B (fallback): si falla, pedir GML en EPSG:4326 y convertir (sin reproyección)
    if not geojson_from_same_gml_ok:
        pack_4326 = _parcela_gml_por_rc_impl(ref14, "EPSG:4326")
        if not pack_4326.get("ok"):
            return {
                "ok": False,
                "used_refcat": ref14,
                "gml_path": gml_path,
                "gml_bytes": gml_bytes,
                "note": f"Guardé GML pero falló GeoJSON. Error al obtener GML 4326: {pack_4326.get('note')}",
            }
        gml_4326 = pack_4326.get("gml") or ""
        if not gml_4326:
            return {
                "ok": False,
                "used_refcat": ref14,
                "gml_path": gml_path,
                "gml_bytes": gml_bytes,
                "note": "Guardé GML pero el GML 4326 vino vacío (GeoJSON imposible).",
            }
        feature = _geojson_feature_from_gml(gml_4326, ref14)

    collection = {"type": "FeatureCollection", "features": [feature]}
    if isinstance(feature, dict) and "bbox" in feature:
        collection["bbox"] = feature["bbox"]

    geojson_text = json.dumps(collection, ensure_ascii=False)
    geojson_path = _safe_export_path(f"{base}.geojson", out_dir=out_dir)
    geojson_bytes = _write_text(geojson_path, geojson_text, overwrite=overwrite)

    return {
        "ok": True,
        "used_refcat": ref14,
        "gml": {
            "path": gml_path,
            "bytes": gml_bytes,
            "requested_srs": srs,
            "resolved_srs": pack_gml.get("resolved_srs"),
            "response_srsName": pack_gml.get("response_srsName"),
        },
        "geojson": {
            "path": geojson_path,
            "bytes": geojson_bytes,
            "note": "GeoJSON siempre en lon/lat (WGS84).",
            "converted_from_same_gml": geojson_from_same_gml_ok,
            "pyproj_available": _HAS_PYPROJ,
        },
        "note": "Exportación completada desde el servidor MCP.",
    }


    
