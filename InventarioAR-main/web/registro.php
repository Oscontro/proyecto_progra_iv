<?php
// Registro de usuarios "generales" (perfil Técnico). La cuenta queda
// pendiente: un administrador la aprueba desde la pestaña Administración.
require_once __DIR__ . '/inc/inicio.php';
require_once __DIR__ . '/../php/usuarios_validacion.php';

if (usuarioActual()) {
    redirigir('app.php');
}

$valores = ['legajo' => '', 'username' => '', 'nombre' => '', 'apellido' => '', 'email' => ''];
$error = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    foreach ($valores as $campo => $_) {
        $valores[$campo] = trim((string)($_POST[$campo] ?? ''));
    }
    if (!csrfValido($_POST['csrf'] ?? null)) {
        $error = 'El formulario venció. Volvé a enviarlo.';
    } elseif (($_POST['sitio_web'] ?? '') !== '') {
        // Campo trampa invisible: solo lo completan los robots.
        redirigir('registro.php');
    } elseif ($espera = esperaFormulario('registro', 60)) {
        $error = "Ya enviaste una solicitud hace instantes. Esperá $espera segundos.";
    } else {
        [$datos, $error] = validarDatosPersonales($valores, true);
        $error ??= errorClave((string)($_POST['clave'] ?? ''), (string)($_POST['repetir'] ?? ''));
        $error ??= buscarDuplicado(bd(), $datos['legajo'], $datos['username']);

        if (!$error) {
            bd()->prepare(
                "INSERT INTO usuarios
                    (legajo, username, nombre, apellido, email, password_hash,
                     es_administrador, debe_cambiar_clave, activo, pendiente_aprobacion)
                 VALUES (?, ?, ?, ?, ?, ?, 0, 0, 0, 1)"
            )->execute([$datos['legajo'], $datos['username'], $datos['nombre'], $datos['apellido'],
                        $datos['email'], password_hash((string)$_POST['clave'], PASSWORD_DEFAULT)]);
            registrarEnvioFormulario('registro');
            flash('registro_ok', $datos['username']);
            redirigir('registro.php');
        }
    }
}

$registrado = flash('registro_ok');
encabezado('Registrarse', 'registro', [
    'descripcion' => 'Creá tu cuenta en el ' . NOMBRE_SISTEMA . '. Un administrador aprueba la solicitud antes del primer ingreso.',
]);
?>
<section class="caja-formulario">
    <?php if ($registrado): ?>
        <h1>¡Solicitud enviada!</h1>
        <p class="mensaje-info" role="status">
            La cuenta <strong><?= e($registrado) ?></strong> quedó registrada y pendiente de aprobación.
            Cuando un administrador la apruebe vas a poder ingresar con tu usuario y contraseña.
        </p>
        <p><a class="btn btn-primario" href="index.php">Volver al inicio</a></p>
    <?php else: ?>
        <h1>Crear una cuenta</h1>
        <p class="texto-suave">Las cuentas nuevas tienen perfil <strong>Técnico</strong> y un administrador debe aprobarlas.</p>
        <?php if ($error): ?>
            <p class="mensaje-error" role="alert"><?= e($error) ?></p>
        <?php endif; ?>
        <form method="post" action="registro.php" class="formulario-sitio">
            <input type="hidden" name="csrf" value="<?= e(tokenCsrf()) ?>">
            <div class="trampa" aria-hidden="true">
                <label for="sitio_web">No completar este campo</label>
                <input type="text" id="sitio_web" name="sitio_web" tabindex="-1" autocomplete="off">
            </div>

            <div class="rejilla-dos">
                <div>
                    <label for="legajo">Legajo</label>
                    <input type="text" id="legajo" name="legajo" value="<?= e($valores['legajo']) ?>" required maxlength="50" autocomplete="off">
                </div>
                <div>
                    <label for="username">Usuario</label>
                    <input type="text" id="username" name="username" value="<?= e($valores['username']) ?>" required maxlength="100" autocomplete="username">
                </div>
                <div>
                    <label for="nombre">Nombre</label>
                    <input type="text" id="nombre" name="nombre" value="<?= e($valores['nombre']) ?>" required maxlength="100" autocomplete="given-name">
                </div>
                <div>
                    <label for="apellido">Apellido</label>
                    <input type="text" id="apellido" name="apellido" value="<?= e($valores['apellido']) ?>" required maxlength="100" autocomplete="family-name">
                </div>
            </div>

            <label for="email">Email</label>
            <input type="email" id="email" name="email" value="<?= e($valores['email']) ?>" required maxlength="150" autocomplete="email">

            <div class="rejilla-dos">
                <div>
                    <label for="clave">Contraseña</label>
                    <input type="password" id="clave" name="clave" required minlength="<?= CLAVE_MINIMO ?>" autocomplete="new-password" aria-describedby="clave-ayuda">
                    <small id="clave-ayuda" class="ayuda">Mínimo <?= CLAVE_MINIMO ?> caracteres.</small>
                </div>
                <div>
                    <label for="repetir">Repetir contraseña</label>
                    <input type="password" id="repetir" name="repetir" required autocomplete="new-password">
                </div>
            </div>

            <button type="submit" class="btn btn-primario btn-ancho">Enviar solicitud</button>
        </form>
        <p class="texto-suave">¿Ya tenés cuenta? <a href="ingresar.php">Ingresá</a>.</p>
    <?php endif; ?>
</section>
<?php
pie();
