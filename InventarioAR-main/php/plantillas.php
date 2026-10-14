<?php
require_once 'auth.php';    // reemplaza a conexion.php, ya lo incluye adentro
$user = requireAuth(); 

try {
    $pdo = getConnection();
    
    $sql = "SELECT DISTINCT nombre_plantilla FROM programacion_canales WHERE nombre_plantilla IS NOT NULL ORDER BY nombre_plantilla ASC";
    $stmt = $pdo->query($sql);
    $nombre_config = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    echo json_encode($nombre_config);
    
} catch(PDOException $e) {
    sendError(API_DEBUG ? $e->getMessage() : "Error al obtener nombres de plantillas");
}
?>