# Replicación fiel de PDFs

Guía reutilizable para generar un PDF **visualmente idéntico** a un original y
añadirle contenido encima, sin que lo original se desplace, se corte ni cambie
de página.

El flujo que se sigue aquí es *analizar → generar → verificar*, y la verificación
es cuantitativa: no se da por bueno un documento hasta que las mediciones cuadran.

---

## 1. Requisitos

```bash
apt-get install -y poppler-utils libreoffice fonts-liberation
pip install python-docx pillow numpy
```

| Herramienta | Para qué |
|---|---|
| `poppler-utils` | `pdftotext`, `pdfinfo`, `pdffonts`, `pdftoppm`, `pdfimages`, `pdftohtml` |
| `libreoffice` | conversión DOCX → PDF en headless |
| `python-docx` | generación del documento |
| `Pillow`, `numpy` | comparación a nivel de píxel |

No uses LaTeX para replicar un PDF hecho en Word: desajusta tipografía, cajas y
saltos de línea.

### Fuentes: compruébalas antes de escribir código

```bash
pdffonts original.pdf
fc-list | grep -iE "arial|roboto mono"
```

Si las fuentes del original no están instaladas, LibreOffice las sustituye
(Arial → Liberation Sans, Roboto Mono → DejaVu Sans Mono). Las métricas no
coinciden, las líneas cambian de ancho, el texto refluye y **todo se desplaza**.
Instálalas si puedes; si no, decláralo como limitación conocida y no presentes el
resultado como idéntico.

---

## 2. Estructura de trabajo

```
proyecto/
├── original.pdf          # intocable, solo lectura
├── orig.xml              # geometría del original (generado)
├── new.xml               # geometría del generado (generado)
├── orig-1.png            # renders del original a 150 ppp
├── new-1.png             # renders del generado a 150 ppp
├── generar.py            # script que produce el DOCX
└── salida/
    ├── documento.docx
    └── documento.pdf
```

Nunca sobrescribas el original. Trabaja siempre sobre renderizados y copias.

---

## 3. Fase 1 — Analizar el original

```bash
pdfinfo original.pdf                  # nº de páginas, tamaño exacto de página
pdffonts original.pdf                 # fuentes y si van embebidas
pdftohtml -xml -hidden -stdout original.pdf > orig.xml
pdftoppm -png -r 150 original.pdf orig
pdfimages -png -f 1 -l 1 original.pdf img
```

El XML de `pdftohtml` da, por bloque de texto, `top`, `left` y `width`
**en píxeles a 150 ppp**:

```
pt  = valor / 1.5
cm  = pt / 28.3465
```

Antes de generar nada, extrae y anota en una tabla:

- texto de cada bloque, con su posición, cuerpo y color (`#rrggbb`)
- el conjunto **exacto** de estilos `fontspec` que usa el original
- posición y tamaño en cm de cada imagen
- todos los trazos y recuadros (ver fase 4: no se ven en el XML)
- **dónde hay espacio libre real** para lo nuevo

Regla de oro: el enunciado no se reescribe. Se copia literal desde el XML, en el
mismo orden, y las respuestas van después de cada apartado. Si el enunciado exige
una firma concreta (p. ej. `plot_decision_tree(model)`), se cumple esa firma
aunque resulte menos cómoda.

---

## 4. Fase 2 — Generar el documento

Con `python-docx`, replicando del original:

- tamaño de página exacto en puntos (`section.page_width`, `page_height`)
- márgenes y `header_distance` / `footer_distance` en puntos
- un estilo base con la fuente y el cuerpo correctos
- colores en `w:color` (`#000000`, `#1154cc` para enlaces, `#ff0000` para avisos)
- los párrafos originales intactos; lo nuevo va en párrafos nuevos

Para imágenes:

```python
# python-docx solo admite centímetros en tamaño; el alto se deriva del aspect ratio
from PIL import Image
px_w, px_h = Image.open(ruta).size
ancho_cm = 15.5                      # medido en la fase 1, no al azar
alto_cm  = ancho_cm * px_h / px_w
doc.add_picture(ruta, width=Cm(ancho_cm))
```

