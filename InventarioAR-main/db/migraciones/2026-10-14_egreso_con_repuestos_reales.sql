-- ═══════════════════════════════════════════════════════════════════
-- Migración: el egreso de taller descuenta repuestos REALES del catálogo
-- Fecha: 2026-10-14
--
-- Antes: taller_egresos tenía 12 columnas fijas (repuesto_potenciometro,
-- repuesto_display, ...) y un trigger descontaba stock buscando repuestos
-- con esos nombres genéricos ('POTENCIOMETRO', 'DISPLAY'...). En el catálogo
-- real los repuestos tienen otros nombres, así que nunca descontaba nada; y
-- además restaba de repuestos.stock_actual en vez del stock por taller.
--
-- Ahora: egreso_taller.php recibe los repuestos del catálogo vinculados al
-- modelo del equipo, con cantidades, y en la misma transacción:
--   - descuenta repuesto_stock del taller del ingreso y suma repuestos.en_uso
--     (lo mismo que "Usar en equipo" en la pestaña Repuestos),
--   - registra cada uso en taller_egreso_repuestos,
--   - deja el detalle en historial_equipos.
-- Las columnas repuesto_* se conservan (datos históricos y "Otros").
--
-- Aplicar:  mysql -uroot inventario_radios < 2026-10-14_egreso_con_repuestos_reales.sql
-- ═══════════════════════════════════════════════════════════════════

-- Los comentarios llevan acentos: sin esto, el cliente mysql de Windows los
-- interpreta con la página de códigos de la consola y quedan mal guardados.
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `taller_egreso_repuestos` (
  `id`              INT(11)      NOT NULL AUTO_INCREMENT,
  `id_egreso`       INT(11)      NOT NULL,
  `id_repuesto`     INT(11)      NULL     COMMENT 'NULL si el repuesto se dio de baja después',
  `nombre_repuesto` VARCHAR(100) NOT NULL COMMENT 'Copia del nombre al momento del egreso',
  `id_taller`       INT(11)      NOT NULL COMMENT 'Taller del que salió el stock',
  `cantidad`        INT(11)      NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_egreso` (`id_egreso`),
  KEY `idx_repuesto` (`id_repuesto`),
  CONSTRAINT `fk_ter_egreso`   FOREIGN KEY (`id_egreso`)   REFERENCES `taller_egresos` (`id_egreso`) ON DELETE CASCADE,
  CONSTRAINT `fk_ter_repuesto` FOREIGN KEY (`id_repuesto`) REFERENCES `repuestos` (`id_repuesto`) ON DELETE SET NULL,
  CONSTRAINT `fk_ter_taller`   FOREIGN KEY (`id_taller`)   REFERENCES `talleres` (`id_taller`),
  CONSTRAINT `chk_ter_cantidad` CHECK (`cantidad` > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Repuestos del catálogo usados en cada egreso de taller';

-- Descontaba stock por nombres genéricos que no existen en el catálogo.
DROP TRIGGER IF EXISTS `trg_after_insert_restar_stock_repuestos`;

-- Armaba el historial con las 12 columnas fijas; ahora lo escribe
-- egreso_taller.php con los repuestos reales y sus cantidades.
DROP TRIGGER IF EXISTS `trg_historial_repuestos`;
