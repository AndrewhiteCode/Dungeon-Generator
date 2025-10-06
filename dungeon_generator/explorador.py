from __future__ import annotations
from typing import Tuple, List, Optional, Dict
from collections import deque
from .mapa import Mapa
from .habitacion import Habitacion
from .contenido import Tesoro, Monstruo, Jefe, Evento
import random

class Explorador:
    def __init__(self, mapa: Mapa, posicion: Optional[Tuple[int,int]] = None, vida: int = 5, ataque_base: int = 1):
        self.mapa = mapa
        if posicion is None:
            inicio = mapa.habitacion_inicial
            if inicio is None:
                raise ValueError("El mapa no tiene habitación inicial definida")
            self.posicion_actual = tuple(inicio.pos)
        else:
            self.posicion_actual = tuple(posicion)
        self.vida = int(vida)
        self.ataque_base = int(ataque_base)
        self.inventario: List = []
        self.equipado: Dict[str, Optional[object]] = {}  
        self.buffs: List[dict] = []  

    @property
    def esta_vivo(self) -> bool:
        return self.vida > 0

    def recibir_dano(self, cantidad: int):
        cantidad = int(cantidad)
        self.vida = max(0, self.vida - cantidad)

    def calcular_ataque(self) -> int:
        total = int(self.ataque_base)
        for slot, obj in (self.equipado or {}).items():
            if obj and isinstance(obj, object):
                eff = getattr(obj, "efecto", {}) or {}
                total += int(eff.get("ataque", 0))
        for b in (self.buffs or []):
            total += int(b.get("ataque", 0))
        return max(1, total)

    def equipar(self, objeto) -> str:
        if getattr(objeto, "categoria", "") != "equipable":
            return "Ese objeto no es equipable."
        eff = getattr(objeto, "efecto", {}) or {}
        slot = eff.get("slot", "ring")
        prev = self.equipado.get(slot)
        self.equipado[slot] = objeto
        if objeto in self.inventario:
            self.inventario.remove(objeto)
        if prev:
            self.inventario.append(prev)
            return f"Has equipado {objeto.nombre}. {prev.nombre} devuelto al inventario."
        return f"Has equipado {objeto.nombre} en slot {slot}."

    def usar(self, objeto) -> str:
        if objeto not in self.inventario:
            return "No tienes ese objeto en el inventario."
        if getattr(objeto, "categoria", "") != "consumible":
            return "Ese objeto no es consumible."
        eff = getattr(objeto, "efecto", {}) or {}
        modo = eff.get("modo", "permanente")
        if "ataque" in eff:
            val = int(eff.get("ataque", 0))
            if modo == "permanente":
                self.ataque_base += val
                self.inventario.remove(objeto)
                return f"Has usado {objeto.nombre}. Ataque base incrementado en {val}."
            elif modo == "temporal_habitaciones":
                dur = int(eff.get("habitaciones", 1))
                self.buffs.append({"ataque": val, "restante_habitaciones": dur})
                self.inventario.remove(objeto)
                return f"Has usado {objeto.nombre}. +{val} ataque por {dur} habitaciones."
        if eff.get("tipo") == "curar":
            amt = int(eff.get("valor", 1))
            self.vida += amt
            self.inventario.remove(objeto)
            return f"Has usado {objeto.nombre} y recuperas {amt} PV."
        self.inventario.remove(objeto)
        return f"Has usado {objeto.nombre}."

    def obtener_habitaciones_adyacentes(self) -> List[str]:
        hab = self.mapa.habitaciones.get(tuple(self.posicion_actual))
        if not hab:
            return []
        return list(hab.conexiones.keys())

    def mover(self, direccion: str) -> bool:
        hab = self.mapa.habitaciones.get(tuple(self.posicion_actual))
        if not hab:
            return False
        if direccion not in hab.conexiones:
            return False
        otra = hab.conexiones[direccion]
        self.posicion_actual = tuple(otra.pos)
        otra.visitada = True
        nuevos = []
        for b in (self.buffs or []):
            b["restante_habitaciones"] -= 1
            if b["restante_habitaciones"] > 0:
                nuevos.append(b)
        self.buffs = nuevos
        return True

    def explorar_habitacion(self) -> str:
        hab = self.mapa.habitaciones.get(tuple(self.posicion_actual))
        if not hab:
            return "No hay habitación en tu posición."
        if hab.visitada and hab.contenido is None:
            return "Ya visitaste esta habitación y está vacía."
        if hab.contenido is None:
            hab.visitada = True
            return "La habitación está vacía."
        contenido = hab.contenido
        resultado = contenido.interactuar(self)
        if isinstance(contenido, Tesoro):
            hab.contenido = None
        elif isinstance(contenido, Evento):
            hab.contenido = None
        elif isinstance(contenido, (Monstruo, Jefe)):
            enemigo_vivo = getattr(contenido, "vida", 1) > 0
            if not enemigo_vivo:
                hab.contenido = None
        hab.visitada = True
        return resultado

    def encontrar_camino(self, destino: Tuple[int,int]) -> list:
        start = tuple(self.posicion_actual)
        if start == destino:
            return []
        q = deque([start])
        prev = {start: None}
        while q:
            cur = q.popleft()
            hab = self.mapa.habitaciones[cur]
            for dir_name, otra in hab.conexiones.items():
                coord = tuple(otra.pos)
                if coord not in prev:
                    prev[coord] = (cur, dir_name)
                    if coord == destino:
                        path = []
                        node = coord
                        while prev[node] is not None:
                            pcoord, pdirection = prev[node]
                            path.append((pdirection, node))
                            node = pcoord
                        path.reverse()
                        return path
                    q.append(coord)
        return []

    def mover_hasta(self, destino: Tuple[int,int]) -> bool:
        path = self.encontrar_camino(destino)
        if not path:
            return False
        for direccion, coord in path:
            if not self.esta_vivo:
                return False
            moved = self.mover(direccion)
            if not moved:
                return False
            hab = self.mapa.habitaciones.get(tuple(self.posicion_actual))
            if hab and hab.contenido is not None:
                resultado = self.explorar_habitacion()
                if resultado:
                    print(resultado)
                if not self.esta_vivo:
                    return False
        return True

    def __repr__(self):
        return f"Explorador(pos={self.posicion_actual}, vida={self.vida}, atk={self.calcular_ataque()}, inv={len(self.inventario)})"
