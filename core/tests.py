from django.test import TestCase

from core.models import Tarea

import json
from datetime import date

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
            {"titulo": ""},
            {"titulo": "   "},
            {"titulo": 123},
            {"titulo": "A" * 101},
            {"descripcion": None},
            {"fecha_limite": "mañana"},
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
                self.assertEqual("Estudiar", self.tarea1.titulo)
                self.assertEqual("", self.tarea1.descripcion)
                self.assertIsNone(self.tarea1.fecha_limite)

    def test_patch_tarea_inexistente(self):

        respuesta = self.client.patch(
            "/api/tareas/9999/",
            data=json.dumps({"completada": True}),
            content_type="application/json"
        )

        self.assertEqual(respuesta.status_code, 404)

    def test_patch_varios_campos(self):

        url = f"/api/tareas/{self.tarea1.id}/"

        respuesta = self.client.patch(
            url,
            data=json.dumps({
                "titulo": "Estudiar Django avanzado",
                "descripcion": "Aprender actualizaciones parciales",
                "fecha_limite": "2026-11-20",
                "completada": True
            }),
            content_type="application/json"
        )

        datos_respuesta = respuesta.json()
        self.tarea1.refresh_from_db()
        self.tarea2.refresh_from_db()

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(self.tarea1.titulo, datos_respuesta["titulo"])
        self.assertEqual(self.tarea1.descripcion, datos_respuesta["descripcion"])
        self.assertEqual(self.tarea1.fecha_limite, date.fromisoformat(datos_respuesta["fecha_limite"]))
        self.assertTrue(self.tarea1.completada)
        self.assertTrue(datos_respuesta["completada"])
        self.assertEqual(datos_respuesta["id"], self.tarea1.id)
        self.assertEqual(self.tarea2.titulo, "Leer")
        self.assertTrue(self.tarea2.completada)

    def test_patch_sin_cambios(self):

        url = f"/api/tareas/{self.tarea1.id}/"

        respuesta = self.client.patch(
            url,
            data=json.dumps({}),
            content_type="application/json"
        )

        datos_respuesta = respuesta.json()
        self.tarea1.refresh_from_db()

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual("Estudiar", self.tarea1.titulo)
        self.assertEqual("Estudiar", datos_respuesta["titulo"])
        self.assertEqual("", self.tarea1.descripcion)
        self.assertEqual("", datos_respuesta["descripcion"])
        self.assertIsNone(self.tarea1.fecha_limite)
        self.assertIsNone(datos_respuesta["fecha_limite"])
        self.assertFalse(self.tarea1.completada)
        self.assertFalse(datos_respuesta["completada"])

    def test_put_tarea_completa(self):

        url = f"/api/tareas/{self.tarea1.id}/"

        respuesta = self.client.put(
            url,
            data=json.dumps({
                "titulo": "Terminar proyecto",
                "descripcion": "Completar el gestor de tareas",
                "fecha_limite": "2026-12-01",
                "completada": True
            }),
            content_type="application/json"
        )

        datos_respuesta = respuesta.json()

        self.tarea1.refresh_from_db()
        self.tarea2.refresh_from_db()

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(self.tarea1.titulo, "Terminar proyecto")
        self.assertEqual(datos_respuesta["titulo"], "Terminar proyecto")
        self.assertEqual(self.tarea1.descripcion, "Completar el gestor de tareas")
        self.assertEqual(datos_respuesta["descripcion"], "Completar el gestor de tareas")
        self.assertEqual(self.tarea1.fecha_limite, date.fromisoformat("2026-12-01"))
        self.assertEqual(datos_respuesta["fecha_limite"], "2026-12-01")
        self.assertTrue(self.tarea1.completada)
        self.assertTrue(datos_respuesta["completada"])
        self.assertEqual(self.tarea1.id, datos_respuesta["id"])
        self.assertEqual(self.tarea2.titulo, "Leer")
        self.assertEqual(self.tarea2.descripcion, "")
        self.assertIsNone(self.tarea2.fecha_limite)
        self.assertTrue(self.tarea2.completada)

    def test_put_valores_predeterminados(self):

        self.tarea2.descripcion = "Terminar una novela"
        self.tarea2.fecha_limite = date(2026, 11, 20)
        self.tarea2.save()

        url = f"/api/tareas/{self.tarea2.id}/"

        respuesta = self.client.put(
            url,
            data=json.dumps({"titulo": "Leer otra novela"}),
            content_type="application/json"
        )

        datos_respuesta = respuesta.json()
        self.tarea2.refresh_from_db()

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(datos_respuesta["titulo"], "Leer otra novela")
        self.assertEqual(self.tarea2.titulo, "Leer otra novela")
        self.assertEqual(datos_respuesta["descripcion"], "")
        self.assertEqual(self.tarea2.descripcion, "")
        self.assertIsNone(datos_respuesta["fecha_limite"])
        self.assertIsNone(self.tarea2.fecha_limite)
        self.assertFalse(datos_respuesta["completada"])
        self.assertFalse(self.tarea2.completada)
        self.assertEqual(datos_respuesta["id"], self.tarea2.id)

    def test_put_tarea_invalida(self):
        casos = [
            {},
            {"titulo": ""},
            {"titulo": "   "},
            {"titulo": 123},
            {"titulo": "A" * 101},
            {"titulo": "Válido", "descripcion": None},
            {"titulo": "Válido", "fecha_limite": "mañana"},
            {"titulo": "Válido", "completada": 1}
        ]

        url = f"/api/tareas/{self.tarea1.id}/"

        self.tarea1.descripcion = "Estudiar Django Rest"
        self.tarea1.fecha_limite = date(2026, 12, 12)
        self.tarea1.completada = True
        self.tarea1.save()

        for caso in casos:
            with self.subTest(caso=caso):

                respuesta = self.client.put(
                    url,
                    data=json.dumps(caso),
                    content_type="application/json"
                )

                self.tarea1.refresh_from_db()

                self.assertEqual(respuesta.status_code, 400)
                self.assertEqual(self.tarea1.titulo, "Estudiar")
                self.assertEqual(self.tarea1.descripcion, "Estudiar Django Rest")
                self.assertEqual(self.tarea1.fecha_limite, date(2026, 12, 12))
                self.assertTrue(self.tarea1.completada)
                self.assertIn("error", respuesta.json())

    def test_delete_tarea(self):

        id = self.tarea1.id

        url = f"/api/tareas/{id}/"

        self.assertTrue(Tarea.objects.filter(id=id).exists())

        respuesta = self.client.delete(url)

        self.assertEqual(respuesta.status_code, 204)
        self.assertEqual(respuesta.content, b"")

        self.assertFalse(Tarea.objects.filter(id=id).exists())
        self.assertTrue(Tarea.objects.filter(id=self.tarea2.id).exists())

    def test_delete_tarea_inexistente(self):

        url = "/api/tareas/9999/"

        respuesta = self.client.delete(url)

        self.assertEqual(respuesta.status_code, 404)
        self.assertIn("error", respuesta.json())
        self.assertTrue(Tarea.objects.filter(id=self.tarea1.id).exists())
        self.assertTrue(Tarea.objects.filter(id=self.tarea2.id).exists())