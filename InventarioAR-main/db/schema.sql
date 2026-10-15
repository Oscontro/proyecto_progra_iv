
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
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_AUTO_VALUE_ON_ZERO' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_equipos_after_insert` AFTER INSERT ON `equipos` FOR EACH ROW BEGIN
    INSERT INTO historial_equipos (
        id_equipo, 
        usuario_evento, 
        tipo_evento, 
        observaciones
    ) VALUES (
        NEW.id_equipo,
        @usuario_actual,
        'ALTA_EQUIPO',
        CONCAT('Equipo creado: ', 
            NEW.numero_serie, ' - ', 
            (SELECT marca FROM marcas WHERE id_marca = NEW.marca), ' ', 
            (SELECT modelo_equipo FROM modelos WHERE id_modelo = NEW.modelo)
    ));
    
    INSERT INTO observaciones_equipos (
        id_equipo,
        usuario_observacion,
        texto_observacion,
        tipo_observacion
    ) VALUES (
        NEW.id_equipo,
        @usuario_actual,
        CONCAT('Equipo ingresado al sistema el ', DATE_FORMAT(NEW.fecha_ingreso, '%d/%m/%Y %H:%i')),
        'SISTEMA'
    );
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_AUTO_VALUE_ON_ZERO' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_equipos_after_envio_taller` AFTER UPDATE ON `equipos` FOR EACH ROW IF OLD.en_taller = FALSE AND NEW.en_taller = TRUE THEN
    INSERT INTO historial_equipos (
        id_equipo,
        usuario_evento,
        tipo_evento,
        observaciones
    ) VALUES (
        NEW.id_equipo,
        @usuario_actual,
        'ENVIADO_A_TALLER',
        CONCAT('Equipo enviado a taller: ', 
            COALESCE(
                (SELECT estado FROM estados_taller WHERE id_estado = NEW.id_estado), 
                'Sin especificar'
            )
        )
    );
