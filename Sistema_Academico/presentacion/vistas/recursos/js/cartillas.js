const formulario = document.getElementById('carga-masiva');
if (formulario) formulario.addEventListener('submit', async (evento) => {
  evento.preventDefault();
  const archivos = [...formulario.elements.archivos.files, ...formulario.elements.carpeta.files];
  if (!archivos.length) { document.getElementById('progreso-carga').textContent = 'Selecciona imágenes, un PDF o una carpeta.'; return; }
  const progreso = document.getElementById('progreso-carga');
  const boton = formulario.querySelector('button');
  boton.disabled = true;
  let creadas = 0;
  for (let i = 0; i < archivos.length; i++) {
    progreso.textContent = `Procesando ${i + 1} de ${archivos.length}: ${archivos[i].name}`;
    const datos = new FormData();
    datos.append('csrf_token', formulario.elements.csrf_token.value);
    datos.append('examen', formulario.elements.examen.value);
    datos.append('archivos', archivos[i]);
    try {
      const respuesta = await fetch(formulario.action || location.href, {method:'POST', body:datos, headers:{'X-Carga-Lote':'1'}, redirect:'error'});
      const resultado = await respuesta.json();
      if (!respuesta.ok) throw new Error(resultado.error || 'No se pudo procesar el archivo');
      creadas += resultado.creadas;
    } catch (error) {
      progreso.textContent = `Se detuvo en ${archivos[i].name} (${i + 1} de ${archivos.length}). ${creadas} páginas registradas. ${error.message}. Puedes volver a seleccionar los archivos; los duplicados se omiten.`;
      boton.disabled = false;
      return;
    }
  }
  progreso.textContent = `Finalizado: ${creadas} páginas nuevas. Actualizando la lista...`;
  location.reload();
});
