class Objeto:
    def __init__(self, nombre: str, valor: int = 0, descripcion: str = "", categoria: str = "normal", efecto: dict = None):
        self.nombre = nombre
        self.valor = int(valor)
        self.descripcion = descripcion
        self.categoria = categoria  
        self.efecto = efecto or {}
        

    def to_dict(self) -> dict:
        return {
            "nombre": self.nombre,
            "valor": self.valor,
            "descripcion": self.descripcion,
            "categoria": self.categoria,
            "efecto": self.efecto,
        }

    @staticmethod
    def from_dict(d: dict) -> "Objeto":
        return Objeto(
            d.get("nombre", "obj"),
            int(d.get("valor", 0)),
            d.get("descripcion", ""),
            d.get("categoria", "normal"),
            d.get("efecto", {}) or {},
        )

    def __repr__(self):
        return f"Objeto({self.nombre}, valor={self.valor})"