END IF */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_AUTO_VALUE_ON_ZERO' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_equipos_after_update` AFTER UPDATE ON `equipos` FOR EACH ROW BEGIN
    
    IF OLD.tipo <> NEW.tipo THEN
        INSERT INTO historial_equipos (
            id_equipo,
            usuario_evento,
            tipo_evento,
            campo_modificado,
            valor_anterior,
            valor_nuevo,
            observaciones
        ) VALUES (
            NEW.id_equipo,
            @usuario_actual,
            'CAMBIO_TIPO',
            'tipo',
            (SELECT tipo FROM tipos WHERE id_tipo = OLD.tipo),
            (SELECT tipo FROM tipos WHERE id_tipo = NEW.tipo),
            CONCAT('Tipo cambiado de "', 
                   (SELECT tipo FROM tipos WHERE id_tipo = OLD.tipo), 
                   '" a "', 
                   (SELECT tipo FROM tipos WHERE id_tipo = NEW.tipo), '"')
        );
    END IF;

    
    IF OLD.marca <> NEW.marca THEN
        INSERT INTO historial_equipos (
            id_equipo,
            usuario_evento,
            tipo_evento,
            campo_modificado,
            valor_anterior,
            valor_nuevo,
            observaciones
        ) VALUES (
            NEW.id_equipo,
            @usuario_actual,
            'CAMBIO_MARCA',
            'marca',
            (SELECT marca FROM marcas WHERE id_marca = OLD.marca),
            (SELECT marca FROM marcas WHERE id_marca = NEW.marca),
            CONCAT('Marca cambiada de "', 
                   (SELECT marca FROM marcas WHERE id_marca = OLD.marca), 
                   '" a "', 
                   (SELECT marca FROM marcas WHERE id_marca = NEW.marca), '"')
        );
    END IF;

    
    IF OLD.modelo <> NEW.modelo THEN
        INSERT INTO historial_equipos (
            id_equipo,
            usuario_evento,
            tipo_evento,
            campo_modificado,
            valor_anterior,
            valor_nuevo,
            observaciones
        ) VALUES (
            NEW.id_equipo,
            @usuario_actual,
            'CAMBIO_MODELO',
            'modelo',
            (SELECT modelo_equipo FROM modelos WHERE id_modelo = OLD.modelo),
            (SELECT modelo_equipo FROM modelos WHERE id_modelo = NEW.modelo),
            CONCAT('Modelo cambiado de "', 
                   (SELECT modelo_equipo FROM modelos WHERE id_modelo = OLD.modelo), 
                   '" a "', 
                   (SELECT modelo_equipo FROM modelos WHERE id_modelo = NEW.modelo), '"')
        );
    END IF;

    
    IF OLD.escala <> NEW.escala THEN
        INSERT INTO historial_equipos (
            id_equipo,
            usuario_evento,
            tipo_evento,
            campo_modificado,
            valor_anterior,
            valor_nuevo,
            observaciones
        ) VALUES (
            NEW.id_equipo,
            @usuario_actual,
            'CAMBIO_ESCALA',
            'escala',
            (SELECT escala FROM escalas WHERE id_escala = OLD.escala),
            (SELECT escala FROM escalas WHERE id_escala = NEW.escala),
            CONCAT('Escala cambiada de "', 
                   (SELECT escala FROM escalas WHERE id_escala = OLD.escala), 
                   '" a "', 
                   (SELECT escala FROM escalas WHERE id_escala = NEW.escala), '"')
        );
    END IF;

    
    IF OLD.sector <> NEW.sector THEN
        INSERT INTO historial_equipos (
            id_equipo,
            usuario_evento,
            tipo_evento,
            campo_modificado,
            valor_anterior,
            valor_nuevo,
            observaciones
        ) VALUES (
            NEW.id_equipo,
            @usuario_actual,
            'CAMBIO_SECTOR',
            'sector',
            OLD.sector,
            NEW.sector,
            CONCAT('Sector cambiado de "', OLD.sector, '" a "', NEW.sector, '"')
        );
    END IF;

    
    IF OLD.estado <> NEW.estado THEN
        INSERT INTO historial_equipos (
            id_equipo,
            usuario_evento,
            tipo_evento,
            campo_modificado,
            valor_anterior,
            valor_nuevo,
            observaciones
        ) VALUES (
            NEW.id_equipo,
            @usuario_actual,
            'CAMBIO_ESTADO',
            'estado',
            OLD.estado,
            NEW.estado,
            CONCAT('Estado cambiado de "', OLD.estado, '" a "', NEW.estado, '"')
        );
    END IF;
    
    
    IF OLD.en_papelera = FALSE AND NEW.en_papelera = TRUE THEN
        INSERT INTO historial_equipos (
            id_equipo,
            usuario_evento,
            tipo_evento,
            observaciones
        ) VALUES (
            NEW.id_equipo,
            @usuario_actual,
            'ENVIADO_PAPELERA',
            'Equipo enviado a la papelera'
        );
    END IF;
    
    
    IF OLD.en_papelera = TRUE AND NEW.en_papelera = FALSE THEN
        INSERT INTO historial_equipos (
            id_equipo,
            usuario_evento,
            tipo_evento,
            observaciones
        ) VALUES (
            NEW.id_equipo,
            @usuario_actual,
            'RESTAURADO_PAPELERA',
            'Equipo restaurado desde la papelera'
        );
    END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
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
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_AUTO_VALUE_ON_ZERO' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_stock_taller_after_insert` AFTER INSERT ON `repuesto_stock` FOR EACH ROW BEGIN
    UPDATE repuestos
    SET stock_actual = (
        SELECT COALESCE(SUM(stock_actual), 0)
        FROM repuesto_stock
        WHERE id_repuesto = NEW.id_repuesto
    )
    WHERE id_repuesto = NEW.id_repuesto;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_AUTO_VALUE_ON_ZERO' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_stock_taller_after_update` AFTER UPDATE ON `repuesto_stock` FOR EACH ROW BEGIN
    UPDATE repuestos
    SET stock_actual = (
        SELECT COALESCE(SUM(stock_actual), 0)
        FROM repuesto_stock
        WHERE id_repuesto = NEW.id_repuesto
    )
    WHERE id_repuesto = NEW.id_repuesto;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_AUTO_VALUE_ON_ZERO' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_stock_taller_after_delete` AFTER DELETE ON `repuesto_stock` FOR EACH ROW BEGIN
    UPDATE repuestos
    SET stock_actual = (
        SELECT COALESCE(SUM(stock_actual), 0)
        FROM repuesto_stock
        WHERE id_repuesto = OLD.id_repuesto
    )
    WHERE id_repuesto = OLD.id_repuesto;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
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
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_AUTO_VALUE_ON_ZERO' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_taller_egresos_after_insert` AFTER INSERT ON `taller_egresos` FOR EACH ROW BEGIN
    DECLARE equipo_id INT;
    
    SELECT id_equipo INTO equipo_id 
    FROM taller_ingresos 
    WHERE id_ingreso = NEW.id_ingreso;
    
    INSERT INTO historial_equipos (
        id_equipo,
        usuario_evento,
        tipo_evento,
        observaciones
    ) VALUES (
        equipo_id,
        @usuario_actual,
        'EGRESO_TALLER',
        'Equipo egresado del taller'
    );
    
    
    UPDATE taller_ingresos 
    SET egresado = TRUE 
    WHERE id_ingreso = NEW.id_ingreso;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
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
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_AUTO_VALUE_ON_ZERO' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_taller_ingresos_after_insert` AFTER INSERT ON `taller_ingresos` FOR EACH ROW BEGIN
    INSERT INTO historial_equipos (
        id_equipo,
        usuario_evento,
        tipo_evento,
        observaciones
    ) VALUES (
        NEW.id_equipo,
        @usuario_actual,
        'INGRESO_TALLER',
        CONCAT('Equipo ingresado a ', (SELECT taller from talleres where id_taller = NEW.taller), 
               CASE WHEN NEW.numero_ticket_sd IS NOT NULL 
                    THEN CONCAT(' - Ticket SD: ', NEW.numero_ticket_sd)
                    ELSE '' 
               END)
    );
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
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
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_AUTO_VALUE_ON_ZERO' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_historial_vehiculos_after_insert` AFTER INSERT ON `vehiculos` FOR EACH ROW BEGIN
    INSERT INTO historial_vehiculos (
        id_vehiculo,
        usuario_evento,
        tipo_evento,
        observaciones
    ) VALUES (
        NEW.id_vehiculo,
        @usuario_actual,
        'CREACION',
        CONCAT('Vehiculo creado: ', NEW.identificacion)
    );
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_AUTO_VALUE_ON_ZERO' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_vehiculos_after_update` AFTER UPDATE ON `vehiculos` FOR EACH ROW BEGIN
    IF OLD.radio_asignado IS NULL AND NEW.radio_asignado IS NOT NULL THEN
        INSERT INTO historial_equipos (
            id_equipo,
            usuario_evento,
            tipo_evento,
            observaciones
        ) VALUES (
            NEW.radio_asignado,
            @usuario_actual,
            'ASIGNADO_VEHICULO',
            CONCAT('Radio asignado al vehículo: ', NEW.tipo_vehiculo, ' - ', NEW.identificacion)
        );
    END IF;
    
    IF OLD.radio_asignado IS NOT NULL AND NEW.radio_asignado IS NULL THEN
        INSERT INTO historial_equipos (
            id_equipo,
            usuario_evento,
            tipo_evento,
            observaciones
        ) VALUES (
            OLD.radio_asignado,
            @usuario_actual,
            'DESASIGNADO_VEHICULO',
            CONCAT('Radio desasignado del vehículo: ', NEW.tipo_vehiculo, ' - ', NEW.identificacion)
        );
    END IF;
    
        
    IF OLD.escala <> NEW.escala THEN
        INSERT INTO historial_vehiculos (
            id_vehiculo,
            usuario_evento,
            tipo_evento,
            campo_modificado,
            valor_anterior,
            valor_nuevo,
            observaciones
        ) VALUES (
            NEW.id_vehiculo,
            @usuario_actual,
            'CAMBIO_ESCALA',
            'escala',
            (SELECT escala FROM escalas WHERE id_escala = OLD.escala),
            (SELECT escala FROM escalas WHERE id_escala = NEW.escala),
            CONCAT('Escala cambiada de "', 
                   (SELECT escala FROM escalas WHERE id_escala = OLD.escala), 
                   '" a "', 
                   (SELECT escala FROM escalas WHERE id_escala = NEW.escala), '"')
        );
    END IF;
    
        
    IF OLD.de_baja = FALSE AND NEW.de_baja = TRUE THEN
        INSERT INTO historial_vehiculos (
            id_vehiculo,
            usuario_evento,
            tipo_evento,
            observaciones
        ) VALUES (
            NEW.id_vehiculo,
            @usuario_actual,
            'BAJA_VEHICULO',
            'Vehiculo dado de baja'
        );
    END IF;
    
    
    IF OLD.de_baja = TRUE AND NEW.de_baja = FALSE THEN
        INSERT INTO historial_vehiculos (
            id_vehiculo,
            usuario_evento,
            tipo_evento,
            observaciones
        ) VALUES (
            NEW.id_vehiculo,
            @usuario_actual,
            'ALTA DE VEHICULO',
            'Vehiculo restaurado'
        );
    END IF;
    
        IF OLD.radio_asignado IS NULL AND NEW.radio_asignado IS NOT NULL THEN
        INSERT INTO historial_vehiculos (
            id_vehiculo,
            usuario_evento,
            tipo_evento,
            observaciones
        ) VALUES (
            NEW.id_vehiculo,
            @usuario_actual,
            'RADIO_ASIGNADA',
            CONCAT('Radio asignada: ',(SELECT numero_serie FROM equipos WHERE id_equipo = NEW.radio_asignado))
        );
    END IF;
    
    IF OLD.radio_asignado IS NOT NULL AND NEW.radio_asignado IS NULL THEN
        INSERT INTO historial_vehiculos (
            id_vehiculo,
            usuario_evento,
            tipo_evento,
            observaciones
        ) VALUES (
            OLD.id_vehiculo,
            @usuario_actual,
            'RADIO_DESASIGNADA',
            CONCAT('Radio desasignado: ', (SELECT numero_serie FROM equipos WHERE id_equipo = OLD.radio_asignado))
        );
    END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
