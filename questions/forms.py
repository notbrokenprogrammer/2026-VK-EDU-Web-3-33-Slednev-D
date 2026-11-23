from django import forms
from django.core.validators import validate_unicode_slug
from django.db import transaction
from django.db.models import Sum

from core.forms import StyledFields
from .models import Answer, Question, Tag


class QuestionForm(StyledFields, forms.ModelForm):
    title = forms.CharField(label="Заголовок", min_length=10, max_length=150)
    text = forms.CharField(label="Текст вопроса", min_length=20, max_length=5000, widget=forms.Textarea)
    tag_names = forms.CharField(label="Теги", max_length=100, help_text="До трёх тегов через запятую.")

    class Meta:
        model = Question
        fields = ["title", "text", "tag_names"]

    def clean_tag_names(self):
        names = [part.strip().lower() for part in self.cleaned_data["tag_names"].split(",")]
        if len(names) > 3 or any(not name or len(name) > 64 for name in names):
            raise forms.ValidationError("Введите от одного до трёх тегов, до 64 символов каждый.")
        for name in names:
            validate_unicode_slug(name)
        return list(dict.fromkeys(names))

    @transaction.atomic
    def save(self, author):
        self.instance.author = author
        question = super().save()
        for name in sorted(self.cleaned_data["tag_names"]):
            tag, _ = Tag.objects.get_or_create(name__iexact=name, defaults={"name": name})
            question.tags.add(tag)
        return question


class AnswerForm(StyledFields, forms.ModelForm):
    text = forms.CharField(label="Текст ответа", min_length=10, max_length=5000, widget=forms.Textarea)

    class Meta:
        model = Answer
        fields = ["text"]

    def save(self, author, question):
        self.instance.author = author
        self.instance.question = question
        return super().save()


class VoteForm(forms.Form):
    value = forms.TypedChoiceField(choices=[(1, "Лайк"), (-1, "Дизлайк")], coerce=int)

    def save(self, target, user):
        value = self.cleaned_data["value"]
        vote, created = target.likes.get_or_create(user=user, defaults={"value": value})
        if not created and vote.value == value:
            raise forms.ValidationError("Такая оценка уже поставлена.")
        if not created:
            vote.value = value
            vote.save(update_fields=["value"])
        return {"score": target.likes.aggregate(total=Sum("value"))["total"], "vote": value}


class AcceptedAnswerForm(forms.Form):
    answer = forms.ModelChoiceField(queryset=Answer.objects.none(), error_messages={
        "invalid_choice": "Этот ответ не относится к вопросу.",
    })
    accepted = forms.TypedChoiceField(choices=[("1", "Принять"), ("0", "Снять отметку")], coerce=int)

    def __init__(self, data, question):
        super().__init__(data)
        self.fields["answer"].queryset = question.answers.all()

    def save(self):
        answer = self.cleaned_data["answer"]
        accepted = bool(self.cleaned_data["accepted"])
        if accepted:
            Answer.objects.filter(question_id=answer.question_id, accepted=True).exclude(pk=answer.pk).update(accepted=False)
        answer.accepted = accepted
        answer.save(update_fields=["accepted"])
        return {"answer": answer.pk, "accepted": accepted}
