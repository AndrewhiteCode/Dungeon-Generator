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
        Genera n_habitaciones conectadas, con el spawn siempre en el borde.
        Estrategia:
        - Elegir spawn en borde (_coords_en_borde()).
        - Mantener frontier de celdas adyacentes a las existentes.
        - Priorizar candidatos más alejados del conjunto existente para esparcir habitaciones.
        - Cuando se añade una habitación, intentar conectar con 1 vecino válido y con
            cierta probabilidad añadir conexiones adicionales para densificar.
        - Si la frontier se vacía antes de alcanzar n_habitaciones, reconstruir frontier desde existentes.
        """
        if n_habitaciones <= 0:
            raise ValueError("n_habitaciones debe ser >= 1")
        max_posibles = self.ancho * self.alto
        if n_habitaciones > max_posibles:
            raise ValueError("Demasiadas habitaciones para el tamaño del mapa")

        import random

        self.habitaciones.clear()
        self._next_id = 0

        # elegir inicio en borde
        posibles_bordes = self._coords_en_borde()
        inicio_coord = random.choice(posibles_bordes)
        inicio = Habitacion(self._next_id, inicio_coord, inicial=True)
        self._next_id += 1
        self.habitaciones[inicio_coord] = inicio
        self.habitacion_inicial = inicio

        deltas = {"norte": (0, -1), "sur": (0, 1), "este": (1, 0), "oeste": (-1, 0)}
        existing = set([inicio_coord])

        # frontier = celdas adyacentes libres a las habitaciones existentes
        frontier = set()
        for dx, dy in deltas.values():
            nx, ny = inicio_coord[0] + dx, inicio_coord[1] + dy
            if 0 <= nx < self.ancho and 0 <= ny < self.alto:
                frontier.add((nx, ny))

        def repoblar_frontier():
            """Si frontier se vacía, reconstruirla mirando alrededor de todas las existing."""
            f = set()
            for ex in existing:
                for dx, dy in deltas.values():
                    nx, ny = ex[0] + dx, ex[1] + dy
                    if 0 <= nx < self.ancho and 0 <= ny < self.alto:
                        coord = (nx, ny)
                        if coord not in existing and coord not in self.habitaciones and coord not in f:
                            f.add(coord)
            return f

        def distancia_min_a_existentes(coord):
            return min(abs(coord[0] - e[0]) + abs(coord[1] - e[1]) for e in existing)

        # Probabilidades
        P_ADDITIONAL_CONN = 0.25  
        MAX_ATTEMPT_REPOB = 3     

        repob_intentos = 0
        while self._next_id < n_habitaciones:
            if not frontier:
                
                if repob_intentos >= MAX_ATTEMPT_REPOB:
                    break
                frontier = repoblar_frontier()
                repob_intentos += 1
                if not frontier:
                    continue

            dist_list = [(distancia_min_a_existentes(f), f) for f in frontier]
            dist_list.sort(reverse=True, key=lambda x: x[0])
            top_fraction = 0.5  
            top_k = max(1, int(len(dist_list) * top_fraction))
            candidates = [f for (_, f) in dist_list[:top_k]]
            candidate = random.choice(candidates)

            new_hab = Habitacion(self._next_id, candidate)
            vecinos_existentes = []
            for dir_name, (dx, dy) in deltas.items():
                neighbor = (candidate[0] - dx, candidate[1] - dy)
                if neighbor in existing:
                    vecinos_existentes.append((dir_name, self.habitaciones[neighbor]))

            if not vecinos_existentes:
                frontier.remove(candidate)
                continue

            random.shuffle(vecinos_existentes)
            connected = False
            for dir_name, neigh_hab in vecinos_existentes:
                try:
                    neigh_hab.conectar(dir_name, new_hab)
                    connected = True
                    break
                except Exception:
                    continue

            if not connected:
                frontier.remove(candidate)
                continue

            self.habitaciones[candidate] = new_hab
            self._next_id += 1
            existing.add(candidate)
            frontier.remove(candidate)

            for dx, dy in deltas.values():
                nx, ny = candidate[0] + dx, candidate[1] + dy
                if 0 <= nx < self.ancho and 0 <= ny < self.alto:
                    coord = (nx, ny)
                    if coord not in existing and coord not in frontier and coord not in self.habitaciones:
                        frontier.add(coord)

            if random.random() < P_ADDITIONAL_CONN:
                for dir_name, (dx, dy) in deltas.items():
                    neighbor = (candidate[0] - dx, candidate[1] - dy)
                    if neighbor in existing:
                        neigh_hab = self.habitaciones[neighbor]
                        try:
                            neigh_hab.conectar(dir_name, new_hab)
                        except Exception:
                            pass

        if self._next_id < n_habitaciones:
            for ex in list(existing):
                if self._next_id >= n_habitaciones:
                    break
                for dx, dy in deltas.values():
                    if self._next_id >= n_habitaciones:
                        break
                    nx, ny = ex[0] + dx, ex[1] + dy
                    coord = (nx, ny)
                    if not (0 <= nx < self.ancho and 0 <= ny < self.alto):
                        continue
                    if coord in existing or coord in self.habitaciones:
                        continue
                    new_hab = Habitacion(self._next_id, coord)
                    for dir_name, (ddx, ddy) in deltas.items():
                        if ex[0] + ddx == coord[0] and ex[1] + ddy == coord[1]:
                            try:
                                self.habitaciones[ex].conectar(dir_name, new_hab)
                                self.habitaciones[coord] = new_hab
                                self._next_id += 1
                                existing.add(coord)
                            except Exception:
                                pass
                            break

        if self._next_id < n_habitaciones:
            raise RuntimeError("No se pudieron colocar todas las habitaciones (frontera agotada)")

        if not self.es_todo_accesible():
            raise RuntimeError("Error: mapa generado no es completamente accesible")



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
            base_vida = 5
            base_ataque = 1
            vida = base_vida + (dist // 2)
            ataque = base_ataque + (dist // 4)
            nombre = f"Monstruo(d{dist})"
            return Monstruo(nombre, vida, ataque)

        def crear_jefe_segun_distancia(dist: int) -> Jefe:
            vida = 8 + dist
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
                ataque_bonus = 1 + (dist // 5)
                dur = 2 + (dist // 6)
                efecto = {"tipo": "buff_por_habitaciones", "ataque": ataque_bonus, "habitaciones": dur}
                return Evento("Bonificación", f"+{ataque_bonus} ataque por {dur} habitaciones", efecto)

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
    def obtener_estadisticas_mapa(self) -> dict:
        """
        Retorna: {
        'total': int,
        'vacios': int,
        'tesoros': int,
        'monstruos': int,
        'jefes': int,
        'eventos': int,
        'promedio_conexiones': float
        }
        """
        total = len(self.habitaciones)
        conteos = {"vacios": 0, "tesoros": 0, "monstruos": 0, "jefes": 0, "eventos": 0}
        suma_conex = 0
        for hab in self.habitaciones.values():
            suma_conex += len(hab.conexiones)
            if hab.contenido is None:
                conteos["vacios"] += 1
            else:
                t = getattr(hab.contenido, "tipo", None)
                if t == "tesoro":
                    conteos["tesoros"] += 1
                elif t == "monstruo":
                    conteos["monstruos"] += 1
                elif t == "jefe":
                    conteos["jefes"] += 1
                elif t == "evento":
                    conteos["eventos"] += 1
                else:
                    conteos["vacios"] += 1
        promedio = (suma_conex / total) if total > 0 else 0.0
        resumen = {"Total de habitaciones": total, **conteos, "promedio_conexiones": round(promedio, 2)}
        return resumen