DROP TABLE IF EXISTS `vista_equipo_etiqueta`;
/*!50001 DROP VIEW IF EXISTS `vista_equipo_etiqueta`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `vista_equipo_etiqueta` AS SELECT
 1 AS `tipo`,
  1 AS `marca`,
  1 AS `modelo_equipo`,
  1 AS `numero_serie`,
  1 AS `escala`,
  1 AS `sector`,
  1 AS `estado`,
  1 AS `usuario_modificacion` */;
SET character_set_client = @saved_cs_client;
DROP TABLE IF EXISTS `vista_equipos_papelera`;
/*!50001 DROP VIEW IF EXISTS `vista_equipos_papelera`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `vista_equipos_papelera` AS SELECT
 1 AS `id_equipo`,
  1 AS `numero_serie`,
  1 AS `tipo`,
  1 AS `marca`,
  1 AS `modelo_equipo`,
  1 AS `escala`,
  1 AS `sector`,
  1 AS `fecha_eliminacion` */;
SET character_set_client = @saved_cs_client;
DROP TABLE IF EXISTS `vista_equipos_taller`;
/*!50001 DROP VIEW IF EXISTS `vista_equipos_taller`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `vista_equipos_taller` AS SELECT
 1 AS `numero_serie`,
  1 AS `tipo`,
  1 AS `marca`,
  1 AS `modelo`,
  1 AS `escala`,
  1 AS `sector`,
  1 AS `estado`,
  1 AS `taller`,
  1 AS `fecha_ingreso`,
  1 AS `numero_ticket_sd`,
  1 AS `egresado`,
  1 AS `usuario_ingreso` */;
SET character_set_client = @saved_cs_client;
DROP TABLE IF EXISTS `vista_equipos_v3`;
/*!50001 DROP VIEW IF EXISTS `vista_equipos_v3`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `vista_equipos_v3` AS SELECT
 1 AS `id_equipo`,
  1 AS `numero_serie`,
  1 AS `tipo`,
  1 AS `marca`,
  1 AS `modelo_equipo`,
  1 AS `escala`,
  1 AS `sector`,
  1 AS `estado`,
  1 AS `valor_potencia`,
  1 AS `nombre_plantilla`,
  1 AS `ult_observacion`,
  1 AS `en_papelera`,
  1 AS `en_taller`,
  1 AS `fecha_ingreso`,
  1 AS `fecha_modificacion`,
  1 AS `usuario_creacion`,
  1 AS `usuario_modificacion`,
  1 AS `cantidad_canales`,
  1 AS `vehiculo_asignado` */;
SET character_set_client = @saved_cs_client;
DROP TABLE IF EXISTS `vista_equipos_v4`;
/*!50001 DROP VIEW IF EXISTS `vista_equipos_v4`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `vista_equipos_v4` AS SELECT
 1 AS `id_equipo`,
  1 AS `numero_serie`,
  1 AS `tipo`,
  1 AS `marca`,
  1 AS `modelo_equipo`,
  1 AS `escala`,
  1 AS `sector`,
  1 AS `estado`,
  1 AS `potencia`,
  1 AS `nombre_plantilla`,
  1 AS `ult_observacion`,
  1 AS `en_papelera`,
  1 AS `en_taller`,
  1 AS `fecha_ingreso`,
  1 AS `fecha_modificacion`,
  1 AS `usuario_creacion`,
  1 AS `usuario_modificacion`,
  1 AS `cantidad_canales`,
  1 AS `vehiculo_asignado` */;
SET character_set_client = @saved_cs_client;
DROP TABLE IF EXISTS `vista_estadisticas_generales`;
/*!50001 DROP VIEW IF EXISTS `vista_estadisticas_generales`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `vista_estadisticas_generales` AS SELECT
 1 AS `total_equipos`,
  1 AS `equipos_en_taller`,
  1 AS `equipos_en_papelera`,
  1 AS `movimientos_anio_actual`,
  1 AS `total_vehiculos` */;
