<?php
require_once 'auth.php';    // reemplaza a conexion.php, ya lo incluye adentro
$user = requireAuth();

try {
    $modelo_equipo = $_GET['imagen_modelo'] ?? '';

    if (!$modelo_equipo) {
        sendError("No se recibieron datos", 400);
        exit;
    }
    
    $pdo = getConnection();

    $sql = "SELECT imagen_modelo FROM modelos WHERE modelo_equipo = :modelo_equipo LIMIT 1";
    $stmt = $pdo->prepare($sql);
    $stmt->bindParam(":modelo_equipo", $modelo_equipo);
    $stmt->execute();

    $ruta_imagen = $stmt->fetchColumn();
    $archivo = $ruta_imagen ? archivoDeImagen($ruta_imagen) : null;

    if ($archivo) {
        sendSuccess($archivo);
    } else {
        sendError("No se encontró la imagen", 404);
    }

} catch(PDOException $e) {
    sendError(API_DEBUG ? $e->getMessage() : "Error al obtener la imagen");
}

/**
 * Nombre real del archivo en resources/images para el valor guardado en la base.
 * En Windows (XAMPP) los nombres no distinguen mayúsculas y en el hosting (Linux)
 * sí: la base tiene "EP450.JPEG" y el archivo es "EP450.jpeg". Se busca, en orden:
 * el nombre exacto, el mismo sin distinguir mayúsculas, y el único archivo con
 * el mismo nombre ignorando extensión, guiones y espacios ("BC355N-JPG" → "BC355N.jpg").
 * Solo devuelve archivos que existen en la carpeta: no sirve para leer otras rutas.
 */
function archivoDeImagen(string $guardado): ?string {
    $archivos = array_values(array_filter(scandir(__DIR__ . '/../resources/images') ?: [],
        fn($a) => $a[0] !== '.'));

    if (in_array($guardado, $archivos, true)) {
        return $guardado;
    }
    foreach ($archivos as $a) {
        if (strcasecmp($a, $guardado) === 0) {
            return $a;
        }
    }
    $base = fn($n) => preg_replace('/[^a-z0-9]/', '',
        preg_replace('/[.\-](jpe?g|png|webp|avif|gif)$/i', '', strtolower($n)));
    $iguales = array_values(array_filter($archivos, fn($a) => $base($a) === $base($guardado)));
    return count($iguales) === 1 ? $iguales[0] : null;
}
?>