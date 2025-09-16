class Usuario:
    def __init__(
        self,
        id: int = None,  # Opcional para creaciones nuevas
        username: str = None,
        first_name: str = None,
        last_name: str = None,
        email: str = None,
        password: str = None,
        grupo_id: int = None
    ):
        self.id = id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = password  # Hash se aplicará en el repositorio
        self.grupo_id = grupo_id

    def validar(self):
        """Reglas de negocio básicas para contraseña"""
        if not self.email or "@" not in self.email:
            raise ValueError("Email inválido")
        if len(self.password) < 12:  
            raise ValueError("La contraseña debe tener al menos 12 caracteres")
        

    def __repr__(self):
        return f"Usuario(id={self.id}, username={self.username}, email={self.email})"