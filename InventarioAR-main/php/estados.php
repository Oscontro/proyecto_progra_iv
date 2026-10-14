<?php
require_once 'auth.php';    // reemplaza a conexion.php, ya lo incluye adentro
$user = requireAuth(); 

try {
    $pdo = getConnection();
    
    $sql = "SELECT DISTINCT estado FROM equipos ORDER BY estado ASC";
    $stmt = $pdo->query($sql);
    $estados = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    echo json_encode($estados);
    
} catch(PDOException $e) {
    sendError(API_DEBUG ? $e->getMessage() : "Error al obtener estados");
}
?>