SET character_set_client = @saved_cs_client;
DROP TABLE IF EXISTS `vista_ingreso_taller`;
/*!50001 DROP VIEW IF EXISTS `vista_ingreso_taller`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `vista_ingreso_taller` AS SELECT
 1 AS `id_ingreso`,
  1 AS `id_recepcion`,
  1 AS `id_equipo`,
  1 AS `taller`,
  1 AS `sd`,
  1 AS `equipo`,
  1 AS `antena`,
  1 AS `cargador`,
  1 AS `bateria`,
  1 AS `fuente`,
  1 AS `cables`,
  1 AS `otros` */;
SET character_set_client = @saved_cs_client;
DROP TABLE IF EXISTS `vista_movimientos`;
/*!50001 DROP VIEW IF EXISTS `vista_movimientos`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `vista_movimientos` AS SELECT
 1 AS `origen`,
  1 AS `fecha`,
  1 AS `usuario`,
  1 AS `tipo_accion`,
  1 AS `identificador`,
  1 AS `tipo`,
  1 AS `marca`,
  1 AS `modelo_equipo`,
  1 AS `detalle`,
  1 AS `estado_anterior`,
  1 AS `estado_nuevo`,
  1 AS `observaciones` */;
SET character_set_client = @saved_cs_client;
DROP TABLE IF EXISTS `vista_papelera_unificada`;
/*!50001 DROP VIEW IF EXISTS `vista_papelera_unificada`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `vista_papelera_unificada` AS SELECT
 1 AS `origen`,
  1 AS `id_referencia`,
  1 AS `identificador`,
  1 AS `tipo`,
  1 AS `marca`,
  1 AS `modelo_equipo`,
  1 AS `escala`,
  1 AS `sector`,
  1 AS `fecha_eliminacion` */;
SET character_set_client = @saved_cs_client;
DROP TABLE IF EXISTS `vista_taller`;
/*!50001 DROP VIEW IF EXISTS `vista_taller`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `vista_taller` AS SELECT
 1 AS `tipo`,
  1 AS `marca`,
  1 AS `modelo_equipo`,
  1 AS `serie`,
  1 AS `taller`,
  1 AS `fecha_recepcion`,
  1 AS `fecha_ingreso`,
  1 AS `dias`,
  1 AS `estado_taller`,
  1 AS `observaciones` */;
SET character_set_client = @saved_cs_client;
DROP TABLE IF EXISTS `vista_taller_v2`;
/*!50001 DROP VIEW IF EXISTS `vista_taller_v2`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `vista_taller_v2` AS SELECT
 1 AS `tipo`,
  1 AS `marca`,
  1 AS `modelo_equipo`,
  1 AS `serie`,
  1 AS `taller`,
  1 AS `fecha_recepcion`,
  1 AS `fecha_ingreso`,
  1 AS `dias`,
  1 AS `estado_taller`,
  1 AS `observaciones`,
  1 AS `id_equipo`,
  1 AS `escala`,
  1 AS `sector`,
  1 AS `id_recepcion`,
  1 AS `id_ingreso`,
  1 AS `id`,
  1 AS `id_taller` */;
SET character_set_client = @saved_cs_client;
DROP TABLE IF EXISTS `vista_usuarios`;
/*!50001 DROP VIEW IF EXISTS `vista_usuarios`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `vista_usuarios` AS SELECT
 1 AS `id_usuario`,
  1 AS `legajo`,
  1 AS `username`,
  1 AS `nombre`,
  1 AS `apellido`,
  1 AS `email`,
  1 AS `es_administrador`,
  1 AS `activo`,
  1 AS `debe_cambiar_clave`,
  1 AS `fecha_ultima_conexion` */;
SET character_set_client = @saved_cs_client;
DROP TABLE IF EXISTS `vista_vehiculos_v5`;
/*!50001 DROP VIEW IF EXISTS `vista_vehiculos_v5`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `vista_vehiculos_v5` AS SELECT
 1 AS `id_vehiculo`,
  1 AS `tipo_vehiculo`,
  1 AS `identificacion`,
  1 AS `escala`,
  1 AS `modelo_equipo`,
  1 AS `numero_serie`,
  1 AS `fecha_modificacion` */;
SET character_set_client = @saved_cs_client;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_AUTO_VALUE_ON_ZERO' */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_egreso_cambio_estado` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_egreso_cambio_estado`(IN `p_id_equipo` INT, IN `p_usuario` INT, IN `p_id_estado` INT)
BEGIN
	UPDATE equipos
    SET en_taller = FALSE,
    	estado = 'REPARADO',
        usuario_modificacion = @usuario_actual
    WHERE id_equipo = p_id_equipo;
    
    UPDATE equipo_estado
    SET id_estado = 6
    WHERE id = p_id_estado AND id_equipo = p_id_equipo;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_AUTO_VALUE_ON_ZERO' */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_enviar_a_papelera` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_enviar_a_papelera`(IN `p_id_equipo` INT, IN `p_usuario` INT, IN `p_motivo` TEXT, IN `p_numero_serie` VARCHAR(100))
