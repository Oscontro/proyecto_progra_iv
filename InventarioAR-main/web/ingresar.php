<?php
// Ingreso al sistema (login) con usuario o email. Verifica la contraseña, abre la
// sesión de PHP y lleva a la aplicación; si algo falla redirige a error.php con el motivo.
require_once __DIR__ . '/inc/inicio.php';

if (usuarioActual()) {
    redirigir('app.php');
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (!csrfValido($_POST['csrf'] ?? null)) {
        irAError('csrf');
    }
    $username = trim((string)($_POST['usuario'] ?? ''));
    $clave = (string)($_POST['clave'] ?? '');
    if ($username === '' || $clave === '') {
        irAError('datos');
    }

    $resultado = autenticar(bd(), $username, $clave);
    if (isset($resultado['error'])) {
        irAError($resultado['error']);
    }
    abrirSesion($resultado['usuario']);
    redirigir('app.php');
}

$aviso = flash('aviso');
encabezado('Iniciar sesión', 'ingresar');
?>
<section class="caja-formulario caja-angosta">
    <h1>Iniciar sesión</h1>
    <p class="texto-suave">Ingresá con tu usuario o tu email.</p>
    <?php if ($aviso): ?>
        <p class="mensaje-info" role="status"><?= e($aviso) ?></p>
    <?php endif; ?>
    <form method="post" action="ingresar.php" class="formulario-sitio">
        <input type="hidden" name="csrf" value="<?= e(tokenCsrf()) ?>">

        <label for="usuario">Usuario o email</label>
        <input type="text" id="usuario" name="usuario" autocomplete="username" required autofocus maxlength="150">

        <div class="etiqueta-con-enlace">
            <label for="clave">Contraseña</label>
            <a href="olvide-clave.php">¿Olvidaste tu contraseña?</a>
        </div>
        <div class="campo-clave">
            <input type="password" id="clave" name="clave" autocomplete="current-password" required>
            <!-- Mostrar/ocultar la contraseña (js/sitio.js); sin JavaScript queda oculto -->
            <button type="button" class="ver-clave" aria-controls="clave" aria-pressed="false" hidden>Mostrar</button>
        </div>

        <button type="submit" class="btn btn-primario btn-ancho">Ingresar</button>
    </form>
    <p class="pie-formulario">¿No tenés cuenta? <a href="registro.php">Creá una</a></p>
</section>
<?php
pie();
