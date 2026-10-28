
/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
DROP TABLE IF EXISTS `backups_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `backups_log` (
  `id_backup` int(11) NOT NULL AUTO_INCREMENT,
  `tipo_backup` enum('SQL','EXCEL','AUTOMATICO','MANUAL') NOT NULL,
  `nombre_archivo` varchar(255) NOT NULL,
  `ruta_archivo` varchar(500) NOT NULL,
  `tamanio_bytes` bigint(20) DEFAULT NULL COMMENT 'Tamaño del archivo en bytes',
  `fecha_backup` datetime DEFAULT current_timestamp(),
  `usuario_backup` int(11) DEFAULT NULL COMMENT 'Usuario que realizó el backup (NULL si es automático)',
  `estado` enum('EXITOSO','FALLIDO') DEFAULT 'EXITOSO',
  `mensaje_error` text DEFAULT NULL,
  PRIMARY KEY (`id_backup`),
  KEY `idx_fecha` (`fecha_backup`),
  KEY `idx_tipo` (`tipo_backup`),
  KEY `usuario_backup` (`usuario_backup`),
  CONSTRAINT `backups_log_ibfk_1` FOREIGN KEY (`usuario_backup`) REFERENCES `usuarios` (`id_usuario`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Log de backups realizados';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `canales_detalle`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `canales_detalle` (
  `id_canal` int(11) NOT NULL AUTO_INCREMENT,
  `id_programacion` int(11) NOT NULL COMMENT 'Programación a la que pertenece',
  `numero_canal` int(11) NOT NULL COMMENT 'Número de canal (1, 2, 3... )',
  `frecuencia_tx` decimal(10,3) DEFAULT NULL COMMENT 'Frecuencia TX en MHz (ej: 154.2500)',
  `frecuencia_rx` decimal(10,3) DEFAULT NULL COMMENT 'Frecuencia RX en MHz',
  `codificacion` enum('SQL','DPL','TPL') DEFAULT NULL COMMENT 'Tipo de codificación',
  `codigo_squelch` varchar(50) DEFAULT NULL COMMENT 'Código DPL/TPL si aplica',
  PRIMARY KEY (`id_canal`),
  KEY `idx_programacion` (`id_programacion`),
  KEY `idx_numero_canal` (`numero_canal`),
  CONSTRAINT `canales_detalle_ibfk_1` FOREIGN KEY (`id_programacion`) REFERENCES `programacion_canales` (`id_programacion`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Detalle de cada canal programado';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `contactos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `contactos` (
  `id_contacto` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `email` varchar(150) NOT NULL,
  `asunto` varchar(150) NOT NULL,
  `mensaje` text NOT NULL,
  `id_usuario` int(11) DEFAULT NULL COMMENT 'Usuario logueado que la envió (NULL = visitante)',
  `mail_enviado` tinyint(1) NOT NULL DEFAULT 0 COMMENT 'Resultado de mail() al recibirla',
  `leido` tinyint(1) NOT NULL DEFAULT 0,
  `ip` varchar(45) DEFAULT NULL,
  `fecha` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_contacto`),
  KEY `idx_fecha` (`fecha`),
  KEY `idx_leido` (`leido`),
  KEY `idx_usuario` (`id_usuario`),
  CONSTRAINT `contactos_ibfk_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Consultas del formulario de contacto';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `equipo_estado`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `equipo_estado` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `id_equipo` int(11) NOT NULL,
  `id_estado` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `id_equipo` (`id_equipo`),
  KEY `id_estado` (`id_estado`),
  CONSTRAINT `equipo_estado_ibfk_1` FOREIGN KEY (`id_equipo`) REFERENCES `equipos` (`id_equipo`) ON DELETE CASCADE,
  CONSTRAINT `equipo_estado_ibfk_2` FOREIGN KEY (`id_estado`) REFERENCES `estados_taller` (`id_estado`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `equipos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `equipos` (
  `id_equipo` int(11) NOT NULL AUTO_INCREMENT,
  `numero_serie` varchar(100) NOT NULL COMMENT 'Identificador único - MAYÚSCULAS sin espacios',
  `tipo` int(2) NOT NULL COMMENT 'HT , Base VHF FM, Base HF, etc.',
  `marca` int(2) NOT NULL,
  `modelo` int(3) NOT NULL,
  `escala` int(2) NOT NULL,
  `sector` varchar(100) NOT NULL,
  `estado` varchar(100) NOT NULL COMMENT 'Operativo, En Stock, En Reparación, De Baja',
  `ult_observacion` varchar(255) DEFAULT NULL COMMENT 'Última observación breve',
  `nombre_plantilla` varchar(150) DEFAULT NULL COMMENT 'Nombre de plantilla de frecuencias programada',
  `valor_potencia` varchar(50) DEFAULT NULL COMMENT 'Valor de potencia (ej: 5W, 25W, etc)',
  `en_papelera` tinyint(1) DEFAULT 0 COMMENT 'TRUE si está en papelera',
  `fecha_ingreso` datetime DEFAULT current_timestamp(),
  `fecha_modificacion` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `usuario_creacion` int(11) DEFAULT NULL COMMENT 'Usuario que ingresó el equipo',
  `usuario_modificacion` int(11) DEFAULT NULL COMMENT 'Último usuario que modificó',
  `en_taller` tinyint(1) DEFAULT 0,
  `id_estado` int(2) DEFAULT NULL,
  PRIMARY KEY (`id_equipo`),
  UNIQUE KEY `numero_serie` (`numero_serie`),
  KEY `idx_numero_serie` (`numero_serie`),
  KEY `idx_tipo` (`tipo`),
  KEY `idx_marca` (`marca`),
  KEY `idx_modelo` (`modelo`),
  KEY `idx_escala` (`escala`),
  KEY `idx_sector` (`sector`),
  KEY `idx_estado` (`estado`),
  KEY `idx_papelera` (`en_papelera`),
  KEY `usuario_creacion` (`usuario_creacion`),
  KEY `usuario_modificacion` (`usuario_modificacion`),
  KEY `idx_equipos_fecha_ingreso` (`fecha_ingreso`),
  KEY `idx_equipos_fecha_modificacion` (`fecha_modificacion`),
  KEY `id_estado` (`id_estado`),
  KEY `idx_equipos_taller_status` (`en_taller`,`id_equipo`),
  CONSTRAINT `equipos_ibfk_1` FOREIGN KEY (`usuario_creacion`) REFERENCES `usuarios` (`id_usuario`) ON DELETE SET NULL,
  CONSTRAINT `equipos_ibfk_2` FOREIGN KEY (`usuario_modificacion`) REFERENCES `usuarios` (`id_usuario`) ON DELETE SET NULL,
  CONSTRAINT `equipos_ibfk_3` FOREIGN KEY (`modelo`) REFERENCES `modelos` (`id_modelo`),
  CONSTRAINT `equipos_ibfk_4` FOREIGN KEY (`escala`) REFERENCES `escalas` (`id_escala`),
  CONSTRAINT `equipos_ibfk_5` FOREIGN KEY (`tipo`) REFERENCES `tipos` (`id_tipo`),
  CONSTRAINT `equipos_ibfk_6` FOREIGN KEY (`marca`) REFERENCES `marcas` (`id_marca`),
  CONSTRAINT `equipos_ibfk_7` FOREIGN KEY (`id_estado`) REFERENCES `estados_taller` (`id_estado`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Equipos de radio del inventario';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `escalas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `escalas` (
  `id_escala` int(2) NOT NULL AUTO_INCREMENT,
  `escala` varchar(3) NOT NULL COMMENT 'AEP, EZE, COR, ROS, ETC.',
  `fecha_creacion` datetime DEFAULT current_timestamp(),
  `usuario_creacion` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_escala`),
  KEY `usuario_creacion` (`usuario_creacion`),
  CONSTRAINT `escalas_ibfk_1` FOREIGN KEY (`usuario_creacion`) REFERENCES `usuarios` (`id_usuario`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Datos predefinidos para combos editables';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `estados_taller`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `estados_taller` (
  `id_estado` int(2) NOT NULL AUTO_INCREMENT,
  `estado` varchar(100) NOT NULL,
  `usuario_modificacion` int(11) DEFAULT NULL,
  `id_equipo` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_estado`),
  KEY `usuario_modificacion` (`usuario_modificacion`),
  KEY `id_equipo` (`id_equipo`),
  KEY `idx_id_equipo_esta` (`id_equipo`),
  CONSTRAINT `estados_taller_ibfk_1` FOREIGN KEY (`usuario_modificacion`) REFERENCES `usuarios` (`id_usuario`) ON DELETE SET NULL,
  CONSTRAINT `estados_taller_ibfk_2` FOREIGN KEY (`id_equipo`) REFERENCES `equipos` (`id_equipo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `historial_equipos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `historial_equipos` (
  `id_historial` bigint(20) NOT NULL AUTO_INCREMENT,
  `id_equipo` int(11) NOT NULL COMMENT 'Equipo relacionado',
  `fecha_evento` datetime DEFAULT current_timestamp(),
  `usuario_evento` int(11) DEFAULT NULL COMMENT 'Usuario que realizó la acción',
  `tipo_evento` varchar(100) NOT NULL COMMENT 'CREACION, MODIFICACION, CAMBIO_ESTADO, INGRESO_TALLER, etc',
  `campo_modificado` varchar(100) DEFAULT NULL COMMENT 'Campo que cambió (si aplica)',
  `valor_anterior` text DEFAULT NULL COMMENT 'Valor antes del cambio',
  `valor_nuevo` text DEFAULT NULL COMMENT 'Valor después del cambio',
  `observaciones` text DEFAULT NULL COMMENT 'Observaciones del evento',
  `ip_usuario` varchar(45) DEFAULT NULL COMMENT 'IP del usuario (auditoría)',
  PRIMARY KEY (`id_historial`),
  KEY `idx_equipo` (`id_equipo`),
  KEY `idx_fecha` (`fecha_evento`),
  KEY `idx_tipo_evento` (`tipo_evento`),
  KEY `idx_usuario` (`usuario_evento`),
  KEY `idx_historial_fecha_usuario` (`fecha_evento`,`usuario_evento`),
  CONSTRAINT `historial_equipos_ibfk_1` FOREIGN KEY (`id_equipo`) REFERENCES `equipos` (`id_equipo`) ON DELETE CASCADE,
  CONSTRAINT `historial_equipos_ibfk_2` FOREIGN KEY (`usuario_evento`) REFERENCES `usuarios` (`id_usuario`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Historial completo de cambios (auditoría total)';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `historial_vehiculos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `historial_vehiculos` (
  `id_historial` int(11) NOT NULL AUTO_INCREMENT,
  `id_vehiculo` int(11) NOT NULL COMMENT 'Equipo relacionado',
  `fecha_evento` datetime DEFAULT current_timestamp(),
  `usuario_evento` int(11) DEFAULT NULL COMMENT 'Usuario que realizó la acción',
  `tipo_evento` varchar(100) NOT NULL COMMENT 'CREACION, MODIFICACION, CAMBIO_ESTADO, etc',
  `campo_modificado` varchar(100) DEFAULT NULL COMMENT 'Campo que cambió (si aplica)',
  `valor_anterior` text DEFAULT NULL COMMENT 'Valor antes del cambio',
  `valor_nuevo` text DEFAULT NULL COMMENT 'Valor después del cambio',
  `observaciones` text DEFAULT NULL COMMENT 'Observaciones del evento',
  PRIMARY KEY (`id_historial`),
  KEY `idx_vehiculo` (`id_vehiculo`),
  KEY `idx_fecha` (`fecha_evento`),
  KEY `idx_tipo_evento` (`tipo_evento`),
  KEY `idx_usuario` (`usuario_evento`),
  CONSTRAINT `historial_vehiculos_ibfk_1` FOREIGN KEY (`id_vehiculo`) REFERENCES `vehiculos` (`id_vehiculo`) ON DELETE CASCADE,
  CONSTRAINT `historial_vehiculos_ibfk_2` FOREIGN KEY (`usuario_evento`) REFERENCES `usuarios` (`id_usuario`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Historial de vehiculos completo';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `marcas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `marcas` (
  `id_marca` int(2) NOT NULL AUTO_INCREMENT,
  `marca` varchar(100) NOT NULL,
  `usuario_creacion` int(11) DEFAULT NULL,
  `id_tipo` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_marca`),
  KEY `usuario_creacion` (`usuario_creacion`),
  KEY `fk_id_tipo` (`id_tipo`),
  CONSTRAINT `fk_id_tipo` FOREIGN KEY (`id_tipo`) REFERENCES `tipos` (`id_tipo`),
  CONSTRAINT `marcas_ibfk_1` FOREIGN KEY (`usuario_creacion`) REFERENCES `usuarios` (`id_usuario`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='MARCAS DE EQUIPOS Y RADIO';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `modelo_repuesto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `modelo_repuesto` (
  `id_modelo` int(11) NOT NULL,
  `id_repuesto` int(11) NOT NULL,
  KEY `id_modelo` (`id_modelo`),
  KEY `id_repuesto` (`id_repuesto`),
  CONSTRAINT `modelo_repuesto_ibfk_1` FOREIGN KEY (`id_modelo`) REFERENCES `modelos` (`id_modelo`),
  CONSTRAINT `modelo_repuesto_ibfk_2` FOREIGN KEY (`id_repuesto`) REFERENCES `repuestos` (`id_repuesto`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `modelos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `modelos` (
  `id_modelo` int(3) NOT NULL AUTO_INCREMENT,
  `modelo_equipo` varchar(150) NOT NULL,
  `marca` int(2) NOT NULL,
  `potencia` varchar(50) DEFAULT NULL,
  `imagen_modelo` varchar(50) DEFAULT NULL,
  `usuario_creacion` int(11) DEFAULT NULL,
  `tipo` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_modelo`),
  KEY `usuario_creacion` (`usuario_creacion`),
  KEY `marca` (`marca`),
  KEY `fk_tipo` (`tipo`),
  CONSTRAINT `fk_tipo` FOREIGN KEY (`tipo`) REFERENCES `tipos` (`id_tipo`),
  CONSTRAINT `modelos_ibfk_1` FOREIGN KEY (`usuario_creacion`) REFERENCES `usuarios` (`id_usuario`) ON DELETE SET NULL,
  CONSTRAINT `modelos_ibfk_2` FOREIGN KEY (`marca`) REFERENCES `marcas` (`id_marca`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Modelos de equipos';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `observaciones_equipos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `observaciones_equipos` (
  `id_observacion` bigint(20) NOT NULL AUTO_INCREMENT,
  `id_equipo` int(11) NOT NULL,
  `fecha_observacion` datetime DEFAULT current_timestamp(),
  `usuario_observacion` int(11) DEFAULT NULL,
  `texto_observacion` text NOT NULL,
  `tipo_observacion` varchar(50) DEFAULT NULL COMMENT 'MANUAL, AUTOMATICA, SISTEMA',
  PRIMARY KEY (`id_observacion`),
  KEY `idx_equipo` (`id_equipo`),
  KEY `idx_fecha` (`fecha_observacion`),
  KEY `usuario_observacion` (`usuario_observacion`),
  CONSTRAINT `observaciones_equipos_ibfk_1` FOREIGN KEY (`id_equipo`) REFERENCES `equipos` (`id_equipo`) ON DELETE CASCADE,
  CONSTRAINT `observaciones_equipos_ibfk_2` FOREIGN KEY (`usuario_observacion`) REFERENCES `usuarios` (`id_usuario`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Observaciones y comentarios de equipos';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `observaciones_taller`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `observaciones_taller` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `id_equipo` int(11) NOT NULL,
  `usuario_observacion` int(11) NOT NULL,
  `fecha_observacion` datetime DEFAULT current_timestamp(),
  `observacion` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `usuario_observacion` (`usuario_observacion`),
  KEY `idx_id_equipo_obs` (`id_equipo`),
  CONSTRAINT `observaciones_taller_ibfk_1` FOREIGN KEY (`id_equipo`) REFERENCES `equipos` (`id_equipo`) ON DELETE CASCADE,
  CONSTRAINT `observaciones_taller_ibfk_2` FOREIGN KEY (`usuario_observacion`) REFERENCES `usuarios` (`id_usuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `papelera`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `papelera` (
  `id_papelera` int(11) NOT NULL AUTO_INCREMENT,
  `id_equipo` int(11) NOT NULL COMMENT 'Equipo enviado a papelera',
  `fecha_eliminacion` datetime DEFAULT current_timestamp(),
  `usuario_eliminacion` int(11) DEFAULT NULL COMMENT 'Usuario que envió a papelera',
  `motivo_eliminacion` text DEFAULT NULL COMMENT 'Motivo de eliminación',
  `puede_restaurar` tinyint(1) DEFAULT 1 COMMENT 'Solo admin puede eliminar definitivamente',
  `numero_serie` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id_papelera`),
  KEY `idx_equipo` (`id_equipo`),
  KEY `idx_fecha` (`fecha_eliminacion`),
  KEY `usuario_eliminacion` (`usuario_eliminacion`),
  KEY `idx_papelera_fecha` (`fecha_eliminacion`),
  CONSTRAINT `papelera_ibfk_1` FOREIGN KEY (`id_equipo`) REFERENCES `equipos` (`id_equipo`) ON DELETE CASCADE,
  CONSTRAINT `papelera_ibfk_2` FOREIGN KEY (`usuario_eliminacion`) REFERENCES `usuarios` (`id_usuario`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Papelera de reciclaje - Equipos eliminados';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `papelera_vehiculos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `papelera_vehiculos` (
  `id_papelera_vehiculo` int(11) NOT NULL AUTO_INCREMENT,
  `id_vehiculo` int(11) NOT NULL,
  `fecha_eliminacion` datetime DEFAULT current_timestamp(),
  `usuario_eliminacion` int(11) DEFAULT NULL COMMENT 'Usuario que envio a papelera',
  `motivo_eliminacion` text DEFAULT NULL COMMENT 'Motivo de eliminacion',
  `puede_restaurar` tinyint(1) DEFAULT 1 COMMENT 'Solo admin',
  `identificacion` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id_papelera_vehiculo`),
  KEY `idx_vehiculo` (`id_vehiculo`),
  KEY `idx_fecha` (`fecha_eliminacion`),
  KEY `usuario_eliminacion` (`usuario_eliminacion`),
  CONSTRAINT `papelera_vehiculos_ibfk_1` FOREIGN KEY (`id_vehiculo`) REFERENCES `vehiculos` (`id_vehiculo`) ON DELETE CASCADE,
  CONSTRAINT `papelera_vehiculos_ibfk_2` FOREIGN KEY (`usuario_eliminacion`) REFERENCES `usuarios` (`id_usuario`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Papelera de vehiculos - Vehiculos eliminados';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `potencias`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `potencias` (
  `id_potencia` int(11) NOT NULL AUTO_INCREMENT,
  `valor_potencia` varchar(50) NOT NULL COMMENT 'Valor de potencia (ej: 5W, 25W, etc)',
  `fecha_creacion` datetime DEFAULT current_timestamp(),
  `usuario_creacion` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_potencia`),
  KEY `usuario_creacion` (`usuario_creacion`),
  CONSTRAINT `potencias_ibfk_1` FOREIGN KEY (`usuario_creacion`) REFERENCES `usuarios` (`id_usuario`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Valores de potencia predefinidos para equipos';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `programacion_canales`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `programacion_canales` (
  `id_programacion` int(11) NOT NULL AUTO_INCREMENT,
  `id_equipo` int(11) DEFAULT NULL COMMENT 'numero de serie',
  `cantidad_canales` int(11) DEFAULT 16 COMMENT 'Total de canales programados',
  `nombre_plantilla` varchar(150) DEFAULT NULL COMMENT 'Nombre de plantilla guardada',
  `fecha_programacion` datetime DEFAULT current_timestamp(),
  `usuario_programacion` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_programacion`),
  KEY `idx_equipo` (`id_equipo`),
  KEY `usuario_programacion` (`usuario_programacion`),
  CONSTRAINT `programacion_canales_ibfk_1` FOREIGN KEY (`id_equipo`) REFERENCES `equipos` (`id_equipo`) ON DELETE CASCADE,
  CONSTRAINT `programacion_canales_ibfk_2` FOREIGN KEY (`usuario_programacion`) REFERENCES `usuarios` (`id_usuario`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Programación de frecuencias por equipo';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `recuperaciones_clave`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `recuperaciones_clave` (
  `id_recuperacion` int(11) NOT NULL AUTO_INCREMENT,
  `id_usuario` int(11) NOT NULL,
  `token_hash` char(64) NOT NULL COMMENT 'SHA-256 del token enviado por correo',
  `vence` datetime NOT NULL,
  `usado` tinyint(1) NOT NULL DEFAULT 0,
  `ip` varchar(45) DEFAULT NULL,
  `fecha` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_recuperacion`),
  UNIQUE KEY `token_hash` (`token_hash`),
  KEY `idx_usuario` (`id_usuario`),
  CONSTRAINT `recuperaciones_clave_ibfk_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Enlaces de recuperación de contraseña';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `repuesto_stock`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `repuesto_stock` (
  `id_repuesto` int(11) NOT NULL,
  `id_taller` int(11) NOT NULL,
  `stock_actual` int(11) NOT NULL DEFAULT 0,
  `fuera_servicio` int(11) NOT NULL DEFAULT 0,
  `fecha_ingreso` datetime DEFAULT NULL,
  `baja_repuesto` int(11) DEFAULT 0,
  `ultima_fecha_baja` datetime DEFAULT NULL,
  PRIMARY KEY (`id_repuesto`,`id_taller`),
  KEY `fk_id_taller` (`id_taller`),
  CONSTRAINT `fk_id_repuesto` FOREIGN KEY (`id_repuesto`) REFERENCES `repuestos` (`id_repuesto`),
  CONSTRAINT `fk_id_taller` FOREIGN KEY (`id_taller`) REFERENCES `talleres` (`id_taller`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `repuestos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `repuestos` (
  `id_repuesto` int(11) NOT NULL AUTO_INCREMENT,
  `numero_parte` varchar(60) DEFAULT NULL,
  `nombre` varchar(100) NOT NULL,
  `descripcion` varchar(100) DEFAULT NULL,
  `stock_actual` int(11) NOT NULL,
  `fecha_ingreso` datetime DEFAULT current_timestamp(),
  `id_usuario` int(11) DEFAULT NULL,
  `en_uso` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id_repuesto`),
  KEY `id_usuario` (`id_usuario`),
  CONSTRAINT `repuestos_ibfk_1` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `taller_egreso_repuestos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `taller_egreso_repuestos` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `id_egreso` int(11) NOT NULL,
  `id_repuesto` int(11) DEFAULT NULL COMMENT 'NULL si el repuesto se dio de baja después',
  `nombre_repuesto` varchar(100) NOT NULL COMMENT 'Copia del nombre al momento del egreso',
  `id_taller` int(11) NOT NULL COMMENT 'Taller del que salió el stock',
  `cantidad` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_egreso` (`id_egreso`),
  KEY `idx_repuesto` (`id_repuesto`),
  KEY `fk_ter_taller` (`id_taller`),
  CONSTRAINT `fk_ter_egreso` FOREIGN KEY (`id_egreso`) REFERENCES `taller_egresos` (`id_egreso`) ON DELETE CASCADE,
  CONSTRAINT `fk_ter_repuesto` FOREIGN KEY (`id_repuesto`) REFERENCES `repuestos` (`id_repuesto`) ON DELETE SET NULL,
  CONSTRAINT `fk_ter_taller` FOREIGN KEY (`id_taller`) REFERENCES `talleres` (`id_taller`),
  CONSTRAINT `chk_ter_cantidad` CHECK (`cantidad` > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Repuestos del catálogo usados en cada egreso de taller';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `taller_egresos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `taller_egresos` (
  `id_egreso` int(11) NOT NULL AUTO_INCREMENT,
  `id_ingreso` int(11) NOT NULL COMMENT 'Ingreso relacionado',
  `fecha_egreso` datetime DEFAULT current_timestamp(),
  `usuario_egreso` int(11) DEFAULT NULL,
  `numero_guia` varchar(100) DEFAULT NULL COMMENT 'N° de guía de envío',
  `tarea_soldadura_smd` tinyint(1) DEFAULT 0,
  `tarea_verificacion_rf` tinyint(1) DEFAULT 0,
  `tarea_reprogramacion` tinyint(1) DEFAULT 0,
  `tarea_reasignacion` tinyint(1) DEFAULT 0,
  `tarea_otros` tinyint(1) DEFAULT 0,
  `detalle_otros_tareas` text DEFAULT NULL,
  `repuesto_potenciometro` tinyint(1) DEFAULT 0,
  `repuesto_carcaza` tinyint(1) DEFAULT 0,
  `repuesto_switch_ptt` tinyint(1) DEFAULT 0,
  `repuesto_plastico_ptt` tinyint(1) DEFAULT 0,
  `repuesto_goma_ptt` tinyint(1) DEFAULT 0,
  `repuesto_display` tinyint(1) DEFAULT 0,
  `repuesto_parlante` tinyint(1) DEFAULT 0,
  `repuesto_microfono` tinyint(1) DEFAULT 0,
  `repuesto_antena` tinyint(1) DEFAULT 0,
  `repuesto_bateria` tinyint(1) DEFAULT 0,
  `repuesto_clip_cintura` tinyint(1) DEFAULT 0,
  `repuesto_conector_rf` tinyint(1) DEFAULT 0,
  `repuesto_otros` tinyint(1) DEFAULT 0,
  `detalle_otros_repuestos` text DEFAULT NULL,
  `texto_email_informe` text DEFAULT NULL COMMENT 'Texto generado del informe',
  `id_observacion` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id_egreso`),
  KEY `idx_ingreso` (`id_ingreso`),
  KEY `usuario_egreso` (`usuario_egreso`),
  KEY `fk_observacion_egresos` (`id_observacion`),
  KEY `idx_id_ingreso_tae` (`id_ingreso`),
  CONSTRAINT `fk_observacion_egresos` FOREIGN KEY (`id_observacion`) REFERENCES `observaciones_equipos` (`id_observacion`),
  CONSTRAINT `taller_egresos_ibfk_1` FOREIGN KEY (`id_ingreso`) REFERENCES `taller_ingresos` (`id_ingreso`) ON DELETE CASCADE,
  CONSTRAINT `taller_egresos_ibfk_2` FOREIGN KEY (`usuario_egreso`) REFERENCES `usuarios` (`id_usuario`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Egresos de equipos del taller';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `taller_ingresos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `taller_ingresos` (
  `id_ingreso` int(11) NOT NULL AUTO_INCREMENT,
  `id_equipo` int(11) NOT NULL,
  `taller` int(11) DEFAULT NULL,
  `numero_ticket_sd` varchar(100) DEFAULT NULL COMMENT 'N° de ticket SD (opcional)',
  `fecha_ingreso` datetime DEFAULT current_timestamp(),
  `usuario_ingreso` int(11) DEFAULT NULL,
  `componente_equipo` tinyint(1) DEFAULT 0,
  `componente_antena` tinyint(1) DEFAULT 0,
  `componente_cargador` tinyint(1) DEFAULT 0,
  `componente_bateria` tinyint(1) DEFAULT 0,
  `componente_fuente` tinyint(1) DEFAULT 0,
  `componente_cables` tinyint(1) DEFAULT 0,
  `componente_otros` tinyint(1) DEFAULT 0,
  `detalle_otros_componentes` text DEFAULT NULL,
  `egresado` tinyint(1) DEFAULT 0 COMMENT 'TRUE si ya egresó del taller',
  `ingreso_de_inventario` int(11) DEFAULT NULL,
  `estado` int(11) DEFAULT NULL,
  `id_observacion` bigint(20) DEFAULT NULL,
  `id_recepcion` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_ingreso`),
  KEY `idx_equipo` (`id_equipo`),
  KEY `idx_taller` (`taller`),
  KEY `idx_egresado` (`egresado`),
  KEY `usuario_ingreso` (`usuario_ingreso`),
  KEY `idx_taller_fecha_ingreso` (`fecha_ingreso`),
  KEY `ingreso_de_inventario` (`ingreso_de_inventario`),
  KEY `fk_estado` (`estado`),
  KEY `fk_observacion_ingresos` (`id_observacion`),
  KEY `idx_id_equipo_tai` (`id_equipo`),
  KEY `recepcion_id_fk` (`id_recepcion`),
  CONSTRAINT `fk_estado` FOREIGN KEY (`estado`) REFERENCES `estados_taller` (`id_estado`),
  CONSTRAINT `fk_observacion_ingresos` FOREIGN KEY (`id_observacion`) REFERENCES `observaciones_equipos` (`id_observacion`),
  CONSTRAINT `fk_taller` FOREIGN KEY (`taller`) REFERENCES `talleres` (`id_taller`),
  CONSTRAINT `recepcion_id_fk` FOREIGN KEY (`id_recepcion`) REFERENCES `taller_recepcion` (`id_recepcion`),
  CONSTRAINT `taller_ingresos_ibfk_1` FOREIGN KEY (`id_equipo`) REFERENCES `equipos` (`id_equipo`) ON DELETE CASCADE,
  CONSTRAINT `taller_ingresos_ibfk_2` FOREIGN KEY (`usuario_ingreso`) REFERENCES `usuarios` (`id_usuario`) ON DELETE SET NULL,
  CONSTRAINT `taller_ingresos_ibfk_4` FOREIGN KEY (`ingreso_de_inventario`) REFERENCES `usuarios` (`id_usuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Ingresos de equipos a taller';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `taller_recepcion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `taller_recepcion` (
  `id_recepcion` int(11) NOT NULL AUTO_INCREMENT,
  `id_taller` int(11) NOT NULL,
  `id_equipo` int(11) NOT NULL,
  `ingresado` tinyint(1) DEFAULT 0,
  `id_estado` int(11) DEFAULT NULL,
  `fecha_recepcion` datetime DEFAULT current_timestamp(),
  `usuario_modificacion` int(11) DEFAULT NULL,
  `id_observacion` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id_recepcion`),
  KEY `idx_equipo` (`id_equipo`),
  KEY `idx_fecha` (`fecha_recepcion`),
  KEY `idx_usuario` (`usuario_modificacion`),
  KEY `id_taller` (`id_taller`),
  KEY `id_estado` (`id_estado`),
  KEY `fk_observacion_recepcion` (`id_observacion`),
  KEY `idx_id_equipo_tar` (`id_equipo`),
  KEY `idx_fecha_recep` (`fecha_recepcion`),
  CONSTRAINT `fk_observacion_recepcion` FOREIGN KEY (`id_observacion`) REFERENCES `observaciones_equipos` (`id_observacion`),
  CONSTRAINT `taller_recepcion_ibfk_1` FOREIGN KEY (`id_equipo`) REFERENCES `equipos` (`id_equipo`) ON DELETE CASCADE,
  CONSTRAINT `taller_recepcion_ibfk_2` FOREIGN KEY (`id_taller`) REFERENCES `talleres` (`id_taller`),
  CONSTRAINT `taller_recepcion_ibfk_3` FOREIGN KEY (`id_estado`) REFERENCES `estados_taller` (`id_estado`),
  CONSTRAINT `taller_recepcion_ibfk_4` FOREIGN KEY (`usuario_modificacion`) REFERENCES `usuarios` (`id_usuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `talleres`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `talleres` (
  `id_taller` int(11) NOT NULL AUTO_INCREMENT,
  `taller` varchar(100) NOT NULL,
  PRIMARY KEY (`id_taller`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tipos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tipos` (
  `id_tipo` int(11) NOT NULL AUTO_INCREMENT,
  `tipo` varchar(100) NOT NULL COMMENT 'Tipo',
  `fecha_creacion` datetime DEFAULT current_timestamp(),
  `usuario_creacion` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_tipo`),
  KEY `usuario_creacion` (`usuario_creacion`),
  CONSTRAINT `tipos_ibfk_1` FOREIGN KEY (`usuario_creacion`) REFERENCES `usuarios` (`id_usuario`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Tipos de equipos';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `usuarios` (
  `id_usuario` int(11) NOT NULL AUTO_INCREMENT,
  `legajo` varchar(50) NOT NULL COMMENT 'Usuario para login',
  `username` varchar(100) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `apellido` varchar(100) NOT NULL,
  `email` varchar(150) DEFAULT NULL,
  `password_hash` varchar(255) NOT NULL COMMENT 'Contraseña encriptada',
  `es_administrador` tinyint(1) DEFAULT 0,
  `debe_cambiar_clave` tinyint(1) DEFAULT 1 COMMENT 'Obligar cambio en primer login',
  `activo` tinyint(1) DEFAULT 1,
  `pendiente_aprobacion` tinyint(1) NOT NULL DEFAULT 0 COMMENT 'Registrado desde la portada, a la espera de que un administrador lo apruebe',
  `fecha_creacion` datetime DEFAULT current_timestamp(),
  `fecha_ultima_conexion` datetime DEFAULT NULL,
  `creado_por` int(11) DEFAULT NULL COMMENT 'ID del usuario que lo creó',
  `intentos_fallidos` int(9) NOT NULL DEFAULT 0,
  `bloqueado_hasta` datetime DEFAULT NULL,
  PRIMARY KEY (`id_usuario`),
  UNIQUE KEY `legajo` (`legajo`),
  UNIQUE KEY `legajo_2` (`legajo`),
  UNIQUE KEY `username` (`username`),
  KEY `idx_legajo` (`legajo`),
  KEY `idx_activo` (`activo`),
  KEY `creado_por` (`creado_por`),
  CONSTRAINT `usuarios_ibfk_1` FOREIGN KEY (`creado_por`) REFERENCES `usuarios` (`id_usuario`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Usuarios del sistema';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `vehiculos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `vehiculos` (
  `id_vehiculo` int(11) NOT NULL AUTO_INCREMENT,
  `tipo_vehiculo` varchar(100) NOT NULL,
  `identificacion` varchar(100) NOT NULL COMMENT 'N° interno, patente, etc',
  `escala` int(2) NOT NULL COMMENT 'Código de 3 letras MAYÚSCULAS',
  `radio_asignado` int(11) DEFAULT NULL COMMENT 'ID del equipo asignado (solo VHF FM Base)',
  `fecha_creacion` datetime DEFAULT current_timestamp(),
  `fecha_modificacion` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `usuario_creacion` int(11) DEFAULT NULL,
  `usuario_modificacion` int(11) DEFAULT NULL,
  `de_baja` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`id_vehiculo`),
  KEY `idx_identificacion` (`identificacion`),
  KEY `idx_escala` (`escala`),
  KEY `idx_radio` (`radio_asignado`),
  KEY `usuario_creacion` (`usuario_creacion`),
  KEY `usuario_modificacion` (`usuario_modificacion`),
  CONSTRAINT `vehiculos_ibfk_1` FOREIGN KEY (`radio_asignado`) REFERENCES `equipos` (`id_equipo`) ON DELETE SET NULL,
  CONSTRAINT `vehiculos_ibfk_2` FOREIGN KEY (`usuario_creacion`) REFERENCES `usuarios` (`id_usuario`) ON DELETE SET NULL,
  CONSTRAINT `vehiculos_ibfk_3` FOREIGN KEY (`usuario_modificacion`) REFERENCES `usuarios` (`id_usuario`) ON DELETE SET NULL,
  CONSTRAINT `vehiculos_ibfk_4` FOREIGN KEY (`escala`) REFERENCES `escalas` (`id_escala`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Vehículos con radios asignadas';
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

