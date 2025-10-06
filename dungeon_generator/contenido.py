from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
import random
from .objetos import Objeto


class ContenidoHabitacion(ABC):
    """
    Interfaz/abstracta para el contenido de una habitación.
    Las subclases deben implementar to_dict() y from_dict() estático.
    """
    @property
    @abstractmethod
    def descripcion(self) -> str:
        ...

    @property
    @abstractmethod
    def tipo(self) -> str:
        ...

    @abstractmethod
    def interactuar(self, explorador) -> str:
        ...

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        ...

    @staticmethod
    @abstractmethod
    def from_dict(d: Dict[str, Any]) -> "ContenidoHabitacion":
        ...

class Tesoro(ContenidoHabitacion):
    def __init__(self, recompensa: Objeto):
        self.recompensa = recompensa

    @property
    def descripcion(self) -> str:
        return f"Un tesoro: {self.recompensa.nombre} (valor {self.recompensa.valor})"

    @property
    def tipo(self) -> str:
        return "tesoro"

    def interactuar(self, explorador) -> str:
        explorador.inventario.append(self.recompensa)
        cat = getattr(self.recompensa, "categoria", "normal")
        if cat == "equipable":
            return f"Has encontrado un objeto equipable: {self.recompensa.nombre}. Está en tu inventario; usa 'equipar' para ponértelo."
        elif cat == "consumible":
            return f"Has encontrado un consumible: {self.recompensa.nombre}. Está en tu inventario; usa 'usar' para activarlo."
        else:
            return f"Has recogido el tesoro: {self.recompensa.nombre} (valor {self.recompensa.valor})"

    def to_dict(self) -> Dict[str, Any]:
        return {"tipo": self.tipo, "recompensa": self.recompensa.to_dict()}

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Tesoro":
        obj = Objeto.from_dict(d["recompensa"])
        return Tesoro(obj)


class Monstruo(ContenidoHabitacion):
    def __init__(self, nombre: str, vida: int, ataque: int):
        self.nombre = nombre
        self.vida = int(vida)
        self.ataque = int(ataque)

    @property
    def descripcion(self) -> str:
        return f"Monstruo {self.nombre} (vida {self.vida}, atq {self.ataque})"

    @property
    def tipo(self) -> str:
        return "monstruo"

    def interactuar(self, explorador) -> str:
        log = []
        vida_enemigo = self.vida
        vida_jugador = explorador.vida

        turno = random.choice([0, 1])
        log.append(f"Comienza el combate contra {self.nombre} (PV enemigo: {vida_enemigo}).")
        while vida_enemigo > 0 and vida_jugador > 0:
            if turno == 0:
                attack_val = explorador.calcular_ataque()
                min_dmg = max(1, attack_val - 1)
                max_dmg = attack_val + 1
                danio = random.randint(min_dmg, max_dmg)
                vida_enemigo -= danio
                log.append(f"Atacas y haces {danio} de daño (enemigo {max(0, vida_enemigo)} PV).")
                turno = 1
            else:
                danio = random.randint(1, self.ataque)
                vida_jugador -= danio
                explorador.recibir_dano(danio)
                log.append(f"{self.nombre} te golpea por {danio} (tus PV {max(0, vida_jugador)}).")
                turno = 0

        self.vida = max(0, vida_enemigo)

        if self.vida <= 0 and explorador.vida > 0:
            log.append(f"Has derrotado a {self.nombre}.")
            return "\n".join(log)
        elif explorador.vida <= 0:
            log.append("Has sido derrotado.")
            return "\n".join(log)
        else:
            return "\n".join(log)


    def to_dict(self) -> Dict[str, Any]:
        return {"tipo": self.tipo, "nombre": self.nombre, "vida": self.vida, "ataque": self.ataque}

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Monstruo":
        return Monstruo(d["nombre"], int(d["vida"]), int(d["ataque"]))


class Jefe(Monstruo):
    def __init__(self, nombre: str, vida: int, ataque: int, recompensa_especial: Objeto):
        super().__init__(nombre, vida, ataque)
        self.recompensa_especial = recompensa_especial

    @property
    def tipo(self) -> str:
        return "jefe"

    def interactuar(self, explorador) -> str:
        log = []
        vida_jugador = explorador.vida
        vida_enemigo = self.vida

        turno = 0 if random.random() < 0.35 else 1
        log.append(f"Enfrentas al jefe {self.nombre} (PV: {vida_enemigo}).")
        while vida_enemigo > 0 and vida_jugador > 0:
            if turno == 0:
                danio = random.randint(1, 2 + int(self.ataque/2))
                vida_enemigo -= danio
                log.append(f"Atacas y haces {danio} de daño (enemigo {max(0, vida_enemigo)} PV).")
                turno = 1
            else:
                danio = random.randint(1, self.ataque)
                vida_jugador -= danio
                explorador.recibir_dano(danio)
                log.append(f"{self.nombre} te golpea por {danio} (tus PV {max(0, vida_jugador)}).")
                turno = 0

        self.vida = max(0, vida_enemigo)

        if self.vida <= 0 and explorador.vida > 0:
            explorador.inventario.append(self.recompensa_especial)
            log.append(f"Has derrotado al jefe {self.nombre} y obtienes {self.recompensa_especial.nombre}!")
            return "\n".join(log)
        elif explorador.vida <= 0:
            log.append("Has sido derrotado por el jefe.")
            return "\n".join(log)
        else:
            return "\n".join(log)


    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({"recompensa_especial": self.recompensa_especial.to_dict()})
        base["tipo"] = self.tipo
        return base

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Jefe":
        recompensa = Objeto.from_dict(d["recompensa_especial"])
        return Jefe(d["nombre"], int(d["vida"]), int(d["ataque"]), recompensa)

