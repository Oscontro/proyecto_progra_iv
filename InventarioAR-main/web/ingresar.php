<?php
// Ingreso al sistema (login). Verifica usuario y contraseña, abre la sesión
// de PHP y lleva a la aplicación; si algo falla redirige a error.php con el motivo.
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
encabezado('Ingresar', 'ingresar');
?>
<section class="caja-formulario">
    <h1>Ingresar al sistema</h1>
    <?php if ($aviso): ?>
        <p class="mensaje-info" role="status"><?= e($aviso) ?></p>
    <?php endif; ?>
    <form method="post" action="ingresar.php" class="formulario-sitio">
        <input type="hidden" name="csrf" value="<?= e(tokenCsrf()) ?>">

        <label for="usuario">Usuario</label>
        <input type="text" id="usuario" name="usuario" autocomplete="username" required autofocus maxlength="100">

        <label for="clave">Contraseña</label>
        <input type="password" id="clave" name="clave" autocomplete="current-password" required>

        <button type="submit" class="btn btn-primario btn-ancho">Ingresar</button>
    </form>
    <p class="texto-suave">¿No tenés cuenta? <a href="registro.php">Registrate</a>.</p>
</section>
<?php
pie();
