from django.contrib import admin
from .models import Room, ClassType

# Register your models here.
@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "capacity")
    search_fields = ("name",)

@admin.register(ClassType)
class ClassTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "duration_min", "default_capacity")
    readonly_fields = ("duration_min",)
    search_fields = ("name",)