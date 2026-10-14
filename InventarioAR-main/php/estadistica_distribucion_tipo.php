<?php
require_once 'auth.php';
$user = requireAuth();

try {
    $pdo = getConnection();
    $sql = "SELECT t.tipo AS etiqueta, COUNT(e.id_equipo) AS cantidad
            FROM equipos e
            JOIN tipos t ON t.id_tipo = e.tipo
            WHERE e.en_papelera = 0
            GROUP BY t.tipo
            ORDER BY cantidad DESC";
    echo json_encode($pdo->query($sql)->fetchAll(PDO::FETCH_ASSOC), JSON_UNESCAPED_UNICODE);
} catch (Throwable $e) {
    sendError("Error al obtener distribución por tipo", 500);
}