class Evento(ContenidoHabitacion):
    def __init__(self, nombre: str, descripcion: str, efecto: Dict[str, Any]):
        self.nombre = nombre
        self._descripcion = descripcion
        self.efecto = efecto  

    @property
    def descripcion(self) -> str:
        return f"{self.nombre}: {self._descripcion}"

    @property
    def tipo(self) -> str:
        return "evento"

    def interactuar(self, explorador) -> str:
        """
        Aplica el efecto del evento sobre el explorador.
        Efectos soportados (self.efecto es un dict):
        - tipo: "curar", "valor": int
        - tipo: "trampa", "valor": int
        - tipo: "teleport", "auto_explore": bool (opcional)
        - tipo: "buff_por_habitaciones", "ataque": int, "habitaciones": int
        - tipo: "modificar_ataque", "delta": int, "modo": "permanente"|"temporal_habitaciones", "habitaciones": int (si temporal)
        """
        tipo = self.efecto.get("tipo")
        if tipo == "curar":
            amount = int(self.efecto.get("valor", 5))
            explorador.vida += amount
            return f"Has enontrado un mago amigable recibes {amount} PV."
        elif tipo == "trampa":
            amount = int(self.efecto.get("valor", 2))
            explorador.recibir_dano(amount)
            return f"Has caido en una trampa, recibes {amount} de daño."
        elif tipo == "teleport":
            coords = list(explorador.mapa.habitaciones.keys())
            if not coords:
                return "Portal: no hay habitaciones disponibles."
            current = tuple(explorador.posicion_actual)
            choices = [c for c in coords if c != current]
            if not choices:
                return "Portal: no hay otra habitación a la que teletransportarte."
            dest = random.choice(choices)
            explorador.posicion_actual = tuple(dest)
            explorador.mapa.habitaciones[dest].visitada = True
            msg = f"Has caido en un portal que te a llevado a {dest}."
            if self.efecto.get("auto_explore", False):
                depth = getattr(explorador, "_event_chain_depth", 0)
                if depth >= 3:
                    msg += " (límite de encadenamiento alcanzado, no se explora automáticamente)."
                else:
                    explorador._event_chain_depth = depth + 1
                    try:
                        extra = explorador.explorar_habitacion()
                        if extra:
                            msg += "\n" + extra
                    finally:
                        explorador._event_chain_depth = depth
            return msg
        elif tipo == "buff_por_habitaciones":
            atk = int(self.efecto.get("ataque", 1))
            dur = int(self.efecto.get("habitaciones", 1))
            if not hasattr(explorador, "buffs"):
                explorador.buffs = []
            explorador.buffs.append({"ataque": atk, "restante_habitaciones": dur})
            return f"Bonificación activada: +{atk} ataque por {dur} habitaciones."
        elif tipo == "modificar_ataque":
            delta = int(self.efecto.get("delta", 0))
            modo = self.efecto.get("modo", "permanente")
            if modo == "permanente":
                if not hasattr(explorador, "ataque_base"):
                    explorador.ataque_base = getattr(explorador, "ataque_base", 1)
                explorador.ataque_base += delta
                sign = "+" if delta >= 0 else ""
                return f"Tu ataque se modifica {sign}{delta} permanentemente."
            elif modo == "temporal_habitaciones":
                dur = int(self.efecto.get("habitaciones", 1))
                if not hasattr(explorador, "buffs"):
                    explorador.buffs = []
                explorador.buffs.append({"ataque": delta, "restante_habitaciones": dur})
                sign = "+" if delta >= 0 else ""
                return f"Tu ataque {('aumenta' if delta>0 else 'disminuye')} {sign}{delta} por {dur} habitaciones."
            else:
                return "Efecto de modificar_ataque desconocido."
        else:
            if self.efecto.get("tipo") == "curar":
                amount = int(self.efecto.get("valor", 1))
                explorador.vida += amount
                return f"Fuente: recuperas {amount} PV."
            elif self.efecto.get("tipo") == "trampa":
                amount = int(self.efecto.get("valor", 1))
                explorador.recibir_dano(amount)
                return f"Trampa: recibes {amount} de daño."
            else:
                return "Evento misterioso..."


    def to_dict(self) -> Dict[str, Any]:
        return {"tipo": self.tipo, "nombre": self.nombre, "descripcion": self._descripcion, "efecto": self.efecto}

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Evento":
        return Evento(d["nombre"], d.get("descripcion", ""), d.get("efecto", {}))


def contenido_from_dict(d: Dict[str, Any]) -> ContenidoHabitacion:
    tipo = d.get("tipo")
    if tipo == "tesoro":
        return Tesoro.from_dict(d)
    elif tipo == "monstruo":
        return Monstruo.from_dict(d)
    elif tipo == "jefe":
        return Jefe.from_dict(d)
    elif tipo == "evento":
        return Evento.from_dict(d)
    else:
        raise ValueError(f"Tipo de contenido desconocido en from_dict: {tipo}")
    
def interactuar(self, explorador) -> str:
    explorador.inventario.append(self.recompensa)
    cat = getattr(self.recompensa, "categoria", "normal")
    if cat == "equipable":
        return f"Has encontrado un objeto equipable: {self.recompensa.nombre}. Está en tu inventario; usa 'equipar' para ponértelo."
    elif cat == "consumible":
        return f"Has encontrado un consumible: {self.recompensa.nombre}. Está en tu inventario; usa 'usar' para activarlo."
    else:
        return f"Has recogido el tesoro: {self.recompensa.nombre} (valor {self.recompensa.valor})"

