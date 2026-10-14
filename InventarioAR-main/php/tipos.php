<?php
require_once 'auth.php';    // reemplaza a conexion.php, ya lo incluye adentro
$user = requireAuth(); 

try {
    $pdo = getConnection();
    
    $sql = "SELECT id_tipo, tipo FROM tipos ORDER BY tipo ASC";
    $stmt = $pdo->query($sql);
    $tipos = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    echo json_encode($tipos);
    
} catch(PDOException $e) {
    sendError(API_DEBUG ? $e->getMessage() : "Error al obtener tipos");
}
?>