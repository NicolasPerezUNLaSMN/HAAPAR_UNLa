class Tema :
    def __init__(
        self,
        id_tema: int = None,
        usuario_id: int = None,
        nombre: str = None,
        descripcion: str = None, 
        horizonte: str = None,
        territorio: str = None,
        #activo: bool = True
    ):
        self.id_tema = id_tema
        self.usuario_id = usuario_id
        self.nombre = nombre
        self.descripcion = descripcion
        self.horizonte = horizonte
        self.territorio = territorio
        #self.activo = activo


    def validar(self):
        if not self.nombre or not self.horizonte:
            raise ValueError("Ingrese un nombre para el tema")
        if not self.horizonte:
            raise ValueError("Ingrese año de interés")
        if not self.territorio:
            raise ValueError("Ingrese ubicación de interés")
        if len(self.descripcion) < 10:
            raise ValueError("Descripción demasiado breve")
        
    
    def __repr__(self):
        return f"Tema (id = {self.id_tema} // nombre = {self.nombre} // descripcion = {self.descripcion} // usuario = {self.usuario_id})"

    
