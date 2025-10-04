from __future__ import annotations
import random
from typing import Dict, Tuple, List, Optional
from .habitacion import Habitacion
from collections import deque
import math
from .contenido import Tesoro, Monstruo, Jefe, Evento, contenido_from_dict
from .objetos import Objeto

def manhattan(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

class Mapa:
    def __init__(self, ancho: int, alto: int, seed: Optional[int] = None):
        if ancho <= 0 or alto <= 0:
            raise ValueError("Ancho y alto deben ser positivos")
        self.ancho = ancho
        self.alto = alto
        self.habitaciones: Dict[Tuple[int, int], Habitacion] = {}
        self.habitacion_inicial: Optional[Habitacion] = None
        self._next_id = 0
        if seed is not None:
            random.seed(seed)

    def _coords_en_borde(self) -> List[Tuple[int, int]]:
        bordes = []
        for x in range(self.ancho):
            bordes.append((x, 0))
            bordes.append((x, self.alto - 1))
        for y in range(self.alto):
            bordes.append((0, y))
            bordes.append((self.ancho - 1, y))
        return list(dict.fromkeys(bordes))

    def generar_estructura(self, n_habitaciones: int):
        """
        Genera N habitaciones conectadas garantizando que todas sean accesibles
        desde la habitación inicial.
        """
        max_posibles = self.ancho * self.alto
        if n_habitaciones <= 0:
            raise ValueError("n_habitaciones debe ser >= 1")
        if n_habitaciones > max_posibles:
            raise ValueError("Demasiadas habitaciones para el tamaño del mapa")

        posibles_bordes = self._coords_en_borde()
        inicio_coord = random.choice(posibles_bordes)
        self._next_id = 0
        inicio = Habitacion(self._next_id, inicio_coord, inicial=True)
        self._next_id += 1
        self.habitaciones[inicio_coord] = inicio
        self.habitacion_inicial = inicio

        frontera: List[Habitacion] = [inicio]

        deltas = {"norte": (0, -1), "sur": (0, 1), "este": (1, 0), "oeste": (-1, 0)}

        while self._next_id < n_habitaciones and frontera:
            actual = random.choice(frontera)

            vecinos_libres = []
            for dir_name, (dx, dy) in deltas.items():
                nx, ny = actual.x + dx, actual.y + dy
                if 0 <= nx < self.ancho and 0 <= ny < self.alto and (nx, ny) not in self.habitaciones:
                    vecinos_libres.append((dir_name, (nx, ny)))

            if not vecinos_libres:
                frontera.remove(actual)
                continue

            dir_elegida, (nx, ny) = random.choice(vecinos_libres)
            nueva = Habitacion(self._next_id, (nx, ny))
            self._next_id += 1
            self.habitaciones[(nx, ny)] = nueva

            actual.conectar(dir_elegida, nueva)

            frontera.append(nueva)

        if not self.es_todo_accesible():
            raise RuntimeError("Error: mapa generado no es completamente accesible (esto no debería pasar)")

    def es_todo_accesible(self) -> bool:
        """BFS desde la habitación inicial, verifica que alcance todas las habitaciones."""
        if not self.habitacion_inicial:
            return False
        visitados = set()
        q = deque()
        start = self.habitacion_inicial.pos
        q.append(start)
        visitados.add(start)

        while q:
            coord = q.popleft()
            hab = self.habitaciones[coord]
            for otra in hab.conexiones.values():
                c = otra.pos
                if c not in visitados:
                    visitados.add(c)
                    q.append(c)

        return len(visitados) == len(self.habitaciones)

    def imprimir_ascii(self) -> str:
        """
        Representación ASCII del mapa
        """
        grid = [["  " for _ in range(self.ancho)] for _ in range(self.alto)]
        for (x, y), hab in self.habitaciones.items():
            mark = f"{hab.id:02d}"
            if hab.inicial:
                mark = "S "  
            grid[y][x] = mark

        lines = []
        for y in range(self.alto):
            lines.append(" ".join(grid[y]))
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Serializa el mapa (habitaciones con conexiones por coords)."""
        return {
            "ancho": self.ancho,
            "alto": self.alto,
            "habitaciones": [hab.to_dict() for hab in self.habitaciones.values()],
            "inicio": list(self.habitacion_inicial.pos) if self.habitacion_inicial else None
        }

    @staticmethod
    def from_dict(d: dict) -> "Mapa":
        """Reconstruye mapa desde dict (reconstruye habitaciones y conexiones)."""
        mapa = Mapa(d["ancho"], d["alto"])
        for h in d["habitaciones"]:
            hab = Habitacion.from_dict(h)
            mapa.habitaciones[tuple(hab.pos)] = hab
            mapa._next_id = max(mapa._next_id, hab.id + 1)
        for h in d["habitaciones"]:
            coord = tuple(h["pos"])
            hab_obj = mapa.habitaciones[coord]
            for dir_, coord_other in h.get("conexiones", {}).items():
                coord_other_t = tuple(coord_other)
                if coord_other_t in mapa.habitaciones:
                    otra = mapa.habitaciones[coord_other_t]
                    if dir_ not in hab_obj.conexiones:
                        hab_obj.conectar(dir_, otra)
        inicio_coord = d.get("inicio")
        if inicio_coord:
            mapa.habitacion_inicial = mapa.habitaciones[tuple(inicio_coord)]
        return mapa

    def __repr__(self):
        return f"Mapa({self.ancho}x{self.alto}, habitaciones={len(self.habitaciones)})"
    
    def colocar_contenido(self, seed: Optional[int] = None) -> dict:
        """
        Distribuye contenido en las habitaciones según los porcentajes del enunciado:
        - Jefe 
        - Monstruos: 20-30% de las habitaciones restantes (excluyendo inicio)
        - Tesoros: 15-25%
        - Eventos: 5-10%
        - Resto vacío

        Devuelve un dict resumen: {"jefes":X, "monstruos":Y, "tesoros":Z, "eventos":W}
        """
        if seed is not None:
            random.seed(seed)

        total = len(self.habitaciones)
        if total <= 1:
            return {"jefes": 0, "monstruos": 0, "tesoros": 0, "eventos": 0}

        inicio_coord = tuple(self.habitacion_inicial.pos)
        coords_disponibles = [c for c in self.habitaciones.keys() if c != inicio_coord]
        n_disp = len(coords_disponibles)

        def pct_range(pmin: float, pmax: float) -> Tuple[int, int]:
            base_min = math.ceil(pmin * n_disp)
            base_max = math.floor(pmax * n_disp)
            if base_max < base_min:
                base_max = base_min
            return base_min, base_max

        mon_min, mon_max = pct_range(0.20, 0.30)
        tes_min, tes_max = pct_range(0.15, 0.25)
        evt_min, evt_max = pct_range(0.05, 0.10)

        n_monstruos = random.randint(mon_min, mon_max) if n_disp > 0 else 0
        n_tesoros = random.randint(tes_min, tes_max) if n_disp > 0 else 0
        n_eventos = random.randint(evt_min, evt_max) if n_disp > 0 else 0
        n_jefes = 1 if n_disp > 0 else 0  

        total_asignado = n_monstruos + n_tesoros + n_eventos + n_jefes
        if total_asignado > n_disp:
            exceso = total_asignado - n_disp
            for attr in ("n_monstruos", "n_tesoros", "n_eventos"):
                if exceso <= 0:
                    break
                val = locals()[attr]
                reduc = min(val, exceso)
                locals()[attr] = val - reduc
                exceso -= reduc
            n_monstruos = locals()["n_monstruos"]
            n_tesoros = locals()["n_tesoros"]
            n_eventos = locals()["n_eventos"]

        random.shuffle(coords_disponibles)
        it = iter(coords_disponibles)

        asignadas = {"jefes": [], "monstruos": [], "tesoros": [], "eventos": []}

        def crear_monstruo_segun_distancia(dist: int) -> Monstruo:
            base_vida = 4
            base_ataque = 1
            vida = base_vida + (dist // 2)
            ataque = base_ataque + (dist // 4)
            nombre = f"Monstruo(d{dist})"
            return Monstruo(nombre, vida, ataque)

        def crear_jefe_segun_distancia(dist: int) -> Jefe:
            vida = 12 + dist
            ataque = 3 + (dist // 3)
            recompensa = Objeto(f"TesoroJefe(d{dist})", valor=50 + dist * 5, descripcion="Recompensa de jefe")
            nombre = f"Jefe(d{dist})"
            return Jefe(nombre, vida, ataque, recompensa)

        def crear_tesoro_segun_distancia(dist: int) -> Tesoro:
            valor = 10 + dist * 2
            obj = Objeto(f"Gema(d{dist})", valor=valor, descripcion=f"Tesoro en distancia {dist}")
            return Tesoro(obj)

        def crear_evento_aleatorio(dist: int) -> Evento:
            tipo_evt = random.choice(["trampa", "fuente", "portal", "buff"])
            if tipo_evt == "trampa":
                efecto = {"tipo": "trampa", "valor": 1 + (dist // 3)}
                return Evento("Trampa", "Una trampa que hiere al explorador", efecto)
            elif tipo_evt == "fuente":
                efecto = {"tipo": "curar", "valor": 1 + (dist // 4)}
                return Evento("Fuente", "Restauradora", efecto)
            elif tipo_evt == "portal":
                efecto = {"tipo": "portal"}
                return Evento("Portal", "Teletransportador", efecto)
            else:
                efecto = {"tipo": "buff", "detalle": f"+1 daño por {1 + dist//5} turnos"}
                return Evento("Bonificación", "Aumenta temporalmente tus estadísticas", efecto)

        if n_jefes > 0:
            coord = next(it)
            dist = manhattan(coord, inicio_coord)
            jefe = crear_jefe_segun_distancia(dist)
            self.habitaciones[coord].contenido = jefe
            asignadas["jefes"].append(coord)

        for _ in range(n_monstruos):
            try:
                coord = next(it)
            except StopIteration:
                break
            dist = manhattan(coord, inicio_coord)
            mon = crear_monstruo_segun_distancia(dist)
            self.habitaciones[coord].contenido = mon
            asignadas["monstruos"].append(coord)

        for _ in range(n_tesoros):
            try:
                coord = next(it)
            except StopIteration:
                break
            dist = manhattan(coord, inicio_coord)
            tes = crear_tesoro_segun_distancia(dist)
            self.habitaciones[coord].contenido = tes
            asignadas["tesoros"].append(coord)

        for _ in range(n_eventos):
            try:
                coord = next(it)
            except StopIteration:
                break
            dist = manhattan(coord, inicio_coord)
            ev = crear_evento_aleatorio(dist)
            self.habitaciones[coord].contenido = ev
            asignadas["eventos"].append(coord)

        
        resumen = {k: len(v) for k, v in asignadas.items()}
        return resumen
