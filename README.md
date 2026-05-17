# PlantillaPro Studio

Aplicacion de escritorio para generar documentos personalizados por lotes desde una imagen base. Esta pensada para plantillas escolares, certificados, diplomas, etiquetas, credenciales o cualquier diseno donde se deba rellenar un area con datos variables.

## Funciones principales

- Carga de imagenes PNG, JPG y JPEG sin deformarlas.
- Canvas central con zoom por rueda, pan con boton medio o `Espacio + arrastrar`.
- Creacion, movimiento, redimensionado con ocho tiradores, duplicado y borrado de rectangulos de texto.
- Campos configurables con plantilla `{{nombre}}`, fuente del sistema o TTF externo, tamano, color, alineacion, margen, autoajuste, mayusculas/minusculas/capitalizacion, interlineado, salto de linea, corte cada N palabras y borde opcional.
- Carga de datos desde TXT, CSV, XLSX o portapapeles.
- Tabla editable para agregar, borrar o modificar filas.
- Boton **Generar** que abre el visor interno con el lote renderizado, navegacion por filas, impresion directa, guardado PDF y exportacion de imagenes.
- Exportacion a PDF unico con una pagina por fila.
- Exportacion opcional de imagenes individuales PNG/JPG con nombres sanitizados para Windows.
- Guardado y apertura de proyectos JSON.

## Instalacion

Requiere Python 3.11 o superior.

```powershell
cd C:\Users\ll\Desktop\template\template_batch_printer
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Ejecucion

```powershell
python main.py
```

## Uso paso a paso

1. Abrir la aplicacion.
2. Pulsar **Cargar imagen** y seleccionar la plantilla PNG/JPG.
3. Dibujar un rectangulo con el mouse sobre el area donde debe aparecer el texto.
4. En el panel derecho configurar el campo:
   - Nombre: `nombre`
   - Texto: `{{nombre}}`
   - Fuente del sistema o archivo TTF externo.
   - Transformar texto: `normal`, `upper`, `lower` o `title`.
   - Palabras por linea: `0` para automatico o, por ejemplo, `2` para cortar nombres en grupos de dos palabras.
   - Alineacion horizontal: `center`.
   - Alineacion vertical: `center`.
   - Autoajustar: activado.
5. Cargar datos con **Cargar datos** o **Pegar lista**.
6. Revisar la tabla editable.
7. Pulsar **Generar** para abrir el visor del lote.
8. Desde el visor se puede imprimir la pagina actual o todo el lote sin exportar PDF.
9. Opcionalmente pulsar **Generar PDF** o **Exportar imagenes**.

## Datos soportados

- TXT: un nombre por linea.
- CSV: con o sin encabezados.
- XLSX: usa la primera hoja. Si detecta encabezados como `nombre`, `curso`, `fecha`, los usa como variables.
- Portapapeles: una linea por nombre o columnas separadas por tabulador.

Los campos de texto pueden usar variables como:

```text
{{nombre}}
{{numero}} - {{nombre}}
Alumno/a: {{nombre}}
```

`{{numero}}` se agrega automaticamente durante la generacion.

## Tamano de salida

En el panel izquierdo se puede elegir:

- tamano original de la imagen,
- A4 vertical/horizontal,
- carta vertical/horizontal,
- tamano personalizado en pixeles.

El DPI por defecto es 300. Si se elige un tamano distinto al original, la imagen renderizada se ajusta manteniendo proporcion sobre una pagina blanca.

## Guardar proyectos

Usa **Guardar**, **Guardar como** y **Abrir proyecto**. El JSON guarda:

- ruta de la imagen base,
- dimensiones,
- campos creados,
- estilos,
- datos cargados,
- configuracion de salida.

## Tests

```powershell
cd C:\Users\ll\Desktop\template\template_batch_printer
python -m pytest
```

Los tests cubren carga TXT/CSV/XLSX, sustitucion de variables, sanitizacion de nombres, renderizado basico y generacion de PDF de prueba.

## Empaquetar como EXE en Windows

```powershell
cd C:\Users\ll\Desktop\template\template_batch_printer
.\build_windows.bat
```

El ejecutable queda en:

```text
dist\PlantillaProStudio\PlantillaProStudio.exe
```

El usuario final no necesita instalar Python si recibe la carpeta completa generada por PyInstaller.

## Estructura

```text
template_batch_printer/
  main.py
  app/
    ui/
      main_window.py
      canvas_widget.py
      data_table.py
      field_properties_panel.py
      preview_dialog.py
    core/
      models.py
      renderer.py
      pdf_exporter.py
      image_exporter.py
      data_loader.py
      project_io.py
      filename_utils.py
    tests/
  assets/
  requirements.txt
  README.md
  build_windows.bat
```

## Limitaciones conocidas

- La impresion directa depende del controlador instalado en Windows.
- La seleccion de fuente del sistema se renderiza con las fuentes disponibles en `C:\Windows\Fonts`; tambien se puede forzar un archivo TTF/OTF.
- La exportacion se ejecuta en la ventana principal con barra de progreso y cancelacion; para lotes enormes conviene mantener la app sin otras acciones hasta finalizar.
