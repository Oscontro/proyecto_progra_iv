# Código retirado

Pestañas del cliente de escritorio que quedaron fuera de la migración a HTML5/JS
(decisión del 14/10/2026), junto con los endpoints PHP que solo ellas usaban:

- `tab_vehiculos.py`: alta_interno, asociar_radio, baja_interno, desasociar_radio,
  internos, modelo_internos, modificar_interno, radios_vehiculos
- `tab_etiquetas.py` y `etiqueta_equipo.py`: equipo_etiqueta, historial_ultimos_tres
- `tab_ultimos_movimientos.py`: movimientos, usuario
- `tab_configuracion.py`: no usaba endpoints (era una maqueta sin funcionalidad real)

Se conservan por referencia. El `.htaccess` impide que Apache los sirva.
Los endpoints de vehículos que usa la Papelera (historialVehiculos, restaurar_vehiculo,
tipo_vehiculo) siguen en `php/`.
