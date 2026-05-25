from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Tema, Variable, Subsistema
from .serializers import TemaSerializer, VariableSerializer

# 1. Endpoint /api/temas/
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_listar_temas(request):
    # Devuelve los temas del usuario en formato JSON
    temas = Tema.objects.filter(user=request.user, activo=True)
    serializer = TemaSerializer(temas, many=True)
    return Response(serializer.data)

# 2. Endpoint /api/variables/
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_listar_variables(request):
    variables = Variable.objects.filter(activo=True)
    serializer = VariableSerializer(variables, many=True)
    return Response(serializer.data)

# 3. Endpoint /api/foda/<tema_id>/
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_foda_tema(request, tema_id):
    try:
        tema = Tema.objects.get(pk=tema_id, activo=True)
    except Tema.DoesNotExist:
        return Response({'error': 'Tema no encontrado'}, status=404)
    
    # Buscamos las variables asociadas a ese tema
    subsistemas = Subsistema.objects.filter(sistema__tema=tema, activo=True)
    variables = Variable.objects.filter(subsistema__in=subsistemas, activo=True)
    
    # Devolvemos un JSON armado con los datos del tema y sus variables
    data = {
        'tema_id': tema.id_tema,
        'nombre_proyecto': tema.nombre,
        'variables': VariableSerializer(variables, many=True).data
    }
    return Response(data)