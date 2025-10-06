from __future__ import annotations
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.box import SIMPLE_HEAVY, ROUNDED
from typing import Tuple
from .mapa import Mapa
from .explorador import Explorador

console = Console()

class Visualizador:
    TYPE_STYLE = {
        "monstruo": ("M", "bold white on red"),
        "jefe": ("J", "bold white on green"),
        "tesoro": ("T", "bold black on yellow"),
        "evento": ("E", "bold white on magenta"),
        None: (" ", "dim"),
        "vacía": ("0", "dim"), 
    }

    def __init__(
        self,
        mapa: Mapa,
        *,
        show_ids: bool = False,
        compact: bool = False,
        minimap_box_width: int = 62,
        minimap_box_height: int = 15,
        cell_w: int = 3,
        cell_h: int = 1,
    ):
        self.mapa = mapa
        self.show_ids = bool(show_ids)
        self.compact = bool(compact)
        self.minimap_box_width = max(30, int(minimap_box_width))
        self.minimap_box_height = max(5, int(minimap_box_height))
        self.cell_w = max(1, int(cell_w))
        self.cell_h = max(1, int(cell_h))

    
    def _sym_and_style_for_hab(self, hab):
        """
        Devuelve (símbolo, estilo) para la celda de 'hab' en el mapa completo.
        Ahora: si hay habitación y su contenido es None -> mostrar '0' (vacía).
        """
       
        if getattr(hab, "inicial", False):
            return ("S", "bold white on blue")

        contenido = getattr(hab, "contenido", None)
        if contenido is None:
            sym, style = self.TYPE_STYLE.get("vacía", ("0", "bold white on black"))
            return (sym, style)

        tipo_name = getattr(contenido, "tipo", None)
        sym, style = self.TYPE_STYLE.get(tipo_name, ("?", "bold"))
        return (sym, style)

    def _style_for_coord(self, coord):
        """
        Versión usada por el minimapa: devuelve (carácter, estilo) para una coordenada.
        Si hay habitación sin contenido -> '0'.
        """
        hab = self.mapa.habitaciones.get(coord)
        if not hab:
            return (" ", "dim")
        if getattr(hab, "inicial", False):
            return ("S", "bold white on blue")
        contenido = getattr(hab, "contenido", None)
        if contenido is None:
            return ("*", "dim")
        tipo = getattr(contenido, "tipo", None)
        if tipo == "monstruo":
            return ("M", "bold white on red")
        if tipo == "jefe":
            return ("J", "bold white on green")
        if tipo == "tesoro":
            return ("T", "black on yellow")
        if tipo == "evento":
            return ("E", "bold white on magenta")
        return ("o", "bold")

    def mostrar_mapa_completo(self) -> None:
        ancho = self.mapa.ancho
        alto = self.mapa.alto

        if self.compact:
            lines = []
            header = "   " + "".join(f"{x:2}" for x in range(ancho))
            lines.append(header)
            for y in range(alto):
                row = [f"{y:2} "]
                for x in range(ancho):
                    coord = (x, y)
                    if coord in self.mapa.habitaciones:
                        hab = self.mapa.habitaciones[coord]
                        sym, style = self._sym_and_style_for_hab(hab)
                        cell = Text(sym.center(2), style=style)
                        row.append(cell.plain)
                    else:
                        row.append("· ")
                lines.append("".join(row))
            panel_text = "\n".join(lines)
            console.print(Panel(panel_text, title="Mapa completo (compacto)", padding=(0,1)))
            return

        t = Table(title="Mapa completo", box=SIMPLE_HEAVY, show_lines=False, pad_edge=True)
        t.add_column("Y\\X", width=4, no_wrap=True, justify="center", style="bold")
        col_width = 6
        for x in range(ancho):
            t.add_column(str(x), width=col_width, justify="center", no_wrap=True)

        for y in range(alto):
            row = [str(y)]
            for x in range(ancho):
                coord = (x, y)
                if coord in self.mapa.habitaciones:
                    hab = self.mapa.habitaciones[coord]
                    sym, style = self._sym_and_style_for_hab(hab)
                    if self.show_ids:
                        txt = Text(sym.center(3), style=style)
                        txt.append("\n")
                        txt.append(Text(f"#{hab.id}", style="dim"))
                    else:
                        txt = Text(sym.center(3), style=style)
                    cell = Align.center(txt, vertical="middle")
                else:
                    cell = Text("·".center(3), style="dim")
                row.append(cell)
            t.add_row(*row)

        leyenda = Text()
        leyenda.append(" S ", style="bold white on blue"); leyenda.append("  Start  ")
        leyenda.append(" M ", style=self.TYPE_STYLE["monstruo"][1]); leyenda.append("  Monstruo  ")
        leyenda.append(" J ", style=self.TYPE_STYLE["jefe"][1]); leyenda.append("  Jefe  ")
        leyenda.append(" T ", style=self.TYPE_STYLE["tesoro"][1]); leyenda.append("  Tesoro  ")
        leyenda.append(" E ", style=self.TYPE_STYLE["evento"][1]); leyenda.append("  Evento  ")
        leyenda.append(" 0 ", style=self.TYPE_STYLE["vacía"][1]); leyenda.append("  Habitación vacía")
        console.print(t)
        console.print(Panel(leyenda, style="dim", padding=(0,1)))

    def mostrar_minimapa(self, explorador: Explorador, *, show_all: bool = False) -> None:
        ancho_map = self.mapa.ancho
        alto_map = self.mapa.alto
        inner_w = self.minimap_box_width - 2
        inner_h = self.minimap_box_height - 3
        max_cells_x = max(1, inner_w // (self.cell_w + 1))
        max_cells_y = max(1, inner_h // (self.cell_h))
        vw = min(ancho_map, max_cells_x)
        vh = min(alto_map, max_cells_y)
        ex, ey = tuple(explorador.posicion_actual)
        half_w = vw // 2
        half_h = vh // 2
        x0 = max(0, ex - half_w)
        y0 = max(0, ey - half_h)
        if x0 + vw > ancho_map:
            x0 = max(0, ancho_map - vw)
        if y0 + vh > alto_map:
            y0 = max(0, alto_map - vh)
        x1 = x0 + vw - 1
        y1 = y0 + vh - 1

        from rich.text import Text
        lines = []
        for row in range(y0, y1 + 1):
            line_cells = []
            for col in range(x0, x1 + 1):
                coord = (col, row)
                if coord in self.mapa.habitaciones:
                    hab = self.mapa.habitaciones[coord]
                    visited = getattr(hab, "visitada", False)
                    if not show_all and not visited and coord != (ex, ey):
                        ch = "·".center(self.cell_w)
                        style = "dim"
                    else:
                        ch, style = self._style_for_coord(coord)
                        ch = ch.center(self.cell_w)
                else:
                    ch = " ".center(self.cell_w)
                    style = "dim"
                if coord == (ex, ey):
                    ch = "X".center(self.cell_w)
                    style = "bold black on white"
                cell_text = Text(ch, style=style)
                line_cells.append(cell_text)
                if col != x1:
                    line_cells.append(Text(" ", style=""))
            line = Text.assemble(*line_cells)
            for _ in range(self.cell_h):
                lines.append(line)

        panel_body = Text("\n").join(lines)
        ley = Text()
        ley.append(" X ", style="bold black on white"); ley.append("  Explorador ")
        ley.append(" M ", style=self.TYPE_STYLE["monstruo"][1]); ley.append(" Monstruo ")
        ley.append(" J ", style=self.TYPE_STYLE["jefe"][1]); ley.append(" Jefe ")
        ley.append(" T ", style=self.TYPE_STYLE["tesoro"][1]); ley.append(" Tesoro ")
        ley.append(" * ", style=self.TYPE_STYLE["vacía"][1]); ley.append(" Habitación recorrida")
        panel = Panel(
            Align.center(panel_body),
            title=f"Minimapa (viewport {vw}×{vh}) — centro: {ex},{ey}",
            width=self.minimap_box_width,
            height=min(self.minimap_box_height, max(3, len(lines) + 3)),
            box=ROUNDED,
            padding=(0, 1),
        )
        console.print(panel)
        console.print(Panel(ley, style="dim", padding=(0,1)))

    def mostrar_habitacion_actual(self, explorador: Explorador) -> None:
        coord = tuple(explorador.posicion_actual)
        hab = self.mapa.habitaciones.get(coord)
        if not hab:
            console.print(Panel("No hay habitación en la posición actual", style="red"))
            return
        tipo = getattr(hab.contenido, "tipo", None)
        descripcion = getattr(hab.contenido, "descripcion", "Sin descripción")
        t = Table.grid(expand=False)
        t.add_column(justify="left"); t.add_column(justify="left")
        t.add_row("Hab ID:", f"{hab.id}")
        t.add_row("Pos:", f"{coord}")
        t.add_row("Visitada:", str(getattr(hab, "visitada", False)))
        if tipo:
            sym, style = self._style_for_coord(coord)
            nombre = getattr(hab.contenido, "nombre", "")
            contenido_txt = Text(f"{sym} {tipo}", style=style)
            if nombre:
                contenido_txt.append(f" — {nombre}", style="bold")
        else:
            contenido_txt = Text("vacía", style="dim")
        t.add_row("Contenido:", contenido_txt)
        t.add_row("Descripción:", descripcion)
        console.print(Panel(t, title="Habitación actual", padding=(0,1)))

    def mostrar_estado_explorador(self, explorador: Explorador) -> None:
            """
            Muestra un cuadro compacto con la información del explorador,
            con estilo visual similar al minimapa (pequeño y centrado).
            """
            t = Table.grid(padding=(0, 1))
            t.add_column(justify="right", style="bold cyan", no_wrap=True)
            t.add_column(justify="left", no_wrap=True)

            t.add_row("  Vida", Text(str(explorador.vida), style="bold red"))
            pos = f"({explorador.posicion_actual[0]}, {explorador.posicion_actual[1]})"
            t.add_row(" Posición", Text(pos, style="bold white"))

            inv = ", ".join([getattr(o, "nombre", str(o)) for o in explorador.inventario]) or "vacío"
            t.add_row(" Inventario", Text(inv, style="yellow"))

            panel = Panel(
                Align.center(t),
                title="[bold]Estado del Explorador[/bold]",
                box=ROUNDED,
                padding=(0, 1),
                width=38,  
                style="bold white",
            )
            console.print(panel)
