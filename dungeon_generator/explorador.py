from __future__ import annotations
from typing import Tuple, List, Optional
from .mapa import Mapa
from .habitacion import Habitacion
from .contenido import Tesoro, Monstruo, Jefe, Evento
import random

class Explorador:
    def __init__(self, mapa: Mapa, posicion: Optional[Tuple[int,int]] = None, vida: int = 5):
        self.mapa = mapa
        if posicion is None:
            inicio = mapa.habitacion_inicial
            if inicio is None:
                raise ValueError("El mapa no tiene habitación inicial definida")
            self.posicion_actual = tuple(inicio.pos)
        else:
            self.posicion_actual = tuple(posicion)
        self.vida = int(vida)
        self.inventario: List = []

    @property
    def esta_vivo(self) -> bool:
        return self.vida > 0

    def recibir_dano(self, cantidad: int):
        cantidad = int(cantidad)
        self.vida = max(0, self.vida - cantidad)

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

    def __repr__(self):
        return f"Explorador(pos={self.posicion_actual}, vida={self.vida}, inv={len(self.inventario)})"
