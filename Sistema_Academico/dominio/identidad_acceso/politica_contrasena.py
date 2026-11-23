"""Política mínima para contraseñas de cuentas nuevas."""
LONGITUD_MINIMA = 8


def validar_contrasena(clave):
    if not isinstance(clave, str) or len(clave) < LONGITUD_MINIMA:
        raise ValueError('La contraseña debe tener al menos 8 caracteres.')
    if not any(c.isalpha() for c in clave) or not any(c.isdigit() for c in clave):
        raise ValueError('La contraseña debe combinar letras y números.')
