-- ═══════════════════════════════════════════════════════════════════
-- Migración: la base queda solo con tablas (sin vistas, triggers,
-- procedimientos ni eventos)
-- Fecha: 2026-10-15
--
-- El sitio se publica en InfinityFree, que en el plan gratuito solo da
-- los privilegios ALTER, CREATE, DELETE, DROP, INDEX, INSERT, SELECT,
-- UPDATE y LOCK TABLES: no se pueden crear vistas, triggers,
-- procedimientos, funciones ni eventos.
--
-- Lo que hacían pasó a PHP:
--   - Vistas vista_equipos_v4, vista_movimientos, vista_papelera_unificada
--     y vista_taller_v2 -> subconsultas en consultaInventario.php,
--     estadisticas_resumen.php, inventario_historial.php y vista_taller.php.
--     El resto de las vistas no las usaba nadie.
--   - Procedimientos sp_* -> consultas en los endpoints que los llamaban
--     (enviar_a_taller, enviar_papelera, restaurar_equipo,
--     restaurar_vehiculo, ingreso_taller, egreso_taller).
--   - Triggers de historial y de stock -> php/historial_comun.php
--     (registrarAltaEquipo, registrarCambiosEquipo, registrarHistorial*,
--     recalcularStockRepuesto).
--   - Evento cambio_estado_reparado: no corría (event_scheduler apagado) y
--     el hosting no tiene eventos; se elimina sin reemplazo.
--
-- Aplicar DESPUÉS de actualizar el código PHP:
--   mysql -uroot inventario_radios < 2026-10-15_sin_vistas_triggers_procedimientos.sql
-- ═══════════════════════════════════════════════════════════════════

SET NAMES utf8mb4;

DROP VIEW IF EXISTS
  `vista_equipos_papelera`, `vista_equipos_taller`, `vista_equipos_v3`, `vista_equipos_v4`,
  `vista_equipo_etiqueta`, `vista_estadisticas_generales`, `vista_ingreso_taller`,
  `vista_movimientos`, `vista_papelera_unificada`, `vista_taller`, `vista_taller_v2`,
  `vista_usuarios`, `vista_vehiculos_v5`;

DROP TRIGGER IF EXISTS `trg_equipos_after_insert`;
DROP TRIGGER IF EXISTS `trg_equipos_after_envio_taller`;
DROP TRIGGER IF EXISTS `trg_equipos_after_update`;
DROP TRIGGER IF EXISTS `trg_stock_taller_after_insert`;
DROP TRIGGER IF EXISTS `trg_stock_taller_after_update`;
DROP TRIGGER IF EXISTS `trg_stock_taller_after_delete`;
DROP TRIGGER IF EXISTS `trg_taller_egresos_after_insert`;
DROP TRIGGER IF EXISTS `trg_taller_ingresos_after_insert`;
DROP TRIGGER IF EXISTS `trg_historial_vehiculos_after_insert`;
DROP TRIGGER IF EXISTS `trg_vehiculos_after_update`;

DROP PROCEDURE IF EXISTS `sp_egreso_cambio_estado`;
DROP PROCEDURE IF EXISTS `sp_enviar_a_papelera`;
DROP PROCEDURE IF EXISTS `sp_enviar_equipo_taller_v3`;
DROP PROCEDURE IF EXISTS `sp_enviar_equipo_taller_v4`;
DROP PROCEDURE IF EXISTS `sp_enviar_vehiculo_papelera`;
DROP PROCEDURE IF EXISTS `sp_estadisticas_por_escala`;
DROP PROCEDURE IF EXISTS `sp_ingresar_taller`;
DROP PROCEDURE IF EXISTS `sp_obtener_historial_equipo`;
DROP PROCEDURE IF EXISTS `sp_restaurar_equipo_papelera`;
DROP PROCEDURE IF EXISTS `sp_restaurar_vehiculo_papelera`;

DROP EVENT IF EXISTS `cambio_estado_reparado`;
