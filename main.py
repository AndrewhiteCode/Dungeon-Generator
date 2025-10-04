from dungeon_generator.mapa import Mapa
from dungeon_generator.explorador import Explorador
from dungeon_generator.contenido import Tesoro, Monstruo

def demo():
    mapa = Mapa(8, 6, seed=42)
    mapa.generar_estructura(12)
    resumen = mapa.colocar_contenido(seed=42)
    print("Resumen colocar_contenido:", resumen)

    coord_tesoro = None
    coord_mon = None
    for coord, hab in mapa.habitaciones.items():
        if hasattr(hab, "contenido") and hab.contenido is not None:
            if hab.contenido.tipo == "tesoro" and coord_tesoro is None:
                coord_tesoro = coord
            if hab.contenido.tipo == "monstruo" and coord_mon is None:
                coord_mon = coord
        if coord_tesoro and coord_mon:
            break

    exp = Explorador(mapa)
    print("Explorador inicial:", exp)

    if coord_tesoro:
        print("\n--- Probando tesoro ---")
        exp.posicion_actual = coord_tesoro
        print("Posición del explorador ->", exp.posicion_actual)
        salida = exp.explorar_habitacion()
        print(salida)
        print("Inventario ahora:", exp.inventario)
        print("Contenido en esa habitación (debe ser None):", mapa.habitaciones[coord_tesoro].contenido)

    if coord_mon:
        print("\n--- Probando combate ---")
        exp.posicion_actual = coord_mon
        print("Posición del explorador ->", exp.posicion_actual)
        salida = exp.explorar_habitacion()
        print(salida)
        print("Vida del explorador:", exp.vida)
        print("Contenido en esa habitación (None si derrotado):", mapa.habitaciones[coord_mon].contenido)

if __name__ == "__main__":
    demo()
