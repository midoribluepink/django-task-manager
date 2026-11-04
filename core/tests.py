from django.test import TestCase

from core.models import Tarea

import json

class TareaAPITests(TestCase):

    def test_listar_tareas_vacias(self):
        respuesta = self.client.get("/api/tareas/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json(), [])
        self.assertEqual(Tarea.objects.count(), 0)

    def test_crear_tarea(self):
        nueva_tarea = {"titulo": "Escribir novela"}

        self.assertEqual(Tarea.objects.count(), 0)

        respuesta = self.client.post(
            "/api/tareas/",
            data=json.dumps(nueva_tarea),
            content_type="application/json"
        )

        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(Tarea.objects.count(), 1)

        tarea_guardada = Tarea.objects.get()
        tarea_devuelta_api = respuesta.json()

        self.assertEqual(tarea_guardada.titulo, "Escribir novela")
        self.assertEqual(tarea_guardada.descripcion, "")
        self.assertIsNone(tarea_guardada.fecha_limite, None)
        self.assertFalse(tarea_guardada.completada, False)
        self.assertEqual(tarea_devuelta_api["id"], tarea_guardada.id)

    def test_crear_tarea_invalida(self):
        casos = [
            {},
            {"descripcion": "Algo"},
            {"titulo": ""},
            {"titulo": "   "},
            {"titulo": 123},
            {"titulo": "Leer", "descripcion": None},
            {"titulo": "Leer", "fecha_limite": "mañana"}
        ]

        for caso in casos:
            with self.subTest(datos=caso):

                respuesta = self.client.post(
                    "/api/tareas/",
                    data=json.dumps(caso),
                    content_type="application/json"
                )

                datos_respuesta = respuesta.json()

                self.assertEqual(respuesta.status_code, 400)
                self.assertIn("error", datos_respuesta)
                self.assertEqual(Tarea.objects.count(), 0)


class TareaConDatosTests(TestCase):

    def setUp(self):
        self.tarea1 = Tarea.objects.create(
            titulo="Estudiar",
            completada=False
        )
        self.tarea2 = Tarea.objects.create(
            titulo="Leer",
            completada=True
        )

    def test_listar_tareas(self):
            
        respuesta = self.client.get("/api/tareas/")
        datos = respuesta.json()

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(datos), 2)

        tareas_por_titulo = {
            tarea["titulo"]: tarea
            for tarea in datos
        }

        self.assertIn("Estudiar", tareas_por_titulo)
        self.assertIn("Leer", tareas_por_titulo)
        self.assertEqual(False, tareas_por_titulo["Estudiar"]["completada"])
        self.assertEqual(True, tareas_por_titulo["Leer"]["completada"])