<?php
require_once 'auth.php';    // reemplaza a conexion.php, ya lo incluye adentro
$user = requireAuth(); 

try {
    $pdo = getConnection();
    
    $sql = "SELECT DISTINCT tipo_vehiculo FROM vehiculos GROUP BY tipo_vehiculo";
    $stmt = $pdo->query($sql);
    $vehiculos = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    echo json_encode($vehiculos);
    
} catch(PDOException $e) {
    sendError(API_DEBUG ? $e->getMessage() : "Error al obtener tipos vehiculos");
}
?>