<?php
require_once 'auth.php';    // reemplaza a conexion.php, ya lo incluye adentro
$user = requireAuth(); 

try {
    
    $sql = "SELECT 
                id_vehiculo,
                tipo_vehiculo as tipo,
                identificacion,
                escala,
                COALESCE(modelo_equipo, 'Sin radio asignada') AS radio_modelo,
                COALESCE(numero_serie, '') AS radio_serie
            FROM vista_vehiculos_v5
            ORDER BY fecha_modificacion DESC";

    $pdo = getConnection();
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);

            
    $stmt = $pdo->prepare($sql);
    $stmt->execute(); 

    $vehiculos = $stmt->fetchAll(); 
    
    // Devolvemos el array puro para que el Front-end lo procese
    echo json_encode($vehiculos, JSON_UNESCAPED_UNICODE);
    
} catch(PDOException $e) {
    http_response_code(500);
    sendError(API_DEBUG ? $e->getMessage() : "Error al obtener internos");
}
?>