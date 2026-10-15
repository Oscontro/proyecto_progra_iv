<?php
require_once 'auth.php';    // reemplaza a conexion.php, ya lo incluye adentro
$user = requireAuth(); 

try {
    $pdo = getConnection();
    
    $sql = "SELECT id_modelo, modelo_equipo FROM modelos ORDER BY modelo_equipo ASC";
    $stmt = $pdo->query($sql);
    $modelos = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    echo json_encode($modelos);
    
} catch(PDOException $e) {
    sendError(API_DEBUG ? $e->getMessage() : "Error al obtener modelos");
}
?>