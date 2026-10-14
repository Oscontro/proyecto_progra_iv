<?php
require_once 'auth.php';    // reemplaza a conexion.php, ya lo incluye adentro
$user = requireAuth(); 

try {
    $pdo = getConnection();
    
    $sql = "SELECT escala FROM escalas ORDER BY escala ASC";
    $stmt = $pdo->query($sql);
    $escalas = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    echo json_encode($escalas);
    
} catch(PDOException $e) {
    sendError(API_DEBUG ? $e->getMessage() : "Error al obtener escalas");
}
?>