from dungeon_generator.mapa import Mapa
from dungeon_generator.explorador import Explorador
from dungeon_generator.contenido import Tesoro, Monstruo
from pathlib import Path

try:
    from dungeon_generator.visualizador import Visualizador
    HAS_VISUALIZADOR = True
except Exception:
    Visualizador = None
    HAS_VISUALIZADOR = False

try:
    from dungeon_generator.serializacion import guardar_partida, cargar_partida
    HAS_SERIALIZACION = True
except Exception:
    guardar_partida = None
    cargar_partida = None
    HAS_SERIALIZACION = False

def mostrar_estadisticas_si_existe(mapa):
    if hasattr(mapa, "obtener_estadisticas_mapa"):
        stats = mapa.obtener_estadisticas_mapa()
    else:
        total = len(mapa.habitaciones)
        tipos = {"tesoros": 0, "monstruos": 0, "jefes": 0, "eventos": 0, "vacios": 0}
        suma_conex = 0
        for h in mapa.habitaciones.values():
            suma_conex += len(h.conexiones)
            if h.contenido is None:
                tipos["vacios"] += 1
            else:
                t = getattr(h.contenido, "tipo", None)
                if t == "tesoro": tipos["tesoros"] += 1
                elif t == "monstruo": tipos["monstruos"] += 1
                elif t == "jefe": tipos["jefes"] += 1
                elif t == "evento": tipos["eventos"] += 1
                else: tipos["vacios"] += 1
        promedio = (suma_conex / total) if total else 0.0
        stats = {"total": total, **tipos, "promedio_conexiones": round(promedio, 2)}
    print("Estadísticas del mapa:", stats)
    return stats

def contenido_str(hab):
    c = hab.contenido
    if c is None:
        return "vacía"
    tipo = getattr(c, "tipo", "desconocido")
    desc = getattr(c, "descripcion", None)
    if desc:
        return f"{tipo} — {desc}"
    if tipo == "tesoro" and hasattr(c, "recompensa"):
        r = c.recompensa
        return f"tesoro — {getattr(r,'nombre',str(r))} (valor {getattr(r,'valor', '?')})"
    if tipo in ("monstruo", "jefe"):
        nombre = getattr(c, "nombre", "monstruo")
        vida = getattr(c, "vida", "?")
        ataque = getattr(c, "ataque", "?")
        return f"{tipo} — {nombre} (PV {vida}, Atq {ataque})"
    if tipo == "evento":
        nombre = getattr(c, "nombre", "evento")
        efecto = getattr(c, "efecto", {})
        return f"evento — {nombre} (efecto: {efecto})"
    return tipo

def demo():
    mapa = Mapa(8, 6, seed=777)
    mapa.generar_estructura(18)
    resumen = mapa.colocar_contenido(seed=777)
    print("Resumen colocar_contenido:", resumen)
    if HAS_VISUALIZADOR:
        viz = Visualizador(mapa)
        viz.mostrar_mapa_completo()
    else:
        print("Visualizador no disponible -> mostrando ASCII:")
        print(mapa.imprimir_ascii())
    mostrar_estadisticas_si_existe(mapa)
    coord_tesoro = None
    coord_mon = None
    for coord, hab in mapa.habitaciones.items():
        if hab.contenido is not None:
            tipo = getattr(hab.contenido, "tipo", None)
            if tipo == "tesoro" and coord_tesoro is None:
                coord_tesoro = coord
            if tipo == "monstruo" and coord_mon is None:
                coord_mon = coord
        if coord_tesoro and coord_mon:
            break
    exp = Explorador(mapa)
    print("Explorador inicial:", exp)
    if HAS_VISUALIZADOR:
        viz.mostrar_estado_explorador(exp)
        viz.mostrar_minimapa(exp)
    if coord_tesoro:
        print("\n--- Trayecto al tesoro (paso a paso) ---")
        path = exp.encontrar_camino(coord_tesoro)
        if not path and tuple(exp.posicion_actual) != tuple(coord_tesoro):
            print("No hay camino hacia el tesoro.")
        else:
            for direccion, destino in path:
                print(f"Moviendo {direccion} -> {destino}")
                moved = exp.mover(direccion)
                if not moved:
                    print("Movimiento fallido.")
                    break
                print("Posición actual:", exp.posicion_actual)
                resultado = exp.explorar_habitacion()
                if resultado:
                    print(resultado)
                if not exp.esta_vivo:
                    print("El explorador ha muerto en el camino.")
                    break
            print("Inventario ahora:", exp.inventario)
            print("Contenido en esa habitación:", contenido_str(mapa.habitaciones[coord_tesoro]))
            if HAS_VISUALIZADOR:
                viz.mostrar_estado_explorador(exp)
                viz.mostrar_minimapa(exp)
    if coord_mon:
        print("\n--- Trayecto al monstruo (paso a paso) ---")
        path = exp.encontrar_camino(coord_mon)
        if not path and tuple(exp.posicion_actual) != tuple(coord_mon):
            print("No hay camino hacia el monstruo.")
        else:
            for direccion, destino in path:
                print(f"Moviendo {direccion} -> {destino}")
                moved = exp.mover(direccion)
                if not moved:
                    print("Movimiento fallido.")
                    break
                print("Posición actual:", exp.posicion_actual)
                resultado = exp.explorar_habitacion()
                if resultado:
                    print(resultado)
                if not exp.esta_vivo:
                    print("El explorador ha muerto en el camino.")
                    break
            print("Vida del explorador:", exp.vida)
            print("Contenido en esa habitación:", contenido_str(mapa.habitaciones[coord_mon]))
            if HAS_VISUALIZADOR:
                viz.mostrar_estado_explorador(exp)
                viz.mostrar_minimapa(exp)
    save_file = "prueba.json"
    if HAS_SERIALIZACION:
        try:
            guardar_partida(mapa, exp, save_file)
            print("Partida guardada en:", Path(save_file).resolve())
            print("Directorio de trabajo actual:", Path.cwd())
        except Exception as e:
            print("Error guardando partida:", e)
    else:
        print("Módulo de serialización no disponible. Saltando guardado.")
    if HAS_SERIALIZACION:
        try:
            mapa2, exp2 = cargar_partida(save_file)
            print("\nPartida cargada. Estado cargado:")
            if HAS_VISUALIZADOR:
                viz2 = Visualizador(mapa2)
                viz2.mostrar_mapa_completo()
                viz2.mostrar_estado_explorador(exp2)
                viz2.mostrar_minimapa(exp2)
            else:
                print(mapa2.imprimir_ascii())
            mostrar_estadisticas_si_existe(mapa2)
        except Exception as e:
            print("Error cargando partida:", e)
    print("\nDemo finalizada. El archivo de guardado no fue eliminado automáticamente.")

if __name__ == "__main__":
    demo()
