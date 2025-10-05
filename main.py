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
    """
    Return a human-friendly description for the content of `hab` (Habitacion).
    """
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
    # generar mapa y colocar contenido
    mapa = Mapa(8, 6, seed=42)
    mapa.generar_estructura(12)
    resumen = mapa.colocar_contenido(seed=42)
    print("Resumen colocar_contenido:", resumen)

    # visualizador 
    if HAS_VISUALIZADOR:
        viz = Visualizador(mapa)
        viz.mostrar_mapa_completo()
    else:
        print("Visualizador no disponible -> mostrando ASCII:")
        print(mapa.imprimir_ascii())

    mostrar_estadisticas_si_existe(mapa)

    # buscar coordenadas de tesoro y monstruo
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

    # crear explorador
    exp = Explorador(mapa)
    print("Explorador inicial:", exp)
    if HAS_VISUALIZADOR:
        viz.mostrar_estado_explorador(exp)
        viz.mostrar_minimapa(exp)

    # probar tesoro
    if coord_tesoro:
        print("\n--- Probando tesoro ---")
        exp.posicion_actual = coord_tesoro
        print("Posición del explorador ->", exp.posicion_actual)
        if HAS_VISUALIZADOR:
            viz.mostrar_habitacion_actual(exp)
        salida = exp.explorar_habitacion()
        print(salida)
        print("Inventario ahora:", exp.inventario)
        print("Contenido en esa habitación:", contenido_str(mapa.habitaciones[coord_tesoro]))
        if HAS_VISUALIZADOR:
            viz.mostrar_estado_explorador(exp)
            viz.mostrar_minimapa(exp)

    # probar combate
    if coord_mon:
        print("\n--- Probando combate ---")
        exp.posicion_actual = coord_mon
        print("Posición del explorador ->", exp.posicion_actual)
        if HAS_VISUALIZADOR:
            viz.mostrar_habitacion_actual(exp)
        salida = exp.explorar_habitacion()
        print(salida)
        print("Vida del explorador:", exp.vida)
        print("Contenido en esa habitación:", contenido_str(mapa.habitaciones[coord_mon]))
        if HAS_VISUALIZADOR:
            viz.mostrar_estado_explorador(exp)
            viz.mostrar_minimapa(exp)

    # guardar partida 
    save_file = "prueba.json"
    if HAS_SERIALIZACION:
        try:
            guardar_partida(mapa, exp, save_file)
            print(f"\nPartida guardada en '{save_file}'")
        except Exception as e:
            print("Error guardando partida:", e)
    else:
        print("\nMódulo de serialización no disponible. Saltando guardado.")

    # cargar partida y mostrar lo cargado 
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

    # limpieza
    if HAS_SERIALIZACION:
        try:
            p = Path(save_file)
            if p.exists():
                p.unlink()
        except Exception:
            pass

    print("\nDemo finalizada.")


if __name__ == "__main__":
    demo()