# catastro_mcp_server
## Descripción general
Servidor MCP (Model Context Protocol) en Python que expone herramientas para consultar servicios oficiales del Catastro de España y obtener información catastral no protegida de forma estructurada.

El servidor integra dos familias de servicios:

- OVC / Servicios WCF en JSON (Catastro): consultas de callejero, referencia catastral y conversión entre RC ↔ coordenadas.
- INSPIRE WFS Cadastral Parcels (CP): consulta de parcelas y descarga de geometría en GML, además de utilidades de diagnóstico (GetCapabilities / DescribeFeatureType).

Está pensado para integrarse con clientes compatibles con MCP (p. ej. Claude Desktop) y para facilitar la automatización de flujos BIM / GIS / AECO (enriquecimiento de modelos, auditorías, obtención de geometría, análisis territorial, etc.), manteniendo una arquitectura modular y fácil de desplegar (por ejemplo con `uv/uvx`).

> Nota: este proyecto no está afiliado a la Dirección General del Catastro. Solo consume endpoints públicos y devuelve los resultados de forma normalizada.
## Componentes
### Herramientas
El servidor ofrece las siguientes herramientas:
- `obtener_provincias`
    - <small>Lista provincias disponibles en los servicios del Catastro.</small>
- `obtener_municipios`
    - <small>Lista municipios de una provincia (puedes filtrar por nombre parcial)</small>
    - <small>Input:</small>
        - <small>provincia (str): nombre de provincia (según obtener_provincias)</small>
        - <small>municipio_filtro (str): texto parcial. `OPCIONAL`</small>
- `obtener_vias`
    - <small>Lista las vías / calles  de un municipio (podemos filtrar por nombre parcial).</small>
    - <small>Input:</small>    
        - <small>provincia (str): nombre de provincia (según obtener_provincias)</small>
        - <small>municipio (str): nombre de municipio (según obtener_municipios)</small>
        - <small>tipo_via (str): tipo de vía (idealmente código: CL, AV, PZ, etc. Anexo II). `OPCIONAL`</small>
        - <small>via_filtro (str): texto parcial opcional (nombre de vía / calle a buscar). `OPCIONAL`</small>
- `obtener_numeros`
    - <small>Consulta número de una vía (devuelve RC del número si existe o aproximación).</small>
    - <small>Input:</small>
        - <small>provincia (str): nombre de provincia (según obtener_provincias)</small>
        - <small>municipio (str): nombre de municipio (según obtener_municipios)</small>
        - <small>tipo_via (str): tipo de vía (idealmente código: CL, AV, PZ, etc. Anexo II)</small>
        - <small>via (str): nombre de vía (según obtener_vias)</small>
        - <small>numero (str): número de la vía (puede ser parcial)</small>
- `dcnp_por_direccion`
    - <small>Consulta los datos catastrales no protegidos de un inmueble por su localización.</small>
    - <small>Input:</small>
        - <small>provincia (str): nombre de provincia (según obtener_provincias)</small>
        - <small>municipio (str): nombre de municipio (según obtener_municipios)</small>
        - <small>sigla (str): tipo de vía (idealmente código: CL, AV, PZ, etc. Anexo II).</small>
        - <small>calle (str): nombre de vía (según obtener_vias)</small>
        - <small>numero (str): número de la vía (según obtener_numeros)</small>
        - <small>bloque (str): número del bloque. `OPCIONAL`</small>
        - <small>escalera (str): identificador de la escalera. `OPCIONAL`</small>
        - <small>planta (str): identificador de la planta. `OPCIONAL`</small>
        - <small>puerta (str): identificador de la puerta. `OPCIONAL`</small>
- `dcnp_por_rc`
    - <small>Consulta los datos catastrales no protegidos de un inmueble por su Referencia Catastral.</small>
    - <small>Input:</small>
        - <small>refcat (str): Referencia Catastral. Puede tener 14, 18 o 20 posiciones. En caso de que sean 14 posiciones (lo que se corresponde con la referencia de una finca), se devuelve una lista de todos los inmuebles de esa finca (es decir cuyos
        14 primeros caracteres de la RC coinciden con el parámetro). </small>
        - <small>provincia (str): nombre de provincia. `OPCIONAL`</small>
        - <small>municipio (str): nombre de municipio. `OPCIONAL`</small>
