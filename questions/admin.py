from django import forms
from django.contrib import admin
from django.db.models import Exists, OuterRef

from .models import Answer, AnswerLike, Question, QuestionLike, Tag


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    fields = ["author", "text", "accepted"]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "author":
            # В строках ответов поле ID не загружает список пользователей и подпись для каждого автора.
            kwargs["widget"] = forms.NumberInput(attrs={"min": 1, "aria-label": "ID автора"})
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "created_at"]
    list_select_related = ["author"]
    search_fields = ["title", "text", "author__username"]
    list_filter = ["created_at"]
    autocomplete_fields = ["author", "tags"]
    inlines = [AnswerInline]


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ["__str__", "question", "author", "accepted", "created_at"]
    list_select_related = ["author", "question"]
    search_fields = ["text", "question__title", "author__username"]
    list_filter = ["accepted", "created_at"]
    autocomplete_fields = ["question", "author"]


class UsedTagFilter(admin.SimpleListFilter):
    title = "Использование"
    parameter_name = "used"

    def lookups(self, request, model_admin):
        return [("yes", "Есть вопросы"), ("no", "Без вопросов")]

    def queryset(self, request, queryset):
        used = Exists(Question.tags.through.objects.filter(tag_id=OuterRef("pk")))
        if self.value() == "yes":
            return queryset.filter(used)
        if self.value() == "no":
            return queryset.filter(~used)
        return queryset


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    search_fields = ["name"]
    list_filter = [UsedTagFilter]


@admin.register(QuestionLike)
class QuestionLikeAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "question"]
    list_select_related = ["user", "question"]
    search_fields = ["user__username", "question__title"]
    list_filter = ["user__is_active"]
    autocomplete_fields = ["user", "question"]


@admin.register(AnswerLike)
class AnswerLikeAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "answer"]
    list_select_related = ["user", "answer"]
    search_fields = ["user__username", "answer__text"]
    list_filter = ["answer__accepted"]
    autocomplete_fields = ["user", "answer"]
