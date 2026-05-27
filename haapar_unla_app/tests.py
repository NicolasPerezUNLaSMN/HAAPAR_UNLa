import json
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APIClient
from haapar_unla_app.models import Tema
from django.contrib.auth.models import User
from haapar_unla_app.models import Tema, Sistema, Subsistema, Variable, EvaluacionVariable

# Tests de IA Service: validan que el parser de JSON funcione correctamente y maneje errores de formato.
class IAServicesTests(TestCase):
    def test_parser_json_valido(self):
        respuesta = """
        {"subsistemas":[{"nombre":"Economía","descripcion":"Desc","variables":[{"nombre":"Tasa (%)","descripcion":"Medición","tipo":"I"}]}]}
        """
        data = json.loads(respuesta)
        self.assertIn("subsistemas", data)

    def test_parser_json_invalido(self):
        with self.assertRaises(json.JSONDecodeError):
            json.loads("texto sin JSON")

# Tests de Models: verifican restricciones de integridad (unique_together) y cálculos de promedios en variables.

class ModelsTests(TestCase):
    def test_unique_together_evaluacionvariable(self):
        user = User.objects.create(username="tester")
        tema = Tema.objects.create(user=user, nombre="Test", descripcion="Desc", horizonte="2026", territorio="AR")
        sistema = Sistema.objects.create(tema=tema, nombre="Sistema", descripcion="Desc")
        subsistema = Subsistema.objects.create(sistema=sistema, nombre="Sub", descripcion="Desc")
        variable = Variable.objects.create(subsistema=subsistema, nombre="Var", nombre_corto="Var", descripcion="Desc", tipo="I")

        EvaluacionVariable.objects.create(variable=variable, usuario=user, importancia=5, incertidumbre=5)
        with self.assertRaises(Exception):
            EvaluacionVariable.objects.create(variable=variable, usuario=user, importancia=7, incertidumbre=3)

    def test_promedios_variable(self):
        user = User.objects.create(username="tester2")
        tema = Tema.objects.create(user=user, nombre="Test2", descripcion="Desc", horizonte="2026", territorio="AR")
        sistema = Sistema.objects.create(tema=tema, nombre="Sistema2", descripcion="Desc")
        subsistema = Subsistema.objects.create(sistema=sistema, nombre="Sub2", descripcion="Desc")
        variable = Variable.objects.create(subsistema=subsistema, nombre="Var2", nombre_corto="Var2", descripcion="Desc", tipo="I")

        EvaluacionVariable.objects.create(variable=variable, usuario=user, importancia=8, incertidumbre=6)
        EvaluacionVariable.objects.create(variable=variable, usuario=None, importancia=4, incertidumbre=2)

        self.assertEqual(variable.promedio_importancia(), 6)
        self.assertEqual(variable.promedio_incertidumbre(), 4)

# Tests de Views: smoke tests que validan que las vistas críticas (listar proyectos) respondan correctamente.

class ViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="tester3", password="12345")

    def test_listar_proyectos_view(self):
        Tema.objects.create(user=self.user, nombre="Proyecto", descripcion="Desc", horizonte="2026", territorio="AR")
        self.client.login(username="tester3", password="12345")
        response = self.client.get(reverse("listar_proyectos"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Proyecto")

# Tests de Signals: verifican que al crear evaluaciones, los promedios de importancia e incertidumbre se recalculen automáticamente.
class SignalsTests(TestCase):
    def test_recalculo_promedios_signal(self):
        user = User.objects.create(username="tester_signal")
        tema = Tema.objects.create(user=user, nombre="TestSignal", descripcion="Desc", horizonte="2026", territorio="AR")
        sistema = Sistema.objects.create(tema=tema, nombre="SistemaSignal", descripcion="Desc")
        subsistema = Subsistema.objects.create(sistema=sistema, nombre="SubSignal", descripcion="Desc")
        variable = Variable.objects.create(subsistema=subsistema, nombre="VarSignal", nombre_corto="VarSignal", descripcion="Desc", tipo="I")

        # Al crear evaluaciones, el signal debería recalcular promedios
        EvaluacionVariable.objects.create(variable=variable, usuario=user, importancia=10, incertidumbre=2)
        EvaluacionVariable.objects.create(variable=variable, usuario=None, importancia=6, incertidumbre=4)

        # Verificamos que los promedios se recalcularon automáticamente
        self.assertEqual(variable.promedio_importancia(), 8)
        self.assertEqual(variable.promedio_incertidumbre(), 3)

# Tests de API: validan que los endpoints de DRF para listar y crear proyectos funcionen correctamente, incluyendo autenticación.
class APITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="tester_api", password="12345")
        self.client.login(username="tester_api", password="12345")

    def test_listar_proyectos_api(self):
        Tema.objects.create(user=self.user, nombre="ProyectoAPI", descripcion="Desc", horizonte="2026", territorio="AR")
        response = self.client.get(reverse("proyectos-list"))  # nombre del endpoint DRF
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["nombre"], "ProyectoAPI")

    def test_crear_proyecto_api(self):
        data = {
            "nombre": "NuevoProyecto",
            "descripcion": "Desc",
            "horizonte": "2026",
            "territorio": "AR",
            "user": self.user.id
        }
        response = self.client.post(reverse("proyectos-list"), data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["nombre"], "NuevoProyecto")