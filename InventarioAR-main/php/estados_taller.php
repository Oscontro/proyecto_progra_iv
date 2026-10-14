<?php
require_once 'auth.php';    // reemplaza a conexion.php, ya lo incluye adentro
$user = requireAuth(); 

try {
    $pdo = getConnection();
    
    $sql = "SELECT id_estado, estado FROM estados_taller ORDER BY id_estado ASC LIMIT 4";
    $stmt = $pdo->query($sql);
    $talleres = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    echo json_encode($talleres);
    
} catch(PDOException $e) {
    sendError(API_DEBUG ? $e->getMessage() : "Error al obtener talleres");
}
?>