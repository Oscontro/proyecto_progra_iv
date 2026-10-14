<?php
require_once 'auth.php';    // reemplaza a conexion.php, ya lo incluye adentro
$user = requireAuth(); 

try {
    $pdo = getConnection();
    
    $sql = "SELECT DISTINCT sector FROM equipos ORDER BY sector ASC";
    $stmt = $pdo->query($sql);
    $sectores = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    echo json_encode($sectores);
    
} catch(PDOException $e) {
    sendError(API_DEBUG ? $e->getMessage() : "Error al obtener sectores");
}
?>