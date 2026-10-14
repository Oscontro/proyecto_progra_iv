<?php
require_once 'auth.php';
$user = requireAuth();

try {
    $pdo = getConnection();

    // Cuenta equipos por tipo. Ajustá los nombres a tu esquema.
    $sql = "SELECT t.tipo AS etiqueta, COUNT(e.id_equipo) AS cantidad
            FROM equipos e
            JOIN tipos t ON t.id_tipo = e.tipo
            WHERE e.en_papelera = 0
            GROUP BY t.tipo
            ORDER BY cantidad DESC";

    $filas = $pdo->query($sql)->fetchAll(PDO::FETCH_ASSOC);
    echo json_encode($filas, JSON_UNESCAPED_UNICODE);

} catch (Throwable $e) {
    sendError("Error al obtener la distribución", 500);
}