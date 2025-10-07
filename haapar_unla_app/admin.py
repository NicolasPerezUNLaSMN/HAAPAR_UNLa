from django.contrib import admin
from .models import Tema, Sistema, Subsistema, TendenciaExterna, PESTEL, Variable, IndicadorVariable, Influencia, VariableTendencia, Evaluacion, ActorClave, RelacionActor

# Registra tus modelos aquí.

@admin.register(Tema)
class TemaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo')

@admin.register(Sistema)
class SistemaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tema')

@admin.register(Subsistema)
class SubsistemaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'sistema', 'activo')

@admin.register(TendenciaExterna)
class TendenciaExternaAdmin(admin.ModelAdmin):
    list_display = ('id_tendencia_externa', 'nombre', 'subsistema', 'activo')
    list_filter = ('subsistema', 'activo')
    search_fields = ('nombre',)

@admin.register(PESTEL)
class PESTELAdmin(admin.ModelAdmin):
    list_display = ('tipo',)

@admin.register(Variable)
class VariableAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'subsistema', 'tipo', 'activo')
    list_filter = ('activo', 'tipo')

@admin.register(IndicadorVariable)
class IndicadorVariableAdmin(admin.ModelAdmin):
    list_display = ('nombre_corto', 'variable')

@admin.register(Influencia)
class InfluenciaAdmin(admin.ModelAdmin):
    list_display = ('variable_origen', 'variable_destino', 'valor')

@admin.register(VariableTendencia)
class VariableTendenciaAdmin(admin.ModelAdmin):
    list_display = ('variable', 'tendencia', 'impacto')

@admin.register(Evaluacion)
class EvaluacionAdmin(admin.ModelAdmin):
    list_display = ('variable', 'importancia', 'incertidumbre', 'usuario_creador')

@admin.register(ActorClave)
class ActorClaveAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'subsistema', 'activo')

@admin.register(RelacionActor)
class RelacionActorAdmin(admin.ModelAdmin):
    list_display = ('actor_clave', 'subsistema', 'influencia')
