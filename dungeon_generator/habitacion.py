from __future__ import annotations
from typing import Dict, Optional, Tuple
from .contenido import ContenidoHabitacion  


class Habitacion:
    def __init__(self, id: int, pos: Tuple[int, int], inicial: bool = False):
        self.id: int = id
        self.pos: Tuple[int, int] = (int(pos[0]), int(pos[1]))
        self.inicial: bool = inicial
        self.contenido: Optional[ContenidoHabitacion] = None
        self.conexiones: Dict[str, "Habitacion"] = {}
        self.visitada: bool = False

    @property
    def x(self) -> int:
        return self.pos[0]

    @property
    def y(self) -> int:
        return self.pos[1]

    def conectar(self, direccion: str, otra: "Habitacion"):
        opuestos = {"norte": "sur", "sur": "norte", "este": "oeste", "oeste": "este"}
        if direccion not in opuestos:
            raise ValueError(f"Dirección inválida: {direccion}")
        self.conexiones[direccion] = otra
        otra.conexiones[opuestos[direccion]] = self

    def desconectar(self, direccion: str):
        opuestos = {"norte": "sur", "sur": "norte", "este": "oeste", "oeste": "este"}
        if direccion in self.conexiones:
            otra = self.conexiones.pop(direccion)
            opp = opuestos[direccion]
            if opp in otra.conexiones and otra.conexiones[opp] is self:
                otra.conexiones.pop(opp)

    def posiciones_vecinas(self) -> Dict[str, Tuple[int, int]]:
        x, y = self.pos
        return {
            "norte": (x, y - 1),
            "sur": (x, y + 1),
            "este": (x + 1, y),
            "oeste": (x - 1, y),
        }

    def to_dict(self) -> dict:
        conexiones_coords = {dir_: [hab.x, hab.y] for dir_, hab in self.conexiones.items()}
        contenido_dict = self.contenido.to_dict() if self.contenido is not None else None
        return {
            "id": self.id,
            "pos": [self.x, self.y],
            "inicial": self.inicial,
            "visitada": self.visitada,
            "conexiones": conexiones_coords,
            "contenido": contenido_dict
        }

    @staticmethod
    def from_dict(d: dict) -> "Habitacion":
        pos = tuple(d["pos"])
        hab = Habitacion(d["id"], pos, d.get("inicial", False))
        hab.visitada = d.get("visitada", False)
        return hab

    def __repr__(self):
        return f"Habitacion(id={self.id}, pos=({self.x},{self.y}), inicial={self.inicial})"
