<?php
require_once 'auth.php';    // reemplaza a conexion.php, ya lo incluye adentro
$user = requireAuth();

try {
    $modelo_equipo = $_GET['imagen_modelo'] ?? '';

    if (!$modelo_equipo) {
        sendError("No se recibieron datos", 400);
        exit;
    }
    
    $pdo = getConnection();

    $sql = "SELECT imagen_modelo FROM modelos WHERE modelo_equipo = :modelo_equipo LIMIT 1";
    $stmt = $pdo->prepare($sql);
    $stmt->bindParam(":modelo_equipo", $modelo_equipo);
    $stmt->execute();

    $ruta_imagen = $stmt->fetchColumn();

    if ($ruta_imagen) {
        sendSuccess($ruta_imagen) ;
    } else {
        sendError("No se encontró la imagen") ;
    }

} catch(PDOException $e) {
    sendError(API_DEBUG ? $e->getMessage() : "Error al obtener la imagen");
}
?>