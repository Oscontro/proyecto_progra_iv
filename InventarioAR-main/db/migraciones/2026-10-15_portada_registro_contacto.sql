-- ═══════════════════════════════════════════════════════════════════
-- Migración: portada pública, registro de usuarios y contacto
-- Fecha: 2026-10-15
--
-- Requisitos del Proyecto Integrador (2º parcial):
--   - Tabla de contactos: las consultas del formulario de contacto se
--     guardan acá (además de enviarse con mail() a una dirección simulada).
--   - Registro de usuarios "generales" desde la portada: la cuenta queda
--     pendiente hasta que un administrador la aprueba
--     (usuarios.pendiente_aprobacion = 1, activo = 0).
--   - La sesión pasa a ser la nativa de PHP ($_SESSION): la tabla
--     `sessions` (tokens propios) y su trigger trg_ultima_sesion dejan de
--     usarse. La última conexión la actualiza el login directamente.
--
-- Aplicar:  mysql -uroot inventario_radios < 2026-10-15_portada_registro_contacto.sql
-- ═══════════════════════════════════════════════════════════════════

-- Los comentarios llevan acentos: sin esto, el cliente mysql de Windows los
-- interpreta con la página de códigos de la consola y quedan mal guardados.
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `contactos` (
  `id_contacto`  INT(11)      NOT NULL AUTO_INCREMENT,
  `nombre`       VARCHAR(100) NOT NULL,
  `email`        VARCHAR(150) NOT NULL,
  `asunto`       VARCHAR(150) NOT NULL,
  `mensaje`      TEXT         NOT NULL,
  `id_usuario`   INT(11)      NULL     COMMENT 'Usuario logueado que la envió (NULL = visitante)',
  `mail_enviado` TINYINT(1)   NOT NULL DEFAULT 0 COMMENT 'Resultado de mail() al recibirla',
  `leido`        TINYINT(1)   NOT NULL DEFAULT 0,
  `ip`           VARCHAR(45)  NULL,
  `fecha`        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_contacto`),
  KEY `idx_fecha` (`fecha`),
  KEY `idx_leido` (`leido`),
  KEY `idx_usuario` (`id_usuario`),
  CONSTRAINT `contactos_ibfk_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Consultas del formulario de contacto';

ALTER TABLE `usuarios`
  ADD COLUMN `pendiente_aprobacion` TINYINT(1) NOT NULL DEFAULT 0
      COMMENT 'Registrado desde la portada, a la espera de que un administrador lo apruebe'
      AFTER `activo`;

-- Sesión nativa de PHP: los tokens propios ya no se usan.
DROP TRIGGER IF EXISTS `trg_ultima_sesion`;
DROP TABLE IF EXISTS `sessions`;
