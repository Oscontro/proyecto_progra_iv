<?php
// Lista de usuarios para la pestaña Administración (solo administradores).
// debe_cambiar_clave se devuelve con su valor real: antes salía invertido
// (IF(... = 1, False, True)) y el escritorio lo volvía a invertir al mostrarlo.
require_once 'auth.php';
$user = requireAdmin();

try {
    $pdo = getConnection();
    $stmt = $pdo->query(
        "SELECT id_usuario, legajo, username, nombre, apellido, email,
                IF(es_administrador = 1, 'Administrador', 'Técnico') AS perfil,
                activo, pendiente_aprobacion, debe_cambiar_clave,
                fecha_ultima_conexion AS ultima_conexion,
                IF(bloqueado_hasta > NOW(), bloqueado_hasta, NULL) AS bloqueado_hasta
           FROM usuarios
          ORDER BY id_usuario");
    $usuarios = array_map(function ($u) {
        $u['activo'] = (bool)$u['activo'];
        $u['pendiente_aprobacion'] = (bool)$u['pendiente_aprobacion'];
        $u['debe_cambiar_clave'] = (bool)$u['debe_cambiar_clave'];
        return $u;
    }, $stmt->fetchAll(PDO::FETCH_ASSOC));

    echo json_encode($usuarios, JSON_UNESCAPED_UNICODE);
} catch (Throwable $e) {
    sendError(API_DEBUG ? $e->getMessage() : "Error al obtener los usuarios", 500);
}
