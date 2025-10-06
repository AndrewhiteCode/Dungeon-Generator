import os
import sys
import random
from pathlib import Path
from typing import List

from dungeon_generator.mapa import Mapa
from dungeon_generator.explorador import Explorador
from dungeon_generator.contenido import Tesoro, Monstruo, Evento
try:
    from dungeon_generator.visualizador import Visualizador
    HAS_VIS = True
except Exception:
    Visualizador = None
    HAS_VIS = False
try:
    from dungeon_generator.serializacion import guardar_partida, cargar_partida
    HAS_SERIAL = True
except Exception:
    guardar_partida = None
    cargar_partida = None
    HAS_SERIAL = False

CLEAR_CMD = "cls" if os.name == "nt" else "clear"

class Controller:
    def __init__(self, ancho=8, alto=6, habitaciones=18, seed=42):
        self.ancho = ancho
        self.alto = alto
        self.habitaciones = habitaciones
        self.seed = seed
        self._init_game()
        self.logs: List[str] = []
        self.save_default = "prueba.json"

    def _init_game(self):
        self.mapa = Mapa(self.ancho, self.alto, seed=self.seed)
        self.mapa.generar_estructura(self.habitaciones)
        self.mapa.colocar_contenido(seed=self.seed)
        self.explorador = Explorador(self.mapa)
        self.visualizador = Visualizador(self.mapa) if HAS_VIS else None

    def reset(self):
        self._init_game()
        self.logs = []
        self.log("Juego reiniciado.")

    def log(self, msg: str):
        self.logs.append(msg)
        if len(self.logs) > 100:
            self.logs.pop(0)

    def render(self):
        os.system(CLEAR_CMD)
        print("=== Dungeon Project — Consola interactiva ===")
        if self.visualizador:
            self.visualizador.mostrar_mapa_completo()
        else:
            print(self.mapa.imprimir_ascii())
        if self.visualizador:
            self.visualizador.mostrar_minimapa(self.explorador)
            self.visualizador.mostrar_estado_explorador(self.explorador)
        else:
            print("Minimapa (visitadas=o, tu=X):")
            grid = [[" " for _ in range(self.mapa.ancho)] for _ in range(self.mapa.alto)]
            for (x, y), hab in self.mapa.habitaciones.items():
                if hab.visitada:
                    grid[y][x] = "o"
            ex, ey = self.explorador.posicion_actual
            grid[ey][ex] = "X"
            for row in grid:
                print("".join(row))
            print("Estado del explorador:")
            print(f"  Pos: {self.explorador.posicion_actual}  Vida: {self.explorador.vida}  Ataque: {self.explorador.calcular_ataque()}")
            inv = ", ".join([f"[{i}] {getattr(o,'nombre',str(o))}" for i,o in enumerate(self.explorador.inventario)]) or "vacío"
            print("  Inventario:", inv)
        print("\n--- Últimos eventos ---")
        for l in self.logs[-12:]:
            print(l)
        print("\nEscribe 'ayuda' para ver comandos.")

    def cmd_mover(self):
        hab = self.mapa.habitaciones.get(tuple(self.explorador.posicion_actual))
        if not hab:
            self.log("Posición inválida.")
            return
        opciones = list(hab.conexiones.keys())
        if not opciones:
            self.log("No hay direcciones disponibles desde aquí.")
            return
        dir_ = random.choice(opciones)
        ok = self.explorador.mover(dir_)
        if not ok:
            self.log(f"No puedes mover {dir_} desde {self.explorador.posicion_actual}.")
            return
        self.log(f"Movido {dir_} -> {self.explorador.posicion_actual}.")
        hab2 = self.mapa.habitaciones.get(tuple(self.explorador.posicion_actual))
        if hab2 and hab2.contenido:
            res = self.explorador.explorar_habitacion()
            self.log(res)

    def cmd_ir(self, x:int, y:int):
        dest = (int(x), int(y))
        path = self.explorador.encontrar_camino(dest)
        if not path and tuple(self.explorador.posicion_actual) != tuple(dest):
            self.log("No hay camino hacia destino.")
            return
        for direccion, coord in path:
            if not self.explorador.esta_vivo:
                self.log("Muerto, no puedes continuar.")
                break
            moved = self.explorador.mover(direccion)
            if not moved:
                self.log(f"Movimiento falló en {direccion}.")
                break
            self.log(f"Moviendo {direccion} -> {self.explorador.posicion_actual}")
            hab = self.mapa.habitaciones.get(tuple(self.explorador.posicion_actual))
            if hab and hab.contenido:
                res = self.explorador.explorar_habitacion()
                self.log(res)

    def cmd_guardar(self, ruta=None):
        ruta = ruta or self.save_default
        if not HAS_SERIAL:
            self.log("Serialización no disponible.")
            return
        try:
            guardar_partida(self.mapa, self.explorador, ruta)
            abs = Path(ruta).resolve()
            self.log(f"Partida guardada en: {abs}")
        except Exception as e:
            self.log(f"Error guardando: {e}")

    def _choose_file_interactive(self, dirpath="."):
        p = Path(dirpath)
        files = sorted([f for f in p.glob("*.json") if f.is_file()])
        if not files:
            print("No hay archivos .json en", Path(dirpath).resolve())
            return None
        print("\nArchivos guardados disponibles:")
        for i, f in enumerate(files):
            size = f.stat().st_size
            mtime = f.stat().st_mtime
            from datetime import datetime
            mt = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            print(f"  [{i}] {f.name}    ({size} bytes, mod: {mt})")
        while True:
            try:
                choice = input("Selecciona índice (o 'c' para cancelar): ").strip()
            except (KeyboardInterrupt, EOFError):
                return None
            if choice.lower() in ("c", "q", ""):
                print("Selección cancelada.")
                return None
            try:
                idx = int(choice)
                if 0 <= idx < len(files):
                    return str(files[idx])
                else:
                    print("Índice fuera de rango.")
            except ValueError:
                print("Entrada inválida. Escribe el número del índice o 'c' para cancelar.")

    def cmd_cargar(self, ruta=None):
        if not HAS_SERIAL:
            self.log("Serialización no disponible.")
            return
        path_to_load = ruta
        if ruta is None or ruta == "seleccionar":
            chosen = self._choose_file_interactive(".")
            if not chosen:
                self.log("Carga cancelada o no hay archivos.")
                return
            path_to_load = chosen
        try:
            mapa2, exp2 = cargar_partida(path_to_load)
            self.mapa = mapa2
            self.explorador = exp2
            if HAS_VIS:
                self.visualizador = Visualizador(self.mapa)
            self.logs = []
            self.log(f"Partida cargada desde {Path(path_to_load).resolve()}")
        except Exception as e:
            self.log(f"Error cargando: {e}")

    def cmd_help(self):
        lines = [
            "Comandos:",
            "  Mover Aleatoriamente      - mover un paso en dirección aleatoria disponible",
            "  Ir a coord (x,y)          - caminar hasta x,y paso a paso",
            "  Guardar [ruta]            - guardar partida (por defecto prueba.json)",
            "  Cargar [ruta]             - cargar partida (sin args lista archivos y permite seleccionar)",
            "  Reinicio / reset          - reiniciar la partida (nuevo mapa con mismos parámetros)",
            "  Estado                    - mostrar estado (redibuja)",
            "  Ayuda                     - mostrar esta ayuda",
            "  Salir                     - salir (pregunta y/n)"
        ]
        for l in lines:
            self.log(l)

