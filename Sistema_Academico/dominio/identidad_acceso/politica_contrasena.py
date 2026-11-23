"""Política mínima de contraseñas para cuentas nuevas."""

LONGITUD_MINIMA = 8


def cumple_longitud(clave):
    return len(clave or '') >= LONGITUD_MINIMA


def validar_contrasena(clave):
    """Exige al menos una letra y un número además de la longitud mínima."""
    if not any(c.isalpha() for c in clave) or not any(c.isdigit() for c in clave):
        raise ValueError('La contraseña debe combinar letras y números.')