BEGIN
    UPDATE equipos 
    SET en_papelera = TRUE,
        usuario_modificacion = p_usuario
    WHERE id_equipo = p_id_equipo;
    
    INSERT INTO papelera (id_equipo, usuario_eliminacion, motivo_eliminacion, numero_serie)
    VALUES (p_id_equipo, p_usuario, p_motivo, p_numero_serie);
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_AUTO_VALUE_ON_ZERO' */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_enviar_equipo_taller_v3` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_enviar_equipo_taller_v3`(IN `p_id_equipo` INT, IN `p_id_estado` INT, IN `p_usuario` INT)
BEGIN
    UPDATE equipos 
    SET en_taller = TRUE,
        usuario_modificacion = p_usuario
    WHERE id_equipo = p_id_equipo;
    
    INSERT INTO taller_ingresos (id_equipo, taller, ingreso_de_inventario)
    VALUES (p_id_equipo, p_id_estado, p_usuario);
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_AUTO_VALUE_ON_ZERO' */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_enviar_equipo_taller_v4` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_enviar_equipo_taller_v4`(IN `p_id_equipo` INT, IN `p_id_taller` INT, IN `p_usuario` INT, IN `p_observacion` TEXT)
BEGIN
    UPDATE equipos 
    SET en_taller = TRUE,
        usuario_modificacion = p_usuario
    WHERE id_equipo = p_id_equipo;
    
    INSERT INTO taller_recepcion (id_equipo, id_taller, usuario_modificacion)
    VALUES (p_id_equipo, p_id_taller, p_usuario);
    
    INSERT INTO observaciones_equipos (id_equipo, usuario_observacion, texto_observacion)
    VALUES (p_id_equipo, p_usuario, p_observacion);
    
    INSERT INTO observaciones_taller (id_equipo, usuario_observacion, observacion)
    VALUES (p_id_equipo, p_usuario, p_observacion);
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_AUTO_VALUE_ON_ZERO' */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_enviar_vehiculo_papelera` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_enviar_vehiculo_papelera`(IN `p_id_vehiculo` INT, IN `p_usuario` INT, IN `p_motivo` TEXT, IN `p_identificacion` VARCHAR(100))
BEGIN
    UPDATE vehiculos 
    SET de_baja = TRUE,
        usuario_modificacion = p_usuario
    WHERE id_vehiculo = p_id_vehiculo;
    
    INSERT INTO papelera_vehiculos (id_vehiculo, usuario_eliminacion, motivo_eliminacion, identificacion)
    VALUES (p_id_vehiculo, p_usuario, p_motivo, p_identificacion);
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_AUTO_VALUE_ON_ZERO' */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_estadisticas_por_escala` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_estadisticas_por_escala`()
BEGIN
    SELECT 
        escala,
        COUNT(*) AS cantidad,
        SUM(CASE WHEN estado LIKE '%Reparación%' THEN 1 ELSE 0 END) AS en_taller,
        SUM(CASE WHEN estado = 'Operativo' THEN 1 ELSE 0 END) AS operativos,
        SUM(CASE WHEN estado = 'En Stock' THEN 1 ELSE 0 END) AS en_stock
    FROM equipos
    WHERE en_papelera = FALSE
    GROUP BY escala
    ORDER BY cantidad DESC;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_AUTO_VALUE_ON_ZERO' */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_ingresar_taller` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_ingresar_taller`(IN `p_id_equipo_estado` INT)
BEGIN
    UPDATE equipo_estado
    SET id_estado = 3
    WHERE id = p_id_equipo_estado
    AND id_estado = 7;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_AUTO_VALUE_ON_ZERO' */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_obtener_historial_equipo` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_obtener_historial_equipo`(IN `p_id_equipo` INT)
BEGIN
    SELECT 
        h.fecha_evento,
        u.legajo AS usuario,
        h.tipo_evento,
        h.campo_modificado,
        h.valor_anterior,
        h.valor_nuevo,
        h.observaciones
    FROM historial_equipos h
    LEFT JOIN usuarios u ON h.usuario_evento = u.id_usuario
    WHERE h.id_equipo = p_id_equipo
    ORDER BY h.fecha_evento DESC;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_AUTO_VALUE_ON_ZERO' */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_restaurar_equipo_papelera` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_restaurar_equipo_papelera`(IN `p_id_equipo` INT, IN `p_usuario` INT)
BEGIN
    UPDATE equipos 
    SET en_papelera = FALSE,
        usuario_modificacion = p_usuario
    WHERE id_equipo = p_id_equipo;
    
    UPDATE papelera
    SET puede_restaurar = FALSE
    WHERE id_equipo = p_id_equipo;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_AUTO_VALUE_ON_ZERO' */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_restaurar_vehiculo_papelera` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_restaurar_vehiculo_papelera`(IN `p_id_vehiculo` INT, IN `p_usuario` INT)
