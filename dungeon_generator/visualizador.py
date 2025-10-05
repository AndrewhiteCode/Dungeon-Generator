from __future__ import annotations
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from typing import Tuple
from .mapa import Mapa
from .explorador import Explorador

console = Console()

class Visualizador:
    def __init__(self, mapa: Mapa):
        self.mapa = mapa

    def mostrar_mapa_completo(self) -> None:
        """
        Muestra una tabla simple con IDs de habitaciones y tipo (si tiene contenido).
        """
        t = Table(title="Mapa completo")
        t.add_column("Y\\X", justify="left")
        for x in range(self.mapa.ancho):
            t.add_column(str(x), justify="center")

        for y in range(self.mapa.alto):
            row = [str(y)]
            for x in range(self.mapa.ancho):
                coord = (x, y)
                if coord in self.mapa.habitaciones:
                    hab = self.mapa.habitaciones[coord]
                    mark = "S" if hab.inicial else f"{hab.id}"
                    tipo = getattr(hab.contenido, "tipo", "")
                    if tipo:
                        cell = f"{mark}({tipo[0]})"
                    else:
                        cell = f"{mark}"
                else:
                    cell = "·"
                row.append(cell)
            t.add_row(*row)
        console.print(t)

    def mostrar_habitacion_actual(self, explorador: Explorador) -> None:
        coord = tuple(explorador.posicion_actual)
        hab = self.mapa.habitaciones.get(coord)
        if not hab:
            console.print(Panel("No hay habitación en la posición actual"))
            return
        tipo = getattr(hab.contenido, "tipo", "vacía")
        descripcion = getattr(hab.contenido, "descripcion", "Sin contenido")
        texto = Text()
        texto.append(f"Hab ID: {hab.id}  Pos: {coord}\n", style="bold")
        texto.append(f"Visitada: {hab.visitada}\n")
        texto.append(f"Contenido: {tipo}\n")
        texto.append(f"{descripcion}\n")
        console.print(Panel(texto, title="Habitación actual"))

    def mostrar_minimapa(self, explorador: Explorador) -> None:
        """
        Muestra solamente habitaciones visitadas y la posición del explorador.
        """
        grid = [[" " for _ in range(self.mapa.ancho)] for _ in range(self.mapa.alto)]
        for (x, y), hab in self.mapa.habitaciones.items():
            if hab.visitada:
                grid[y][x] = "o"
        # marcar explorador
        ex, ey = explorador.posicion_actual
        grid[ey][ex] = "X"
        lines = ["".join(row) for row in grid]
        panel_text = "\n".join(lines)
        console.print(Panel(panel_text, title="Minimapa (visitadas=o, tu=X)"))

    def mostrar_estado_explorador(self, explorador: Explorador) -> None:
        t = Table.grid()
        t.add_column()
        t.add_column()
        t.add_row("Vida:", str(explorador.vida))
        t.add_row("Posición:", str(explorador.posicion_actual))
        inv = ", ".join([getattr(o, "nombre", str(o)) for o in explorador.inventario]) or " vacío"
        t.add_row("Inventario:", inv)
        console.print(Panel(t, title="Estado del Explorador"))
