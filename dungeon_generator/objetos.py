from __future__ import annotations
from typing import Dict


class Objeto:
    def __init__(self, nombre: str, valor: int, descripcion: str = ""):
        self.nombre = nombre
        self.valor = int(valor)
        self.descripcion = descripcion

    def to_dict(self) -> Dict:
        return {
            "nombre": self.nombre,
            "valor": self.valor,
            "descripcion": self.descripcion
        }

    @staticmethod
    def from_dict(d: Dict) -> "Objeto":
        return Objeto(d["nombre"], int(d["valor"]), d.get("descripcion", ""))
    
    def __repr__(self):
        return f"Objeto({self.nombre}, valor={self.valor})"