BEGIN
    UPDATE vehiculos 
    SET de_baja = FALSE,
        usuario_modificacion = p_usuario
    WHERE id_vehiculo = p_id_vehiculo;
    
    UPDATE papelera_vehiculos
    SET puede_restaurar = FALSE
    WHERE id_vehiculo = p_id_vehiculo;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50001 DROP VIEW IF EXISTS `vista_equipo_etiqueta`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vista_equipo_etiqueta` AS select `t`.`tipo` AS `tipo`,`ma`.`marca` AS `marca`,`m`.`modelo_equipo` AS `modelo_equipo`,`e`.`numero_serie` AS `numero_serie`,`es`.`escala` AS `escala`,`e`.`sector` AS `sector`,`e`.`estado` AS `estado`,`u`.`nombre` AS `usuario_modificacion` from (((((`equipos` `e` left join `usuarios` `u` on(`e`.`usuario_modificacion` = `u`.`id_usuario`)) left join `modelos` `m` on(`e`.`modelo` = `m`.`id_modelo`)) left join `marcas` `ma` on(`m`.`marca` = `ma`.`id_marca`)) left join `escalas` `es` on(`e`.`escala` = `es`.`id_escala`)) left join `tipos` `t` on(`e`.`tipo` = `t`.`id_tipo`)) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!50001 DROP VIEW IF EXISTS `vista_equipos_papelera`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vista_equipos_papelera` AS select `e`.`id_equipo` AS `id_equipo`,`e`.`numero_serie` AS `numero_serie`,`t`.`tipo` AS `tipo`,`ma`.`marca` AS `marca`,`m`.`modelo_equipo` AS `modelo_equipo`,`es`.`escala` AS `escala`,`e`.`sector` AS `sector`,`p`.`fecha_eliminacion` AS `fecha_eliminacion` from (((((`equipos` `e` left join `tipos` `t` on(`e`.`tipo` = `t`.`id_tipo`)) left join `modelos` `m` on(`e`.`modelo` = `m`.`id_modelo`)) left join `marcas` `ma` on(`m`.`marca` = `ma`.`id_marca`)) left join `escalas` `es` on(`e`.`escala` = `es`.`id_escala`)) left join `papelera` `p` on(`e`.`id_equipo` = `p`.`id_equipo`)) where `e`.`en_papelera` = 1 */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!50001 DROP VIEW IF EXISTS `vista_equipos_taller`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vista_equipos_taller` AS select `e`.`numero_serie` AS `numero_serie`,`e`.`tipo` AS `tipo`,`e`.`marca` AS `marca`,`e`.`modelo` AS `modelo`,`e`.`escala` AS `escala`,`e`.`sector` AS `sector`,`e`.`estado` AS `estado`,`ti`.`taller` AS `taller`,`ti`.`fecha_ingreso` AS `fecha_ingreso`,`ti`.`numero_ticket_sd` AS `numero_ticket_sd`,`ti`.`egresado` AS `egresado`,`u`.`legajo` AS `usuario_ingreso` from ((((((`taller_ingresos` `ti` join `equipos` `e` on(`ti`.`id_equipo` = `e`.`id_equipo`)) left join `usuarios` `u` on(`ti`.`usuario_ingreso` = `u`.`id_usuario`)) left join `modelos` `m` on(`e`.`modelo` = `m`.`id_modelo`)) left join `marcas` `ma` on(`m`.`marca` = `ma`.`id_marca`)) left join `escalas` `es` on(`e`.`escala` = `es`.`id_escala`)) left join `tipos` `t` on(`e`.`tipo` = `t`.`id_tipo`)) where `ti`.`egresado` = 0 order by `ti`.`fecha_ingreso` desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!50001 DROP VIEW IF EXISTS `vista_equipos_v3`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vista_equipos_v3` AS select `e`.`id_equipo` AS `id_equipo`,`e`.`numero_serie` AS `numero_serie`,`t`.`tipo` AS `tipo`,`ma`.`marca` AS `marca`,`m`.`modelo_equipo` AS `modelo_equipo`,`es`.`escala` AS `escala`,`e`.`sector` AS `sector`,`e`.`estado` AS `estado`,`e`.`valor_potencia` AS `valor_potencia`,`e`.`nombre_plantilla` AS `nombre_plantilla`,`e`.`ult_observacion` AS `ult_observacion`,`e`.`en_papelera` AS `en_papelera`,`e`.`en_taller` AS `en_taller`,`e`.`fecha_ingreso` AS `fecha_ingreso`,`e`.`fecha_modificacion` AS `fecha_modificacion`,`u_creacion`.`legajo` AS `usuario_creacion`,`u_modificacion`.`legajo` AS `usuario_modificacion`,`pc`.`cantidad_canales` AS `cantidad_canales`,`v`.`identificacion` AS `vehiculo_asignado` from ((((((((`equipos` `e` left join `usuarios` `u_creacion` on(`e`.`usuario_creacion` = `u_creacion`.`id_usuario`)) left join `usuarios` `u_modificacion` on(`e`.`usuario_modificacion` = `u_modificacion`.`id_usuario`)) left join `programacion_canales` `pc` on(`e`.`id_equipo` = `pc`.`id_equipo`)) left join `vehiculos` `v` on(`e`.`id_equipo` = `v`.`radio_asignado`)) left join `modelos` `m` on(`e`.`modelo` = `m`.`id_modelo`)) left join `marcas` `ma` on(`m`.`marca` = `ma`.`id_marca`)) left join `escalas` `es` on(`e`.`escala` = `es`.`id_escala`)) left join `tipos` `t` on(`e`.`tipo` = `t`.`id_tipo`)) where `e`.`en_papelera` = 0 and `e`.`en_taller` = 0 */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!50001 DROP VIEW IF EXISTS `vista_equipos_v4`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vista_equipos_v4` AS select `e`.`id_equipo` AS `id_equipo`,`e`.`numero_serie` AS `numero_serie`,`t`.`tipo` AS `tipo`,`ma`.`marca` AS `marca`,`m`.`modelo_equipo` AS `modelo_equipo`,`es`.`escala` AS `escala`,`e`.`sector` AS `sector`,`e`.`estado` AS `estado`,`m`.`potencia` AS `potencia`,`pc`.`nombre_plantilla` AS `nombre_plantilla`,`e`.`ult_observacion` AS `ult_observacion`,`e`.`en_papelera` AS `en_papelera`,`e`.`en_taller` AS `en_taller`,`e`.`fecha_ingreso` AS `fecha_ingreso`,`e`.`fecha_modificacion` AS `fecha_modificacion`,`u_creacion`.`legajo` AS `usuario_creacion`,`u_modificacion`.`legajo` AS `usuario_modificacion`,`pc`.`cantidad_canales` AS `cantidad_canales`,`v`.`identificacion` AS `vehiculo_asignado` from ((((((((`equipos` `e` left join `usuarios` `u_creacion` on(`e`.`usuario_creacion` = `u_creacion`.`id_usuario`)) left join `usuarios` `u_modificacion` on(`e`.`usuario_modificacion` = `u_modificacion`.`id_usuario`)) left join `programacion_canales` `pc` on(`e`.`id_equipo` = `pc`.`id_equipo`)) left join `vehiculos` `v` on(`e`.`id_equipo` = `v`.`radio_asignado`)) left join `modelos` `m` on(`e`.`modelo` = `m`.`id_modelo`)) left join `marcas` `ma` on(`m`.`marca` = `ma`.`id_marca`)) left join `escalas` `es` on(`e`.`escala` = `es`.`id_escala`)) left join `tipos` `t` on(`e`.`tipo` = `t`.`id_tipo`)) where `e`.`en_papelera` = 0 and `e`.`en_taller` = 0 */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!50001 DROP VIEW IF EXISTS `vista_estadisticas_generales`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vista_estadisticas_generales` AS select (select count(0) from `equipos` where `equipos`.`en_papelera` = 0) AS `total_equipos`,(select count(0) from `equipos` where `equipos`.`estado` like '%Reparación%') AS `equipos_en_taller`,(select count(0) from `equipos` where `equipos`.`en_papelera` = 1) AS `equipos_en_papelera`,(select count(0) from `historial_equipos` where year(`historial_equipos`.`fecha_evento`) = year(curdate())) AS `movimientos_anio_actual`,(select count(0) from `vehiculos`) AS `total_vehiculos` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!50001 DROP VIEW IF EXISTS `vista_ingreso_taller`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vista_ingreso_taller` AS select `tai`.`id_ingreso` AS `id_ingreso`,`tai`.`id_recepcion` AS `id_recepcion`,`tai`.`id_equipo` AS `id_equipo`,`ta`.`taller` AS `taller`,coalesce(`tai`.`numero_ticket_sd`,'No informado') AS `sd`,`tai`.`componente_equipo` AS `equipo`,`tai`.`componente_antena` AS `antena`,`tai`.`componente_cargador` AS `cargador`,`tai`.`componente_bateria` AS `bateria`,`tai`.`componente_fuente` AS `fuente`,`tai`.`componente_cables` AS `cables`,coalesce((select `tai`.`detalle_otros_componentes` from DUAL  where `tai`.`componente_otros` = 1),'Sin detalle') AS `otros` from ((`taller_ingresos` `tai` left join `equipos` `e` on(`e`.`id_equipo` = `tai`.`id_equipo`)) left join `talleres` `ta` on(`ta`.`id_taller` = `tai`.`taller`)) where `tai`.`egresado` = 0 */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!50001 DROP VIEW IF EXISTS `vista_movimientos`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vista_movimientos` AS select 'equipo' AS `origen`,`he`.`fecha_evento` AS `fecha`,`u`.`username` AS `usuario`,`he`.`tipo_evento` AS `tipo_accion`,`e`.`numero_serie` AS `identificador`,`t`.`tipo` AS `tipo`,`ma`.`marca` AS `marca`,`m`.`modelo_equipo` AS `modelo_equipo`,'' AS `detalle`,`he`.`valor_anterior` AS `estado_anterior`,`he`.`valor_nuevo` AS `estado_nuevo`,`he`.`observaciones` AS `observaciones` from (((((`historial_equipos` `he` left join `equipos` `e` on(`e`.`id_equipo` = `he`.`id_equipo`)) left join `usuarios` `u` on(`u`.`id_usuario` = `he`.`usuario_evento`)) left join `tipos` `t` on(`t`.`id_tipo` = `e`.`tipo`)) left join `marcas` `ma` on(`ma`.`id_marca` = `e`.`marca`)) left join `modelos` `m` on(`m`.`id_modelo` = `e`.`modelo`)) union all select 'interno' AS `origen`,`hv`.`fecha_evento` AS `fecha`,`u`.`username` AS `usuario`,`hv`.`tipo_evento` AS `tipo_accion`,`v`.`identificacion` AS `identificador`,`v`.`tipo_vehiculo` AS `tipo`,'' AS `marca`,'' AS `modelo_equipo`,'' AS `detalle`,`hv`.`valor_anterior` AS `estado_anterior`,`hv`.`valor_nuevo` AS `estado_nuevo`,`hv`.`observaciones` AS `observaciones` from ((`historial_vehiculos` `hv` left join `vehiculos` `v` on(`v`.`id_vehiculo` = `hv`.`id_vehiculo`)) left join `usuarios` `u` on(`u`.`id_usuario` = `hv`.`usuario_evento`)) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!50001 DROP VIEW IF EXISTS `vista_papelera_unificada`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vista_papelera_unificada` AS select 'equipo' AS `origen`,`e`.`id_equipo` AS `id_referencia`,`e`.`numero_serie` AS `identificador`,`t`.`tipo` AS `tipo`,`ma`.`marca` AS `marca`,`m`.`modelo_equipo` AS `modelo_equipo`,`es`.`escala` AS `escala`,`e`.`sector` AS `sector`,`p`.`fecha_eliminacion` AS `fecha_eliminacion` from (((((`equipos` `e` left join `tipos` `t` on(`t`.`id_tipo` = `e`.`tipo`)) left join `modelos` `m` on(`m`.`id_modelo` = `e`.`modelo`)) left join `marcas` `ma` on(`ma`.`id_marca` = `m`.`marca`)) left join `escalas` `es` on(`es`.`id_escala` = `e`.`escala`)) left join `papelera` `p` on(`p`.`id_equipo` = `e`.`id_equipo`)) where `e`.`en_papelera` = 1 union all select 'vehiculo' AS `origen`,`v`.`id_vehiculo` AS `id_referencia`,`v`.`identificacion` AS `identificador`,`v`.`tipo_vehiculo` AS `tipo`,'' AS `marca`,'' AS `modelo_equipo`,`es`.`escala` AS `escala`,'' AS `sector`,`pv`.`fecha_eliminacion` AS `fecha_eliminacion` from ((`vehiculos` `v` left join `escalas` `es` on(`es`.`id_escala` = `v`.`escala`)) left join `papelera_vehiculos` `pv` on(`v`.`id_vehiculo` = `pv`.`id_vehiculo`)) where `v`.`de_baja` = 1 */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!50001 DROP VIEW IF EXISTS `vista_taller`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vista_taller` AS select straight_join `t`.`tipo` AS `tipo`,`ma`.`marca` AS `marca`,`m`.`modelo_equipo` AS `modelo_equipo`,`e`.`numero_serie` AS `serie`,`tal`.`taller` AS `taller`,`tar`.`fecha_recepcion` AS `fecha_recepcion`,`tai`.`fecha_ingreso` AS `fecha_ingreso`,to_days(coalesce(`tae`.`fecha_egreso`,curdate())) - to_days(`tar`.`fecha_recepcion`) AS `dias`,`est`.`estado` AS `estado_taller`,`obs`.`observacion` AS `observaciones` from ((((((((((`equipos` `e` left join `tipos` `t` on(`t`.`id_tipo` = `e`.`tipo`)) left join `marcas` `ma` on(`ma`.`id_marca` = `e`.`marca`)) left join `modelos` `m` on(`m`.`id_modelo` = `e`.`modelo`)) left join `taller_recepcion` `tar` on(`tar`.`id_equipo` = `e`.`id_equipo` and `tar`.`id_recepcion` = (select max(`taller_recepcion`.`id_recepcion`) from `taller_recepcion` where `taller_recepcion`.`id_equipo` = `e`.`id_equipo`))) left join `talleres` `tal` on(`tal`.`id_taller` = `tar`.`id_taller`)) left join `taller_ingresos` `tai` on(`tai`.`id_equipo` = `e`.`id_equipo` and `tai`.`id_ingreso` = (select max(`taller_ingresos`.`id_ingreso`) from `taller_ingresos` where `taller_ingresos`.`id_equipo` = `e`.`id_equipo`))) left join `equipo_estado` `esta` on(`esta`.`id_equipo` = `e`.`id_equipo` and `esta`.`id` = (select max(`equipo_estado`.`id`) from `equipo_estado` where `equipo_estado`.`id_equipo` = `e`.`id_equipo`))) left join `estados_taller` `est` on(`est`.`id_estado` = `esta`.`id_estado`)) left join `observaciones_taller` `obs` on(`obs`.`id_equipo` = `e`.`id_equipo` and `obs`.`id` = (select max(`observaciones_taller`.`id`) from `observaciones_taller` where `observaciones_taller`.`id_equipo` = `e`.`id_equipo`))) left join `taller_egresos` `tae` on(`tae`.`id_ingreso` = `tai`.`id_ingreso`)) where `e`.`en_taller` = 1 */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!50001 DROP VIEW IF EXISTS `vista_taller_v2`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vista_taller_v2` AS select straight_join `t`.`tipo` AS `tipo`,`ma`.`marca` AS `marca`,`m`.`modelo_equipo` AS `modelo_equipo`,`e`.`numero_serie` AS `serie`,`tal`.`taller` AS `taller`,`tar`.`fecha_recepcion` AS `fecha_recepcion`,`tai`.`fecha_ingreso` AS `fecha_ingreso`,to_days(coalesce(`tae`.`fecha_egreso`,curdate())) - to_days(`tar`.`fecha_recepcion`) AS `dias`,`est`.`estado` AS `estado_taller`,`obs`.`observacion` AS `observaciones`,`e`.`id_equipo` AS `id_equipo`,`es`.`escala` AS `escala`,`e`.`sector` AS `sector`,`tar`.`id_recepcion` AS `id_recepcion`,`tai`.`id_ingreso` AS `id_ingreso`,`esta`.`id` AS `id`,`tal`.`id_taller` AS `id_taller` from (((((((((((`equipos` `e` left join `tipos` `t` on(`t`.`id_tipo` = `e`.`tipo`)) left join `marcas` `ma` on(`ma`.`id_marca` = `e`.`marca`)) left join `modelos` `m` on(`m`.`id_modelo` = `e`.`modelo`)) left join `taller_recepcion` `tar` on(`tar`.`id_equipo` = `e`.`id_equipo` and `tar`.`id_recepcion` = (select max(`tr`.`id_recepcion`) from `taller_recepcion` `tr` where `tr`.`id_equipo` = `e`.`id_equipo`))) left join `talleres` `tal` on(`tal`.`id_taller` = `tar`.`id_taller`)) left join `taller_ingresos` `tai` on(`tai`.`id_equipo` = `e`.`id_equipo` and `tai`.`id_ingreso` = (select max(`ti`.`id_ingreso`) from `taller_ingresos` `ti` where `ti`.`id_equipo` = `e`.`id_equipo` and `ti`.`fecha_ingreso` >= `tar`.`fecha_recepcion`))) left join `taller_egresos` `tae` on(`tae`.`id_ingreso` = `tai`.`id_ingreso`)) left join `equipo_estado` `esta` on(`esta`.`id_equipo` = `e`.`id_equipo` and `esta`.`id` = (select max(`ee`.`id`) from `equipo_estado` `ee` where `ee`.`id_equipo` = `e`.`id_equipo`))) left join `estados_taller` `est` on(`est`.`id_estado` = `esta`.`id_estado`)) left join `observaciones_taller` `obs` on(`obs`.`id_equipo` = `e`.`id_equipo` and `obs`.`id` = (select max(`ot`.`id`) from `observaciones_taller` `ot` where `ot`.`id_equipo` = `e`.`id_equipo`))) left join `escalas` `es` on(`es`.`id_escala` = `e`.`escala`)) where `e`.`en_taller` = 1 */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!50001 DROP VIEW IF EXISTS `vista_usuarios`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vista_usuarios` AS select `usuarios`.`id_usuario` AS `id_usuario`,`usuarios`.`legajo` AS `legajo`,`usuarios`.`username` AS `username`,`usuarios`.`nombre` AS `nombre`,`usuarios`.`apellido` AS `apellido`,`usuarios`.`email` AS `email`,`usuarios`.`es_administrador` AS `es_administrador`,`usuarios`.`activo` AS `activo`,`usuarios`.`debe_cambiar_clave` AS `debe_cambiar_clave`,`usuarios`.`fecha_ultima_conexion` AS `fecha_ultima_conexion` from `usuarios` order by `usuarios`.`id_usuario` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!50001 DROP VIEW IF EXISTS `vista_vehiculos_v5`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vista_vehiculos_v5` AS select `v`.`id_vehiculo` AS `id_vehiculo`,`v`.`tipo_vehiculo` AS `tipo_vehiculo`,`v`.`identificacion` AS `identificacion`,`es`.`escala` AS `escala`,`m`.`modelo_equipo` AS `modelo_equipo`,`e`.`numero_serie` AS `numero_serie`,`v`.`fecha_modificacion` AS `fecha_modificacion` from (((`vehiculos` `v` left join `escalas` `es` on(`es`.`id_escala` = `v`.`escala`)) left join `equipos` `e` on(`e`.`id_equipo` = `v`.`radio_asignado`)) left join `modelos` `m` on(`m`.`id_modelo` = `e`.`modelo`)) where `v`.`de_baja` = 0 */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

