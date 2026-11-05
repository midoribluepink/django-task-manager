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

    def test_obtener_tarea(self):

        url = f"/api/tareas/{self.tarea1.id}/"

        respuesta = self.client.get(url)
        datos_respuesta = respuesta.json()

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(self.tarea1.titulo, datos_respuesta["titulo"])
        self.assertFalse(datos_respuesta["completada"])
        self.assertEqual(self.tarea1.id, datos_respuesta["id"])

        url2 = f"/api/tareas/{self.tarea2.id}/"

        respuesta2 = self.client.get(url2)
        datos_respuesta2 = respuesta2.json()

        self.assertEqual(respuesta2.status_code, 200)
        self.assertEqual(self.tarea2.titulo, datos_respuesta2["titulo"])
        self.assertTrue(datos_respuesta2["completada"])
        self.assertEqual(self.tarea2.id, datos_respuesta2["id"])

    def test_obtener_tarea_inexistente(self):

        respuesta = self.client.get("/api/tareas/9999/")
        datos_respuesta = respuesta.json()

        self.assertEqual(respuesta.status_code, 404)
        self.assertIn("error", datos_respuesta)

    def test_patch_tarea(self):

        url = f"/api/tareas/{self.tarea1.id}/"

        respuesta = self.client.patch(
            url,
            data=json.dumps({"completada": True}),
            content_type="application/json"
        )

        datos_respuesta = respuesta.json()
        self.tarea1.refresh_from_db()
        self.tarea2.refresh_from_db()

        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(datos_respuesta["completada"])
        self.assertTrue(self.tarea1.completada)
        self.assertEqual(datos_respuesta["id"], self.tarea1.id)
        self.assertEqual("Estudiar", self.tarea1.titulo)
        self.assertTrue(self.tarea2.completada)
        self.assertEqual("Leer", self.tarea2.titulo)

    def test_patch_tarea_invalida(self):

        casos = [
            {},
            {"titulo": "Nuevo"},
            {"completada": None},
            {"completada": 1},
            {"completada": "true"},
            {"completada": []}
        ]

        url = f"/api/tareas/{self.tarea1.id}/"

        for caso in casos:
            with self.subTest(datos=caso):

                respuesta = self.client.patch(
                    url,
                    data=json.dumps(caso),
                    content_type="application/json"
                )

                datos_respuesta = respuesta.json()

                self.tarea1.refresh_from_db()

                self.assertEqual(respuesta.status_code, 400)
                self.assertIn("error", datos_respuesta)
                self.assertFalse(self.tarea1.completada)

    def test_patch_tarea_inexistente(self):

        respuesta = self.client.patch(
            "/api/tareas/9999/",
            data=json.dumps({"completada": True}),
            content_type="application/json"
        )

        self.assertEqual(respuesta.status_code, 404)