- `dcnp_por_poligono_parcela`
    - <small>Consulta los datos catastrales no protegidos de un inmueble por su polígono y parcela.</small>
    - <small>Input:</small>
        - <small>provincia (str): nombre de provincia.</small>
        - <small>municipio (str): nombre de municipio.</small>
        - <small>poligono (str): polígono catastral.</small>
        - <small>parcela (str): parcela catastral.</small>
- `rc_a_coordenadas`
    - <small>Convierte una Referencia Catastral a coordenadas.</small>
    - <small>Input:</small>
        - <small>refcat (str): Referencia Catastral (14/18/20 según caso)</small>
        - <small>srs (str): sistema de referencia (p.ej. EPSG:4326)</small>
        - <small>provincia (str): nombre de provincia. `OPCIONAL`</small>
        - <small>municipio (str): nombre de municipio. `OPCIONAL`</small>
- `coordenadas_a_rc`
    - <small>Devuelve la(s) referencia(s) catastral(es) asociadas a unas coordenadas.</small>
    - <small>Input:</small>
        - <small>x (float): CoorX (si EPSG:4326 suele ser longitud)</small>
        - <small>y (float): CoorY (si EPSG:4326 suele ser latitud)</small>
        - <small>srs (str): sistema de referencia (p.ej. EPSG:4326)</small>
- `distancia_coordenadas_a_rc`
    - <small>Devuelve la(s) referencia(s) catastral(es) por proximidad a unas coordenadas.
        A partir de unas coordenadas (X e Y) y su sistema de referencia se obtiene la lista de
        referencias catastrales próximas a un punto así como el domicilio (municipio, calle y
        número o polígono, parcela y municipio), y la distancia a dicho punto.</small>
    - <small>Input:</small>
        - <small>x (float): CoorX (si EPSG:4326 suele ser longitud)</small>
        - <small>y (float): CoorY (si EPSG:4326 suele ser latitud)</small>
        - <small>srs (str): sistema de referencia (p.ej. EPSG:4326)</small>
---
- `wfs_cp_get_capabilities`
    - <small>Obtiene el documento GetCapabilities del WFS INSPIRE de Parcelas del Catastro.</small>
    - <small>Input:</small>
        - <small>version (str): versión WFS (por defecto 2.0.0)</small>
- `wfs_cp_list_feature_types`
    - <small>Lista los FeatureTypes disponibles en el WFS INSPIRE de Parcelas del Catastro,
        extrayendo name/title y CRS soportados desde GetCapabilities.</small>
    - <small>Input:</small>
        - <small>version (str): versión WFS (por defecto 2.0.0)</small>
- `wfs_cp_describe_feature_type_resolved`
    - <small>Obtiene el XSD de DescribeFeatureType y resuelve includes/imports (schemaLocation)
        para poder extraer los campos reales del esquema INSPIRE (p.ej. inspireId, localId, etc.).</small>
    - <small>Input:</small>
        - <small>type_name (str): FeatureType exacto (ej. cp:CadastralParcel)</small>
        - <small>version (str): versión WFS (por defecto 2.0.0)</small>
        - <small>max_includes (int): máximo de includes/imports a descargar (para evitar bucles)</small>
- `parcela_gml_por_rc`
    - <small>Obtiene el GML de UNA parcela por RC usando StoredQuery GetParcel (WFS CP Catastro).</small>
    - <small>Input:</small>
        - <small>refcat (str): RC (14/18/20). Se usa la base de 14.</small>
        - <small>srs (str): CRS de salida. Recomendado "EPSG::25830" o "EPSG::4326".</small>

- `parcela_geojson_por_rc`
    - <small>Devuelve GeoJSON (FeatureCollection) de una parcela por RC.
        - GeoJSON siempre en lon/lat WGS84 (estándar GeoJSON).
        - Para evitar dependencias de reproyección (pyproj) y problemas de CRS en StoredQuery,
          fuerza la petición del GML en EPSG:4326 y realiza swap a lon/lat en la conversión.</small>
    - <small>Input:</small>
        - <small>refcat (str): RC (14/18/20). Se usa la base de 14.</small>
        - <small>srs (str): se mantiene por compatibilidad, pero esta tool fuerza EPSG:4326 internamente.</small>

