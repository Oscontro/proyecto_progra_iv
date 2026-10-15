<?php
require_once 'auth.php';    // reemplaza a conexion.php, ya lo incluye adentro
$user = requireAuth(); 

try {
    $pdo = getConnection();
    
    $sql = "SELECT DISTINCT 
                m.modelo_equipo
            FROM modelos m
            LEFT JOIN equipos e ON m.id_modelo = e.modelo
            WHERE e.tipo = 2
            ORDER BY m.modelo_equipo ASC";
    
    $stmt = $pdo->prepare($sql);
    $stmt->execute();
    $modelos = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    header('Content-Type: application/json');
    echo json_encode($modelos);
    
} catch(PDOException $e) {
    header('Content-Type: application/json');
    echo json_encode([]);
}
?>