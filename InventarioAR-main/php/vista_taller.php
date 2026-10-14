<?php
require_once 'auth.php';    // reemplaza a conexion.php, ya lo incluye adentro
$user = requireAuth(); 
header('Content-Type: application/json; charset=utf-8');

try {
    $pdo = getConnection();
    // Configuraciones recomendadas para estabilidad y rendimiento
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);

    $sql = "SELECT 
                tipo,
                marca,
                modelo_equipo,
                serie,
                taller,
                fecha_recepcion,
                COALESCE(fecha_ingreso, '-') AS fecha_ingreso,
                dias,
                estado_taller,
                observaciones,
                id_equipo,
                escala,
                sector,
                id_recepcion,
                id_ingreso,
                id AS id_estado,
                id_taller
            FROM vista_taller_v2
            ORDER BY fecha_recepcion ASC";
            
    $stmt = $pdo->prepare($sql);
    $stmt->execute(); 

    $datos = $stmt->fetchAll(); 
    
    // Devolvemos el array puro para que el Front-end lo procese
    echo json_encode($datos, JSON_UNESCAPED_UNICODE);
    
} catch(PDOException $e) {
    http_response_code(500);
    echo json_encode(["error" => "Error en la base de datos: " . $e->getMessage()]);
}
?>