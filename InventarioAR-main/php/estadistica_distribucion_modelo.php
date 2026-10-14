<?php
require_once 'auth.php';
$user = requireAuth();

try {
    $pdo = getConnection();
    $sql = "SELECT m.modelo_equipo AS etiqueta, COUNT(e.id_equipo) AS cantidad
        FROM equipos e
        JOIN modelos m ON m.id_modelo = e.modelo
        WHERE e.en_papelera = 0
        GROUP BY m.modelo_equipo
        ORDER BY cantidad DESC";
    echo json_encode($pdo->query($sql)->fetchAll(PDO::FETCH_ASSOC), JSON_UNESCAPED_UNICODE);
} catch (Throwable $e) {
    sendError("Error al obtener distribución por tipo", 500);
}