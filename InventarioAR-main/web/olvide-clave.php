<?php
// "¿Olvidaste tu contraseña?": envía por correo un enlace de un solo uso para
// elegir una nueva (web/restablecer-clave.php). La respuesta es siempre la misma,
// exista o no la cuenta, así el formulario no revela qué emails están registrados.
require_once __DIR__ . '/inc/inicio.php';
require_once __DIR__ . '/../php/correo.php';

const RECUPERACION_VIGENCIA = 3600;   // el enlace vale una hora

if (usuarioActual()) {
    redirigir('app.php');
}

$email = '';
$error = null;

/** Crea el token de la cuenta (anulando los anteriores) y envía el enlace. */
function enviarRecuperacion(array $usuario): void {
    $token = bin2hex(random_bytes(32));
    bd()->prepare("UPDATE recuperaciones_clave SET usado = 1 WHERE id_usuario = ? AND usado = 0")
        ->execute([$usuario['id_usuario']]);
    bd()->prepare("INSERT INTO recuperaciones_clave (id_usuario, token_hash, vence, ip) VALUES (?, ?, ?, ?)")
        ->execute([$usuario['id_usuario'], hash('sha256', $token),
                   date('Y-m-d H:i:s', time() + RECUPERACION_VIGENCIA), ipCliente()]);

    $enlace = urlBase() . 'restablecer-clave.php?token=' . $token;
    $cuerpo = "Hola {$usuario['nombre']}:\n\n"
            . "Recibimos un pedido para restablecer la contraseña de tu cuenta ({$usuario['username']}) "
            . "en el " . NOMBRE_SISTEMA . ".\n\n"
            . "Para elegir una contraseña nueva, abrí este enlace (vale por una hora y se puede usar una sola vez):\n"
            . "$enlace\n\n"
            . "Si no lo pediste, ignorá este correo: tu contraseña actual sigue funcionando.\n";
    if (!enviarCorreo($usuario['email'], 'Restablecer tu contraseña · ' . NOMBRE_CORTO, $cuerpo)) {
        error_log("Recuperación de clave: no se pudo enviar el correo a la cuenta {$usuario['id_usuario']}");
    }
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $email = trim((string)($_POST['email'] ?? ''));
    if (!csrfValido($_POST['csrf'] ?? null)) {
        $error = 'El formulario venció. Volvé a enviarlo.';
    } elseif (($_POST['sitio_web'] ?? '') !== '') {
        redirigir('olvide-clave.php');   // campo trampa: robot
    } elseif (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
        $error = 'Ingresá un email válido.';
    } elseif ($espera = esperaFormulario('recuperar', 60)) {
        $error = "Ya pediste un enlace hace instantes. Esperá $espera segundos.";
    } else {
        // Solo cuentas que pueden ingresar, y si el email es de una sola cuenta.
        $stmt = bd()->prepare(
            "SELECT id_usuario, username, nombre, email FROM usuarios
             WHERE email = ? AND activo = 1 AND pendiente_aprobacion = 0 LIMIT 2"
        );
        $stmt->execute([$email]);
        $cuentas = $stmt->fetchAll();
        if (count($cuentas) === 1) {
            enviarRecuperacion($cuentas[0]);
        }
        registrarEnvioFormulario('recuperar');
        flash('recuperar_ok', $email);
        redirigir('olvide-clave.php');
    }
}

$enviado = flash('recuperar_ok');
encabezado('Recuperar contraseña', '', ['noindex' => true]);
?>
<section class="caja-formulario caja-angosta">
    <?php if ($enviado): ?>
        <h1>Revisá tu correo</h1>
        <p class="mensaje-info" role="status">
            Si <strong><?= e($enviado) ?></strong> corresponde a una cuenta activa, te enviamos un enlace para
            elegir una contraseña nueva. Vale por una hora.
        </p>
        <p class="texto-suave">¿No llegó? Revisá la carpeta de correo no deseado o
           <a href="olvide-clave.php">pedí otro enlace</a>.</p>
        <p class="pie-formulario"><a href="ingresar.php">Volver a iniciar sesión</a></p>
    <?php else: ?>
        <h1>¿Olvidaste tu contraseña?</h1>
        <p class="texto-suave">Ingresá el email de tu cuenta y te enviamos un enlace para restablecerla.</p>
        <?php if ($error): ?>
            <p class="mensaje-error" role="alert"><?= e($error) ?></p>
        <?php endif; ?>
        <form method="post" action="olvide-clave.php" class="formulario-sitio">
            <input type="hidden" name="csrf" value="<?= e(tokenCsrf()) ?>">
            <div class="trampa" aria-hidden="true">
                <label for="sitio_web">No completar este campo</label>
                <input type="text" id="sitio_web" name="sitio_web" tabindex="-1" autocomplete="off">
            </div>

            <label for="email">Email</label>
            <input type="email" id="email" name="email" value="<?= e($email) ?>" required maxlength="150" autocomplete="email" autofocus>

            <button type="submit" class="btn btn-primario btn-ancho">Enviar enlace</button>
        </form>
        <p class="pie-formulario"><a href="ingresar.php">Volver a iniciar sesión</a></p>
    <?php endif; ?>
</section>
<?php
pie();
