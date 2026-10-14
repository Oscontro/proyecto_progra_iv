<?php
require_once 'auth.php'; 
$user = requireAuth(); 

try {
    $pdo = getConnection();
    
    $sql = "SELECT id_taller, taller FROM talleres ORDER BY id_taller ASC";
    $stmt = $pdo->query($sql);
    $talleres = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    echo json_encode($talleres);
    
} catch(PDOException $e) {
    sendError(API_DEBUG ? $e->getMessage() : "Error al obtener talleres");
}
?>