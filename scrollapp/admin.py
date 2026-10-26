from django.contrib import admin
from .models import ScrollSession, BreakEvent,UserGoal
from .models import UserGoal


# Register your models here.

class ScrollSessionAdmin(admin.ModelAdmin):
    list_display = ('app_name','duration','scroll_count','momentum','created_at')
    


admin.site.register(ScrollSession,ScrollSessionAdmin)
admin.site.register(UserGoal)
admin.site.register(BreakEvent)