Nunca estires una imagen, y limita el ancho al hueco real medido para que no
desborde ni empuje a la página siguiente.

Convertir a PDF:

```bash
soffice --headless --convert-to pdf --outdir salida salida/documento.docx
```

---

## 5. Fase 3 — Verificar el texto

Cuantitativo y obligatorio. **0 palabras del original pueden desaparecer.**

```python
import difflib, re
import xml.etree.ElementTree as ET


def palabras(xml):
    root = ET.parse(xml).getroot()
    txt = " ".join("".join(p.itertext()) for p in root.iter("page"))
    return re.sub(r"\s+", " ", txt.replace("\u00ad", "")).split()


ow, nw = palabras("orig.xml"), palabras("new.xml")
perdidas = [
    w
    for tag, i1, i2, _, _ in difflib.SequenceMatcher(a=ow, b=nw, autojunk=False)
    .get_opcodes()
    if tag == "delete"
    for w in ow[i1:i2]
]
print("Palabras ausentes:", len(perdidas))
```

Desviación vertical de la primera página:

```python
def bloques(xml, pagina=0):
    pg = list(ET.parse(xml).getroot().iter("page"))[pagina]
    por_y = {}
    for t in pg.findall("text"):
        s = " ".join("".join(t.itertext()).split())
        if s:
            por_y.setdefault(int(t.get("top")) / 1.5, []).append(s)
    return sorted((y, " ".join(v)) for y, v in por_y.items())


anchor = {}
for y, s in bloques("orig.xml"):
    anchor.setdefault(s[:44], []).append(y)

desv = [y - anchor[s[:44]].pop(0) for y, s in bloques("new.xml") if s[:44] in anchor]
print(f"desviación máx={max(map(abs, desv)):.1f}pt  media={sum(desv)/len(desv):+.2f}pt")
```

Comprobar además:

- número de páginas idéntico al original
- estilos: el conjunto de `(tamaño, color)` del nuevo PDF debe ser **igual** al
  del original. Si añades texto, reutiliza estilos existentes; no introduzcas
  combinaciones nuevas
- enlaces: extrae `/URI` del PDF y los `Target` de `word/_rels/document.xml.rels`
  del DOCX y compáralos carácter a carácter con la lista esperada

```bash
python -c "
import re; d=open('salida/documento.pdf','rb').read()
print(sorted(set(re.findall(rb'/URI\s*\((.*?)\)', d))))"
```

---

## 6. Fase 4 — Verificar los gráficos

**`pdftohtml` no sirve para esto.** Solo devuelve la matriz de transformación, así
que siempre da la imagen por correcta aunque esté recortada o invisible. Hay que
renderizar y medir píxeles.

```bash
pdftoppm -png -r 150 -f 1 -l 1 salida/documento.pdf new
# ojo: el archivo sale new-1.png, con el número de página al final
```

Detección de líneas finas (bordes de tabla, reglas, recuadros, subrayados):

```python
from PIL import Image

PT = 72 / 150          # el render es a 150 ppp


def lineas(ruta, min_largo=300, min_continuidad=0.8):
    im = Image.open(ruta).convert("L")
    W, H = im.size
    px = im.load()
    out = []
    for y in range(H):
        xs = [x for x in range(W) if px[x, y] < 250]      # ver trampa 6
        if not xs:
            continue
        span = (max(xs) - min(xs)) * PT
        if span > min_largo and len(xs) * PT > span * min_continuidad:
            out.append({
                "y": round(y * PT, 2),
                "x0": round(min(xs) * PT, 2),
                "x1": round(max(xs) * PT, 2),
                "gris": min(px[x, y] for x in xs),
            })
    return out
```

Con esto se comparan, original contra generado, posición y **gris** de cada
trazo. Un borde de tabla negro donde el original es gris `#888888` se detecta
aquí y en ningún otro sitio.