## Requisitos
- Tener instalado `uv` (incluye `uvx`).
- Para usar MCP Inspector: tener instalado Node.js (incluye `npx`).
- Un cliente MCP (por ejemplo Claude Desktop) para consumir las herramientas.

## Uso con Claude Desktop
Añade el servidor dentro de `mcpServers` en tu `claude_desktop_config.json`.

> Nota: si ya tienes otros MCP servers configurados, **no sustituyas** tu archivo completo.
> Añade únicamente el bloque `"Catastro": { ... }` dentro de `mcpServers`.

### Opción A (recomendada): `uvx` en PATH
Si `uv/uvx` está en el PATH del sistema, usa:

```json
"Catastro": {
  "command": "uvx",
  "args": [
    "--from",
    "catastro_mcp_server @ https://github.com/carlosGalisteo/catastro_mcp_server/archive/refs/tags/v0.1.1.zip",
    "catastro_mcp_server"
  ]
}
```
### Opción B (Windows): ruta absoluta a `uvx.exe`
Si Claude no encuentra `uvx`, obtén la ruta con where uvx y úsala como command:
```json
"Catastro": {
  "command": "C:\\Users\\TU_USUARIO\\.local\\bin\\uvx.exe",
  "args": [
    "--from",
    "catastro_mcp_server @ https://github.com/carlosGalisteo/catastro_mcp_server/archive/refs/tags/v0.1.1.zip",
    "catastro_mcp_server"
  ]
}
```
## Prueba rápida (prompts de ejemplo)
Una vez activo el servidor en Claude Desktop, prueba con estas consultas:

1) **Listar provincias**
- “Usa la herramienta `obtener_provincias` y muéstrame el resultado.”

2) **Buscar municipios por filtro**
- “Usa `obtener_municipios` para la provincia `Santa Cruz de Tenerife` y filtra por `Laguna`.”

3) **Obtener información por localización**
- “Usa `dcnp_por_direccion` para el municipio de `Madrid` y por `calle Alcala, 48`.”

4) **Obtener GeoJSON de una parcela por RC**
- “Usa `parcela_geojson_por_rc` con `refcat = 1146801VK4714E` y devuélveme el GeoJSON.”

## Test con MCP Inspector
Ejecuta en una consola (no es necesario clonar el repositorio; puedes hacerlo desde cualquier carpeta):

```bash
npx -y @modelcontextprotocol/inspector uvx --from "catastro_mcp_server @ https://github.com/carlosGalisteo/catastro_mcp_server/archive/refs/tags/v0.1.1.zip" catastro_mcp_server
```
## Solución de problemas (Troubleshooting)
- **No aparecen las herramientas en Claude Desktop**
  - Revisa **Ver registros** del servidor Catastro en Claude.
  - Asegúrate de que `uvx` funciona en tu terminal: `uvx --version`.
  - Si `command: "uvx"` falla en Windows, usa la **Opción B** con ruta absoluta (`where uvx`).

- **Errores HTTP / bloqueos (403/429) o respuestas lentas**
  - Los servicios del Catastro son públicos pero pueden aplicar limitaciones.
  - Espera y reintenta más tarde; evita lanzar muchas peticiones seguidas.

## Licencia
Este servidor MCP está licenciado bajo la Licencia MIT. Esto significa que puedes usar, modificar y redistribuir el software, siempre que se cumplan los términos de dicha licencia. Para más detalles, consulta el archivo `LICENSE` incluido en el repositorio.

Copyright (c) 2026 Carlos Galisteo

## Links
- [Servicios web libres (Sede Electrónica del Catastro)](https://www.catastro.hacienda.gob.es/ws/Webservices_Libres.pdf)
- [Servicios INSPIRE de Cartografía Catastral](https://www.catastro.hacienda.gob.es/webinspire/index.html)
