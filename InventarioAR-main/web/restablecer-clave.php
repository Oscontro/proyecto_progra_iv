<?php
// Elegir una contraseña nueva desde el enlace que envía olvide-clave.php.
// El token se busca por su hash, vale una sola vez y vence a la hora. Al cambiar
// la clave, las sesiones abiertas con la anterior dejan de valer (huella en sesion.php).
require_once __DIR__ . '/inc/inicio.php';
require_once __DIR__ . '/../php/usuarios_validacion.php';

$token = (string)($_POST['token'] ?? $_GET['token'] ?? '');
$error = null;

/** Recuperación vigente para el token (con los datos de la cuenta), o null. */
function recuperacionVigente(string $token): ?array {
    if (!preg_match('/^[0-9a-f]{64}$/', $token)) {
        return null;
    }
    $stmt = bd()->prepare(
        "SELECT r.id_recuperacion, u.id_usuario, u.username
         FROM recuperaciones_clave r JOIN usuarios u ON u.id_usuario = r.id_usuario
         WHERE r.token_hash = ? AND r.usado = 0 AND r.vence > NOW()
           AND u.activo = 1 AND u.pendiente_aprobacion = 0"
    );
    $stmt->execute([hash('sha256', $token)]);
    return $stmt->fetch() ?: null;
}

$recuperacion = recuperacionVigente($token);

if ($recuperacion && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $clave = (string)($_POST['clave'] ?? '');
    if (!csrfValido($_POST['csrf'] ?? null)) {
        $error = 'El formulario venció. Volvé a enviarlo.';
    } elseif (!($error = errorClave($clave, (string)($_POST['repetir'] ?? '')))) {
        $pdo = bd();
        $pdo->beginTransaction();
        $pdo->prepare(
            "UPDATE usuarios SET password_hash = ?, debe_cambiar_clave = 0, intentos_fallidos = 0, bloqueado_hasta = NULL
             WHERE id_usuario = ?"
        )->execute([password_hash($clave, PASSWORD_DEFAULT), $recuperacion['id_usuario']]);
        $pdo->prepare("UPDATE recuperaciones_clave SET usado = 1 WHERE id_usuario = ?")
            ->execute([$recuperacion['id_usuario']]);
        $pdo->commit();

        flash('aviso', 'Tu contraseña se actualizó. Ya podés iniciar sesión con la nueva.');
        redirigir('ingresar.php');
    }
}

encabezado('Nueva contraseña', '', ['noindex' => true]);
?>
<section class="caja-formulario caja-angosta">
    <?php if (!$recuperacion): ?>
        <h1>El enlace no es válido</h1>
        <p class="mensaje-error" role="alert">
            El enlace venció, ya se usó o está incompleto. Los enlaces valen por una hora y una sola vez.
        </p>
        <p><a class="btn btn-primario btn-ancho" href="olvide-clave.php">Pedir un enlace nuevo</a></p>
        <p class="pie-formulario"><a href="ingresar.php">Volver a iniciar sesión</a></p>
    <?php else: ?>
        <h1>Elegí una contraseña nueva</h1>
        <p class="texto-suave">Para la cuenta <strong><?= e($recuperacion['username']) ?></strong>.</p>
        <?php if ($error): ?>
            <p class="mensaje-error" role="alert"><?= e($error) ?></p>
        <?php endif; ?>
        <form method="post" action="restablecer-clave.php" class="formulario-sitio">
            <input type="hidden" name="csrf" value="<?= e(tokenCsrf()) ?>">
            <input type="hidden" name="token" value="<?= e($token) ?>">
            <!-- Para que el navegador asocie la clave guardada a la cuenta -->
            <input type="text" name="usuario" value="<?= e($recuperacion['username']) ?>" autocomplete="username" hidden>

            <label for="clave">Contraseña nueva</label>
            <div class="campo-clave">
                <input type="password" id="clave" name="clave" required minlength="<?= CLAVE_MINIMO ?>" autocomplete="new-password" autofocus aria-describedby="clave-ayuda">
                <button type="button" class="ver-clave" aria-controls="clave" aria-pressed="false" hidden>Mostrar</button>
            </div>
            <small id="clave-ayuda" class="ayuda">Mínimo <?= CLAVE_MINIMO ?> caracteres.</small>

            <label for="repetir">Repetir contraseña</label>
            <input type="password" id="repetir" name="repetir" required autocomplete="new-password">

            <button type="submit" class="btn btn-primario btn-ancho">Guardar contraseña</button>
        </form>
    <?php endif; ?>
</section>
<?php
pie();
