<?php
// Validación de datos de usuario sin dependencias de la API: devuelve los
// errores en vez de cortar la respuesta, así la usan tanto los endpoints de
// Administración (usuarios_comun.php) como la página de registro (web/registro.php).

const PERFILES = ['Técnico' => 0, 'Administrador' => 1];
const CLAVE_MINIMO = 8;

/**
 * Valida y normaliza legajo, usuario, nombre, apellido y email.
 * Devuelve [datos, error|null].
 *   $emailObligatorio: el registro público lo exige; Administración no.
 */
function validarDatosPersonales(array $datos, bool $emailObligatorio = false): array {
    $limites = [
        'legajo'   => ['el legajo', 50, true],
        'username' => ['el usuario', 100, true],
        'nombre'   => ['el nombre', 100, true],
        'apellido' => ['el apellido', 100, true],
        'email'    => ['el email', 150, $emailObligatorio],
    ];
    $resultado = [];
    foreach ($limites as $clave => [$nombre, $maximo, $obligatorio]) {
        $valor = trim((string)($datos[$clave] ?? ''));
        if ($valor === '') {
            if ($obligatorio) return [null, "Falta $nombre"];
            $resultado[$clave] = null;
            continue;
        }
        if (mb_strlen($valor) > $maximo) {
            return [null, ucfirst($nombre) . " admite hasta $maximo caracteres"];
        }
        $resultado[$clave] = $valor;
    }
    if (preg_match('/\s/u', $resultado['legajo'])) {
        return [null, "El legajo no puede tener espacios"];
    }
    if (preg_match('/\s/u', $resultado['username'])) {
        return [null, "El nombre de usuario no puede tener espacios"];
    }
    if ($resultado['email'] !== null && !filter_var($resultado['email'], FILTER_VALIDATE_EMAIL)) {
        return [null, "El email no es válido"];
    }
    return [$resultado, null];
}

/** Error de la contraseña elegida por el usuario, o null si es válida. */
function errorClave(string $clave, string $repetir): ?string {
    if (strlen($clave) < CLAVE_MINIMO) {
        return "La contraseña debe tener al menos " . CLAVE_MINIMO . " caracteres";
    }
    if ($clave !== $repetir) {
        return "Las contraseñas no coinciden";
    }
    return null;
}

/** Mensaje si el legajo o el usuario ya los usa otra cuenta, o null. */
function buscarDuplicado(PDO $pdo, string $legajo, string $username, ?int $excluirId = null): ?string {
    $stmt = $pdo->prepare("SELECT legajo FROM usuarios WHERE (legajo = ? OR username = ?) AND id_usuario <> ? LIMIT 1");
    $stmt->execute([$legajo, $username, $excluirId ?? 0]);
    $otro = $stmt->fetchColumn();
    if ($otro === false) {
        return null;
    }
    return strcasecmp($otro, $legajo) === 0
        ? "El legajo '$legajo' ya se encuentra registrado"
        : "El nombre de usuario '$username' ya está en uso";
}

/** Mensaje si el email ya lo usa otra cuenta, o null. El login y la recuperación de clave aceptan el email. */
function emailEnUso(PDO $pdo, string $email, ?int $excluirId = null): ?string {
    $stmt = $pdo->prepare("SELECT 1 FROM usuarios WHERE email = ? AND id_usuario <> ? LIMIT 1");
    $stmt->execute([$email, $excluirId ?? 0]);
    return $stmt->fetchColumn() === false ? null : "El email '$email' ya está registrado en otra cuenta";
}
