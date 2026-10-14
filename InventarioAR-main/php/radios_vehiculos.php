<?php
require_once 'auth.php';

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

try {

    $sql = "SELECT
                id_equipo,
                COALESCE(marca, '') as marca,
                COALESCE(modelo_equipo, '') as modelo_equipo,
                COALESCE(numero_serie, '') as numero_serie,
                COALESCE(escala, '') as escala
            FROM vista_equipos_v3
            WHERE tipo = 'Base VHF FM' ";


    
    $pdo = getConnection();
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
    $stmt = $pdo->prepare($sql);
    $stmt->execute(); 

    $radios = $stmt->fetchAll(); 
    
    // Devolvemos el array puro para que el Front-end lo procese
    echo json_encode($radios, JSON_UNESCAPED_UNICODE);
} catch(PDOException $e) {
    $error = date('Y-m-d H:i:s') . " | EXCEPCION | " .  " | " . $e->getMessage();
    file_put_contents($archivo_log, $error . PHP_EOL, FILE_APPEND);
    sendError(API_DEBUG ? $e->getMessage() : "Error al obtener radios");
}