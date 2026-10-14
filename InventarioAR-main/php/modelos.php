<?php
require_once 'auth.php';    // reemplaza a conexion.php, ya lo incluye adentro
$user = requireAuth(); 

try {
    $pdo = getConnection();
    
    $id_marca = isset($_GET['id_marca']) ? intval($_GET['id_marca']) : 0;
    $id_tipo = isset($_GET['id_tipo']) ? intval($_GET['id_tipo']) : 0;

    if ($id_marca <= 0 || $id_tipo <=0) {
        echo json_encode([]);
        exit;
    }
    
    $sql = "SELECT DISTINCT modelo_equipo FROM modelos
            WHERE marca = ? AND tipo = ?
            ORDER BY modelo_equipo ASC";
    
    $stmt = $pdo->prepare($sql);
    $stmt->execute([$id_marca, $id_tipo]);
    $modelos = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    header('Content-Type: application/json');
    echo json_encode($modelos);
    
} catch(PDOException $e) {
    sendError(API_DEBUG ? $e->getMessage() : "Error al obtener tipos y marcas");
}
?>