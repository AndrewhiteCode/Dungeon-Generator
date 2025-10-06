# Dungeon_Generator

Tarea de Programacion Orientada a Objetos para la asignatura **Bases de Datos 2** 

---

## Resumen
Este proyecto genera un mapa conectado de habitaciones y coloca contenido aleatorio (monstruos, jefes, tesoros y eventos). Incluye:

- Movimiento paso a paso y movimiento automático hacia coordenadas.
- Combates con logs detallados.
- Objetos que afectan las estadísticas del explorador.
- Eventos: teletransportes, curas, trampas, buffs temporales y cambios de ataque.
- Guardado y carga de partidas (JSON).
- Interfaz de consola (`main.py`) que redibuja una única vista (mapa + minimapa + panel de estado + logs).

---

## Requisitos y ejecución rápida

1. Clonar o descargar el repositorio en una carpeta local, por ejemplo `dungeon_project`.

2. Tambien puede crear un entorno virtual:

```bash
python -m venv venv
#      Windows
venv\Scripts\activate

#       Linux
source venv/bin/activate
```

3. Instalar  `rich`:

```bash
#Opcion 1
pip install -r requirements.txt 
#Opcion 2
pip install rich
```

4. Ejecuta la consola interactiva:

```bash
python main.py
```

---

## Comandos disponibles (consola interactiva)

- `mover` — mueve un paso en una dirección **aleatoria** válida desde la habitación actual.  
- `ir x,y` — camina **paso a paso** hasta `(x,y)`; muestra cada paso y las interacciones.    
- `guardar [ruta]` — guarda la partida (por defecto `prueba.json`). Imprime la ruta absoluta.  
- `cargar [ruta]` — carga la partida. Si se usa `cargar` sin argumento o `cargar seleccionar`, lista los archivos `*.json` y permite elegir por índice. Cargar borra logs anteriores.  
- `reinicio`  — reinicia la partida (nuevo mapa con mismos parámetros).  
- `estado` — refresca/redibuja la pantalla.  
- `ayuda`  — muestra ayuda.  
- `salir` — pide confirmación `y/n` antes de salir.

---

## Estructura principal del repositorio

```
dungeon_project/
      ├─ main.py            # Interfaz de consola
      ├─ main_prueba.py                    # Demo
      ├─ README.md
      ├─ uv.lock
      └─ pyproject.toml
      ├─ dungeon_generator/
          ├─ mapa.py                 # Generador de mapa y colocación de contenido
          ├─ habitacion.py           # Clase Habitacion
          ├─ explorador.py           # Explorador: movimiento, stats, inventario, buffs
          ├─ contenido.py            # Tesoro, Monstruo, Jefe, Evento (interactuar())
          ├─ objetos.py              # Clase Objeto (categoria, efecto)
          ├─ serializacion.py        # guardar_partida / cargar_partida
          └─ visualizador.py         # visualización con rich


```

---

## Detalles técnicos y diseño

### Generador de mapa
- Generador estratificado que busca dispersar las habitaciones por toda la rejilla.
- La habitación inicial siempre se coloca en un borde.
- La generación garantiza conectividad sin habitaciones inaccesibles.

### Contenido y colocación
- `colocar_contenido()` reparte: monstruos, jefes, tesoros y eventos respetando porcentajes y seed.
- Los eventos incluyen: `curar`, `trampa`, `teleport`, `buff_por_habitaciones`, `modificar_ataque`.

### Explorador y combate
- `Explorador` tiene `vida`, `ataque_base`, `inventario`, `equipado` y `buffs`.
- `calcular_ataque()` suma `ataque_base` + efectos de equipo + buffs activos.
- Combate: `Monstruo.interactuar()` usa `explorador.calcular_ataque()` para calcular daño del jugador; los logs detallas cada ataque.

### Objetos y tesoros
- `Objeto` incluye campos: `nombre`, `valor`, `descripcion`, `categoria` (`consumible`/`equipable`/`normal`) y `efecto` (dict).
- `Tesoro` añade objetos al inventario; consumibles pueden usarse y equipables pueden equiparse (comando `equipar`).

### Eventos
- `Evento.interactuar()` soporta múltiples efectos:
  - `curar`: aumenta vida.
  - `trampa`: quita vida.
  - `teleport`: teletransporta a habitación aleatoria (opción `auto_explore` para explorar destino).
  - `buff_por_habitaciones`: +ataque por N habitaciones.
  - `modificar_ataque`: altera ataque permanente o temporal.

---

## Guardado y carga
- Guardado en JSON con `guardar_partida(mapa, explorador, ruta)`.
- Carga reconstruye mapa y explorador; al cargar se limpia el historial de logs para evitar mostrar sucesos previos (por ejemplo, muertes antiguas).

---

## Tabla de cumplimiento de requisitos

| Requisito | Estado | Observación |
|---|---:|---|
| Generar mapa conectado | Cumplido | Inicio en borde, mapas accesibles |
| Colocar contenido con porcentajes | Cumplido | Monstruos/tesoros/eventos/jefes distribuidos |
| Movimiento y pathfinding | Cumplido | `mover` (aleatorio) y `ir x,y` (BFS) |
| Interacciones: tesoro, monstruo, jefe, evento | Cumplido | Logs detallados y efectos aplicados |
| Objetos con efectos (gema, anillo) | Parcial | Falta complementar efectos |
| Guardar/Cargar | Cumplido | Carga limpia logs |
| Visualización (mapa + minimapa) | Cumplido | Consola redibuja una sola vista |
| Documentación | Cumplido | Este README |

---

## Tests

Ejecutar:
```bash
python -m pytest -q
```
(Se pueden ejecutar tests básicos.)

---

## Generacion de `uv.lock`

1. Instalar `uv` con pipx :
```bash
pipx install uv
```

2. Generar el lockfile desde la raíz del proyecto (donde está `pyproject.toml`):
```bash
uv lock
```

3. Añadir `uv.lock` al repositorio:
```bash
git add uv.lock
git commit -m "Add uv.lock"
git push
```

---

## Notas finales y conclusiones
Se a disfrutado creando este mini juego se han reforzado conocimientos en el area de la POO , Agradezco que haya llegado hasta esta parte del readme 

sin mas que agregar me despido 

Atentamente

### Andres Barbosa


