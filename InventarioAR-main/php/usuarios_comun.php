<?php
// Funciones compartidas por los endpoints de administración de usuarios
// (todos exigen requireAdmin()).
//
// Reglas que antes no se controlaban:
//   - Un administrador no puede desactivarse, eliminarse ni quitarse el
//     perfil a sí mismo (se quedaría afuera).
//   - Siempre tiene que quedar al menos un administrador activo.
//   - La clave temporal (alta y reseteo) es aleatoria y se devuelve una sola
//     vez para que el administrador se la pase al usuario; ya no es "1234".
require_once 'auth.php';

const PERFILES = ['Técnico' => 0, 'Administrador' => 1];

/** Usuario por legajo, o corta con 404. */
function usuarioPorLegajo(PDO $pdo, $legajo): array {
    $legajo = trim((string)($legajo ?? ''));
    if ($legajo === '') {
        sendError("Falta el legajo", 400);
    }
    $stmt = $pdo->prepare("SELECT id_usuario, legajo, username, es_administrador, activo FROM usuarios WHERE legajo = ?");
    $stmt->execute([$legajo]);
    $usuario = $stmt->fetch(PDO::FETCH_ASSOC);
    if (!$usuario) {
        sendError("No existe un usuario con legajo $legajo", 404);
    }
    return $usuario;
}

/** Valida los datos del formulario de usuario y los devuelve normalizados. */
function datosUsuario(array $datos): array {
    $texto = function (string $clave, string $nombre, int $maximo, bool $obligatorio = true) use ($datos): ?string {
        $valor = trim((string)($datos[$clave] ?? ''));
        if ($valor === '') {
            if ($obligatorio) sendError("Falta $nombre", 400);
            return null;
        }
        if (mb_strlen($valor) > $maximo) {
            sendError(ucfirst($nombre) . " admite hasta $maximo caracteres", 400);
        }
        return $valor;
    };
    $resultado = [
        'legajo'   => $texto('legajo', 'el legajo', 50),
        'username' => $texto('username', 'el usuario', 100),
        'nombre'   => $texto('nombre', 'el nombre', 100),
        'apellido' => $texto('apellido', 'el apellido', 100),
        'email'    => $texto('email', 'el email', 150, false),
    ];
    if (preg_match('/\s/u', $resultado['legajo']) || preg_match('/\s/u', $resultado['username'])) {
        sendError("El legajo y el usuario no pueden tener espacios", 400);
    }
    if ($resultado['email'] !== null && !filter_var($resultado['email'], FILTER_VALIDATE_EMAIL)) {
        sendError("El email no es válido", 400);
    }
    $perfil = $datos['perfil'] ?? '';
    if (!array_key_exists($perfil, PERFILES)) {
        sendError("Perfil no válido (Técnico o Administrador)", 400);
    }
    $resultado['es_administrador'] = PERFILES[$perfil];
    $resultado['activo'] = leerBooleano($datos['activo'] ?? true);
    return $resultado;
}

/** true/false, 1/0 o "activar"/"desactivar" (como lo mandaba el escritorio). */
function leerBooleano($valor): int {
    if (is_string($valor)) {
        $valor = strtolower(trim($valor));
        return in_array($valor, ['1', 'true', 'si', 'sí', 'activar'], true) ? 1 : 0;
    }
    return $valor ? 1 : 0;
}

/**
 * Corta con 409 si el cambio deja al sistema sin administradores activos
 * o si el administrador intenta quitarse acceso a sí mismo.
 *   $quedaAdminActivo: si el usuario sigue siendo administrador activo después del cambio.
 */
function controlarAccesoAdmin(PDO $pdo, array $actual, array $user, bool $quedaAdminActivo, string $accion): void {
    if ($quedaAdminActivo) {
        return;
    }
    if ((int)$actual['id_usuario'] === (int)$user['id']) {
        sendError("No podés $accion tu propio usuario: otro administrador tiene que hacerlo", 409);
    }
    if ($actual['es_administrador'] && $actual['activo']) {
        $stmt = $pdo->prepare("SELECT COUNT(*) FROM usuarios WHERE es_administrador = 1 AND activo = 1 AND id_usuario <> ?");
        $stmt->execute([$actual['id_usuario']]);
        if ((int)$stmt->fetchColumn() === 0) {
            sendError("Tiene que quedar al menos un administrador activo", 409);
        }
    }
}

/** Clave temporal aleatoria de 10 caracteres, sin los que se confunden (0/O, 1/l/I). */
function claveTemporal(): string {
    $alfabeto = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    $clave = '';
    for ($i = 0; $i < 10; $i++) {
        $clave .= $alfabeto[random_int(0, strlen($alfabeto) - 1)];
    }
    return $clave;
}

/** Cierra todas las sesiones abiertas de un usuario. */
function cerrarSesiones(PDO $pdo, int $id_usuario): void {
    $pdo->prepare("DELETE FROM sessions WHERE usuario_id = ?")->execute([$id_usuario]);
}

/** Corta con 409 si el legajo o el usuario ya los usa otra cuenta. */
function controlarDuplicados(PDO $pdo, string $legajo, string $username, ?int $excluirId = null): void {
    $stmt = $pdo->prepare("SELECT legajo, username FROM usuarios WHERE (legajo = ? OR username = ?) AND id_usuario <> ?");
    $stmt->execute([$legajo, $username, $excluirId ?? 0]);
    foreach ($stmt->fetchAll(PDO::FETCH_ASSOC) as $otro) {
        if (strcasecmp($otro['legajo'], $legajo) === 0) {
            sendError("El legajo '$legajo' ya se encuentra registrado", 409);
        }
        sendError("El nombre de usuario '$username' ya está en uso", 409);
    }
}

function registrarError(string $accion, array $user, string $detalle): void {
    $linea = date('Y-m-d H:i:s') . " | usuario=" . ($user['id'] ?? 'N/A') . " | $accion | $detalle";
    @file_put_contents(__DIR__ . '/logs/errores_importacion.log', $linea . PHP_EOL, FILE_APPEND);
}
