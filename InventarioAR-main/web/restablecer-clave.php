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

encabezado('Nueva contraseña', '', ['noindex' => true, 'ancho_completo' => true]);
$icono = fn(string $trazos) => '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    . 'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' . $trazos . '</svg>';
?>
<section class="hero hero-corto" aria-labelledby="titulo-nueva-clave">
    <div class="hero-imagen" aria-hidden="true">
        <img src="img/portada/inventario-oscuro.webp" alt="" width="1568" height="744" decoding="async">
    </div>
    <div class="contenedor hero-texto">
        <p class="producto"><img src="img/logo.svg" alt="" width="28" height="28"><?= e(NOMBRE_CORTO) ?></p>
        <h1 id="titulo-nueva-clave">Nueva contraseña</h1>
        <p class="hero-bajada">Elegí una contraseña nueva para tu cuenta. Una vez guardada, ya podés ingresar con ella.</p>
        <ul class="hero-enlaces">
            <li><a href="index.php"><?= $icono('<path d="M3 11 12 4l9 7"/><path d="M5 10v10h14V10"/>') ?>Conocé el sistema</a></li>
            <li><a href="contacto.php"><?= $icono('<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>') ?>¿Problemas con el enlace? Escribinos</a></li>
        </ul>
    </div>
</section>

<div class="seccion seccion-formulario">
<div class="contenedor">
<section class="caja-formulario caja-angosta" aria-labelledby="titulo-caja">
    <?php if (!$recuperacion): ?>
        <h2 id="titulo-caja">El enlace no es válido</h2>
        <p class="mensaje-error" role="alert">
            El enlace venció, ya se usó o está incompleto. Los enlaces valen por una hora y una sola vez.
        </p>
        <p><a class="btn btn-primario btn-ancho" href="olvide-clave.php">Pedir un enlace nuevo</a></p>
        <p class="pie-formulario"><a href="ingresar.php">Volver a iniciar sesión</a></p>
    <?php else: ?>
        <h2 id="titulo-caja">Elegí una contraseña nueva</h2>
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
</div>
</div>
<?php
pie();