Mide con **el mismo criterio** los dos documentos. Aplicar umbrales distintos a
cada uno produce falsos positivos: un subrayado «demasiado largo» puede ser en
realidad el mismo subrayado cortado en dos por el anti-aliasing.

---

## 7. Trampas conocidas

1. **`line_spacing = Pt(1)` recorta las imágenes.** El recuadro de línea se
   encoge por debajo del alto del inline shape y la imagen desaparece al
   convertir. Usa `line_spacing = 1.0` y controla el espacio con
   `space_before` / `space_after`. Si una imagen no sale, mira aquí primero.

2. **Un logo con fondo transparente necesita su `smask`.** Busca el objeto `/SMask`
   en el PDF y aplícalo sobre el canal alfa; si no, la imagen sale con caja
   blanca o recortada.

3. **`python-docx` solo admite tamaños de imagen en centímetros.** Convertir
   siempre desde los píxeles reales para no deformarla.

4. **Sustitución de fuentes.** Sin las fuentes originales, un enlace puede partir
   línea una palabra antes y desalinear el bloque entero.

5. **Subrayado parcial ≠ subrayado continuo.** Mide cobertura además de extensión,
   y con el mismo umbral en ambos documentos.

6. **Los grises claros desaparecen con umbrales altos.** Con `luma < 128` una
   regla de gris 136 es *invisible* para el detector: se creerá que falta en el
   generado cuando lo que falta es la medición. Usa 250.

7. **Los huecos `____` de un formulario no son un error si los rellenas.**
   Si el original deja `Nombre: ______` y tú lo rellenas, la línea de guiones
   desaparece del renderizado. Es intencional, pero conviene decidirlo y verificarlo.

8. **`bbox_inches="tight"` en matplotlib cambia el tamaño de la figura.** Al
   insertar, mide el PNG *ya* generado, no el tamaño que crees que tiene.

---

## 8. Checklist de aceptación

| Comprobación | Criterio |
|---|---|
| Palabras del original ausentes | **0** |
| Número de páginas | idéntico al original |
| Desviación vertical máx. (pág. 1) | ≤ 2 pt |
| Estilos `(tamaño, color)` | conjunto idéntico |
| Enlaces (PDF y DOCX) | coinciden carácter a carácter |
| Trazos y recuadros | mismos que en el original, posición y gris |
| Imágenes | visibles, sin recorte, sin deformar |
| Tablas | mismo número de filas y columnas que el original |
| Reproducibilidad | reejecutar el script no cambia los artefactos |

Verifica la reproducibilidad comparando hashes antes y después de reejecutar:

```bash
md5sum modelo.pkl > prev.md5
python script.py && md5sum -c prev.md5
```

---

## 9. Utilidades

Comparar el hash del ZIP con el de la carpeta para asegurar que el paquete lleva
lo mismo que la carpeta:

```python
import hashlib, zipfile, pathlib

carpeta = {p.as_posix(): hashlib.md5(p.read_bytes()).hexdigest()
           for p in sorted(pathlib.Path("carpeta").rglob("*")) if p.is_file()}
with zipfile.ZipFile("entrega.zip") as z:
    en_zip = {n: hashlib.md5(z.read(n)).hexdigest()
              for n in z.namelist() if not n.endswith("/")}

print("coincide:", carpeta == en_zip)
for n in sorted(set(carpeta) | set(en_zip)):
    if carpeta.get(n) != en_zip.get(n):
        print("  DIFERENTE:", n)
```

Y comprobar el ZIP extrayéndolo en limpio antes de entregar:

```bash
unzip -t entrega.zip
rm -rf /tmp/verif && mkdir -p /tmp/verif
unzip -q entrega.zip -d /tmp/verif
python /tmp/verif/entrega/recursos/script.py
```

Si el script corre bien desde la copia extraída y reproduce los mismos hashes,
el paquete es ejecutable de verdad.