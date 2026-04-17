from django.contrib import admin
from .models import (
    Tema, Sistema, Subsistema, TendenciaExterna, PESTEL, Variable,
    IndicadorVariable, Influencia, VariableTendencia,
    EvaluacionVariable, EvaluacionTendencia, Historial,
    ActorClave, RelacionActor
)

# ------------------------
# BÁSICOS
# ------------------------

@admin.register(Tema)
class TemaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo')


@admin.register(Sistema)
class SistemaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tema')


@admin.register(Subsistema)
class SubsistemaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'sistema', 'activo')


# ------------------------
# TENDENCIAS
# ------------------------

@admin.register(TendenciaExterna)
class TendenciaExternaAdmin(admin.ModelAdmin):
    list_display = ('id_tendencia_externa', 'nombre', 'subsistema', 'activo')
    list_filter = ('subsistema', 'activo')
    search_fields = ('nombre',)


# ------------------------
# VARIABLES
# ------------------------

@admin.register(Variable)
class VariableAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'subsistema', 'tipo', 'activo')
    list_filter = ('activo', 'tipo')


@admin.register(IndicadorVariable)
class IndicadorVariableAdmin(admin.ModelAdmin):
    list_display = ('nombre_corto', 'variable')


# ------------------------
# RELACIONES
# ------------------------

@admin.register(Influencia)
class InfluenciaAdmin(admin.ModelAdmin):
    list_display = ('variable_origen', 'variable_destino', 'valor')


@admin.register(VariableTendencia)
class VariableTendenciaAdmin(admin.ModelAdmin):
    list_display = ('variable', 'tendencia', 'impacto')


# ------------------------
# EVALUACIONES
# ------------------------

@admin.register(EvaluacionVariable)
class EvaluacionVariableAdmin(admin.ModelAdmin):
    list_display = ('variable', 'usuario', 'importancia', 'incertidumbre', 'fecha')
    list_filter = ('fecha',)
    search_fields = ('variable__nombre',)


@admin.register(EvaluacionTendencia)
class EvaluacionTendenciaAdmin(admin.ModelAdmin):
    list_display = ('tendencia', 'usuario', 'importancia', 'incertidumbre', 'fecha')
    list_filter = ( 'fecha',)
    search_fields = ('tendencia__nombre',)


# ------------------------
#  HISTORIAL
# ------------------------

@admin.register(Historial)
class HistorialAdmin(admin.ModelAdmin):
    list_display = ('accion', 'variable', 'tendencia', 'usuario', 'fecha')
    list_filter = ('accion', 'fecha')
    search_fields = ('variable__nombre', 'tendencia__nombre')


# ------------------------
# ACTORES
# ------------------------

@admin.register(ActorClave)
class ActorClaveAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'subsistema', 'activo')


@admin.register(RelacionActor)
class RelacionActorAdmin(admin.ModelAdmin):
    list_display = ('actor_clave', 'subsistema', 'influencia')