<?php
require_once 'auth.php';    // reemplaza a conexion.php, ya lo incluye adentro
$user = requireAuth(); 

try {
    $pdo = getConnection();
    
    $sql = "SELECT DISTINCT potencia FROM modelos 
            WHERE potencia != '' AND potencia IS NOT NULL
            ORDER BY potencia ASC";
    $stmt = $pdo->query($sql);
    $potencias = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    echo json_encode($potencias);
    
} catch(PDOException $e) {
    sendError(API_DEBUG ? $e->getMessage() : "Error al obtener potencias");
}
?>