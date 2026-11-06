import json
from datetime import date

from django.forms.models import model_to_dict
from django.http import HttpResponseNotAllowed, JsonResponse

from core.models import Tarea


def listar_tareas(request):
    """
    Gestiona la colección de tareas mediante HTTP.

    GET: devuelve todas las tareas.
    POST: valida los datos recibidos y crea una tarea.

    Las tareas nuevas comienzan con completada=False.
    """

    # Consultar todas las tareas existentes
    if request.method == "GET":
        tareas = list(Tarea.objects.values())
        return JsonResponse(tareas, safe=False, status=200)

    # Crear una nueva tarea
    if request.method == "POST":

        # Decodificamos el JSON y verificamos su estructura
        try:
            tarea_nueva = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "JSON inválido"}, status=400)

        if not isinstance(tarea_nueva, dict):
            return JsonResponse({"error": "No es un diccionario"}, status=400)

        if not tarea_nueva:
            return JsonResponse({"error": "El diccionario está vacío"}, status=400)

        if "titulo" not in tarea_nueva:
            return JsonResponse({"error" : "Clave título inexistente"}, status=400)

        titulo = tarea_nueva["titulo"]

        if not isinstance(titulo, str):
            return JsonResponse({"error": "El campo título tiene que ser un dato tipo str"}, status=400)

        # Normalizamos el título antes de comprobar que no esté vacío
        titulo = titulo.strip()

        if not titulo:
            return JsonResponse({"error": "El título no puede ser una cadena vacía"}, status=400)

        if len(titulo) > 100:
            return JsonResponse({"error": "El título no puede contener más de 100 caracteres"}, status=400)

        if "descripcion" not in tarea_nueva:
            descripcion = ""
        else:
            descripcion = tarea_nueva["descripcion"]

        if not isinstance(descripcion, str):
            return JsonResponse({"error": "La descripción debe ser un dato tipo str"}, status=400)

        if "fecha_limite" not in tarea_nueva:
            fecha_limite = None
        else:
            fecha_limite = tarea_nueva["fecha_limite"]

        # Si se proporciona una fecha límite, validamos que esté correctamente dada
        if fecha_limite is not None:

            if not isinstance(fecha_limite, str):
                return JsonResponse({"error": "La fecha límite tiene que tener el tipo de dato str"}, status=400)

            try:
                fecha_limite = date.fromisoformat(fecha_limite)
            except ValueError:
                return JsonResponse({"error": "La fecha límite tiene que tener el formato YYYY-MM-DD"}, status=400)

        tarea_nueva_db = Tarea.objects.create(
            titulo=titulo,
            descripcion=descripcion,
            fecha_limite=fecha_limite,
            completada=False
        )

        tarea_nueva_mandar = model_to_dict(tarea_nueva_db)
        tarea_nueva_mandar["id"] = tarea_nueva_db.id

        return JsonResponse(tarea_nueva_mandar, status=201)   

    return HttpResponseNotAllowed(["GET", "POST"])

def detalle_tarea(request, id):
    """
    Consulta una tarea específica mediante su identificador.

    GET: devuelve los datos de la tarea solicitada.
    """

    if request.method not in ["GET", "PATCH"]:
        return HttpResponseNotAllowed(["GET", "PATCH"])

    tarea = Tarea.objects.filter(id=id).first()

    if tarea is None:
        return JsonResponse({"error": "La tarea no existe"}, status=404)

    if request.method == "GET":
        tarea_mandar = model_to_dict(tarea)
        tarea_mandar["id"] = tarea.id

        return JsonResponse(tarea_mandar, status=200)

    if request.method == "PATCH":

        try:
            datos_recibidos = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "JSON inválido"}, status=400)

        if not isinstance(datos_recibidos, dict):
            return JsonResponse({"error": "El contenido debe ser un diccionario"}, status=400)

        # Validar campo título
        if "titulo" in datos_recibidos:
            titulo = datos_recibidos["titulo"]

            if not isinstance(titulo, str):
                return JsonResponse({"error": "El campo 'titulo' tiene que ser del tipo str"}, status=400)

            titulo = titulo.strip()

            if not titulo:
                return JsonResponse({"error": "El campo 'titulo' no puede estar vacío"}, status=400)

            if len(titulo) > 100:
                return JsonResponse({"error": "El título no puede ser mayor a 100 caracteres"}, status=400)

            tarea.titulo = titulo

        # Validar campo descripcion
        if "descripcion" in datos_recibidos:
            descripcion = datos_recibidos["descripcion"]
            
            if not isinstance(descripcion, str):
                return JsonResponse({"error": "El campo 'descripción' tiene que ser del tipo str"}, status=400)

            tarea.descripcion = descripcion

        # Validar fecha límite
        if "fecha_limite" in datos_recibidos:
            fecha_limite = datos_recibidos["fecha_limite"]
            if fecha_limite is not None and not isinstance(fecha_limite, str):
                return JsonResponse({"error": "El campo 'fecha límite' tiene que ser del tipo null o str"}, status=400)

            if fecha_limite is None:
                tarea.fecha_limite = None
            else:
                if not fecha_limite:
                    return JsonResponse({"error": "No se ha especificado la fecha límite"}, status=400)

                try:
                    fecha_limite = date.fromisoformat(fecha_limite)
                    tarea.fecha_limite = fecha_limite
                except ValueError:
                    return JsonResponse({"error": "El formato de la fecha límite es incorrecto"}, status=400)

        # Validar campo completada
        if "completada" in datos_recibidos:

            if not isinstance(datos_recibidos["completada"], bool):
                return JsonResponse({"error": "El campo 'completada' tiene que ser del tipo bool"}, status=400)

            tarea.completada = datos_recibidos["completada"]

        tarea.save()
        tarea_mandar = model_to_dict(tarea)
        tarea_mandar["id"] = tarea.id

        return JsonResponse(tarea_mandar, status=200)