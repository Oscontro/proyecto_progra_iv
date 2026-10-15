<?php
// Consultas recibidas por el formulario de contacto (solo administradores).
require_once 'auth.php';
$user = requireAdmin();

try {
    $pdo = getConnection();
    $stmt = $pdo->query(
        "SELECT c.id_contacto, c.nombre, c.email, c.asunto, c.mensaje, c.leido, c.mail_enviado,
                c.fecha, u.username AS usuario
           FROM contactos c LEFT JOIN usuarios u ON u.id_usuario = c.id_usuario
          ORDER BY c.leido ASC, c.fecha DESC");
    $consultas = array_map(function ($c) {
        $c['id_contacto'] = (int)$c['id_contacto'];
        $c['leido'] = (bool)$c['leido'];
        $c['mail_enviado'] = (bool)$c['mail_enviado'];
        return $c;
    }, $stmt->fetchAll(PDO::FETCH_ASSOC));

    echo json_encode($consultas, JSON_UNESCAPED_UNICODE);
} catch (Throwable $e) {
    sendError(API_DEBUG ? $e->getMessage() : "Error al obtener las consultas", 500);
}