def repl_loop(controller: Controller):
    controller.render()
    while True:
        try:
            cmd = input("\nComando> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nSaliendo.")
            break
        if not cmd:
            controller.render()
            continue
        parts = cmd.split()
        op = parts[0].lower()
        args = parts[1:]
        if op in ("salir", "q", "exit"):
            try:
                ans = input("¿Seguro que quieres salir? (y/n): ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                ans = "n"
            if ans and ans[0] == "y":
                break
            else:
                controller.log("Salida cancelada.")
                controller.render()
                continue
        if op in ("mover", "m"):
            controller.cmd_mover()
        elif op == "ir" and args:
            xy = args[0].split(",")
            if len(xy) == 2:
                controller.cmd_ir(int(xy[0]), int(xy[1]))
            else:
                controller.log("Formato ir x,y")
        elif op == "guardar":
            controller.cmd_guardar(args[0] if args else None)
        elif op == "cargar":
            controller.cmd_cargar(args[0] if args else None)
        elif op in ("reinicio"):
            controller.reset()
        elif op in ("ayuda", "help"):
            controller.cmd_help()
        elif op == "estado":
            controller.log("Refrescando estado.")
        else:
            controller.log("Comando desconocido. Escribe 'ayuda'.")
        controller.render()

if __name__ == "__main__":
    ctrl = Controller()
    ctrl.log("Bienvenido. Escribe 'ayuda' para comandos.")
    repl_loop(ctrl)
