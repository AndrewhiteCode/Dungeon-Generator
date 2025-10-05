import json
from typing import Tuple
from .mapa import Mapa
from .explorador import Explorador
from .contenido import contenido_from_dict
from .objetos import Objeto
from pathlib import Path


def guardar_partida(mapa: Mapa, explorador: Explorador, archivo: str) -> None:
    """
    Guarda el estado completo (mapa + explorador) en JSON.
    Ignora entradas None en el inventario para evitar errores.
    """
    # Serializar inventario 
    inventario_serializado = []
    for obj in explorador.inventario:
        if obj is None:
            continue
        inventario_serializado.append(obj.to_dict())

    data = {
        "mapa": mapa.to_dict(),
        "explorador": {
            "vida": explorador.vida,
            "posicion": list(explorador.posicion_actual),
            "inventario": inventario_serializado
        }
    }
    p = Path(archivo)
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


def cargar_partida(archivo: str) -> Tuple[Mapa, Explorador]:
    """
    Carga la partida desde JSON y reconstruye Mapa y Explorador.
    Retorna (mapa, explorador).
    """
    p = Path(archivo)
    text = p.read_text(encoding="utf-8")
    data = json.loads(text)

    mapa_dict = data["mapa"]
    mapa = Mapa.from_dict(mapa_dict)

    for h in mapa_dict.get("habitaciones", []):
        cont = h.get("contenido")
        if cont is not None:
            coord = tuple(h["pos"])
            if coord in mapa.habitaciones:
                try:
                    mapa.habitaciones[coord].contenido = contenido_from_dict(cont)
                except Exception:
                    mapa.habitaciones[coord].contenido = None

    exp_data = data.get("explorador", {})
    posicion = tuple(exp_data.get("posicion", mapa.habitacion_inicial.pos))
    explorador = Explorador(mapa, posicion=posicion, vida=int(exp_data.get("vida", 5)))

    invent = []
    for o in exp_data.get("inventario", []):
        try:
            invent.append(Objeto.from_dict(o))
        except Exception:
            continue
    explorador.inventario = invent

    return mapa, explorador
