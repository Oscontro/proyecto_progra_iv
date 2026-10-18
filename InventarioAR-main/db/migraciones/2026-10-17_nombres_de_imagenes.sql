-- Corrige dos nombres de imagen mal cargados en `modelos` que no apuntan a
-- ningún archivo de resources/images (ni siquiera ignorando mayúsculas).
-- El resto de las diferencias (mayúsculas, "-JPG" en vez de ".jpg") las
-- resuelve php/imagen.php buscando el archivo real.
--
-- Aplicar en la base local y en el phpMyAdmin del hosting.

UPDATE modelos SET imagen_modelo = 'DEP450.PNG'  WHERE imagen_modelo = 'DEP.PNG';
UPDATE modelos SET imagen_modelo = 'PRO3100.jpg' WHERE imagen_modelo = 'PRO31000.JPG';
