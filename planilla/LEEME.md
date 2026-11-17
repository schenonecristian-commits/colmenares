# Planilla Gestión apícola

- `Codigo.gs`: el código que va en Extensiones → Apps Script de la planilla. Antes de pegarlo, reemplazar `PONER-LA-CLAVE` por la clave real (la que se pone en la app).
- `armar.py`: arma las hojas Campo, Cuaderno y Sala. Uso:
  `CLAVE=... python3 armar.py pedido.json` y después enviar `pedido.json` por POST a la dirección de la planilla.
- La planilla usa formato regional de Argentina: las fórmulas se convierten solas (`;` entre argumentos, `\` entre columnas de `{}`).
