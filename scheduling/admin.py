from django.contrib import admin
from .models import Room, ClassType, ClassSchedule, ClassSession

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

@admin.register(ClassSchedule)
class ClassScheduleAdmin(admin.ModelAdmin):
    list_display = ("class_type", "room", "weekday", "start_time", "capacity", "active")
    list_filter = ("weekday", "room", "active")
    search_fields = ("class_type__name", "room__name")
    readonly_fields = ("capacity",)

@admin.register(ClassSession)
class ClassSessionAdmin(admin.ModelAdmin):
    list_display = ("schedule", "start_at", "end_at", "capacity", "status")
    list_filter = ("status", "schedule__room", "schedule__weekday")
    search_fields = ("schedule__class_type__name",)