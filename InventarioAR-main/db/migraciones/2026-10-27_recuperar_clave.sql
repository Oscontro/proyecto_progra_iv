-- ═══════════════════════════════════════════════════════════════════
-- Migración: recuperación de contraseña por correo
-- Fecha: 2026-10-27
--
-- "¿Olvidaste tu contraseña?" (web/olvide-clave.php) envía un enlace con un
-- token de un solo uso; acá se guarda solo su hash SHA-256, nunca el token.
-- El enlace vence a la hora (web/restablecer-clave.php).
--
-- Aplicar:  mysql -uroot inventario_radios < 2026-10-27_recuperar_clave.sql
-- En el hosting: pegar el contenido en phpMyAdmin > SQL.
-- ═══════════════════════════════════════════════════════════════════

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `recuperaciones_clave` (
  `id_recuperacion` INT(11)     NOT NULL AUTO_INCREMENT,
  `id_usuario`      INT(11)     NOT NULL,
  `token_hash`      CHAR(64)    NOT NULL COMMENT 'SHA-256 del token enviado por correo',
  `vence`           DATETIME    NOT NULL,
  `usado`           TINYINT(1)  NOT NULL DEFAULT 0,
  `ip`              VARCHAR(45) NULL,
  `fecha`           DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_recuperacion`),
  UNIQUE KEY `token_hash` (`token_hash`),
  KEY `idx_usuario` (`id_usuario`),
  CONSTRAINT `recuperaciones_clave_ibfk_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Enlaces de recuperación de contraseña';
