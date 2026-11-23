from pathlib import Path

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.validators import FileExtensionValidator
from django.db import transaction

from .models import Profile

User = get_user_model()


class StyledFields:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


class LoginForm(StyledFields, AuthenticationForm):
    pass


class AvatarField(forms.ImageField):
    formats = {"png": "PNG", "jpg": "JPEG", "jpeg": "JPEG", "webp": "WEBP"}

    def __init__(self):
        super().__init__(
            label="Аватар", required=False, help_text="PNG, JPEG или WebP до 2 МБ.",
            validators=[FileExtensionValidator(self.formats)],
            widget=forms.FileInput(attrs={"accept": "image/png,image/jpeg,image/webp", "data-avatar-input": "avatar-preview"}),
        )

    def to_python(self, data):
        if data and data.size > 2 * 1024 * 1024:
            raise forms.ValidationError("Выберите файл размером до 2 МБ.")
        upload = super().to_python(data)
        if upload and self.formats.get(Path(upload.name).suffix[1:].lower()) != upload.image.format:
            raise forms.ValidationError("Расширение файла должно соответствовать формату PNG, JPEG или WebP.")
        return upload


class SignupForm(StyledFields, UserCreationForm):
    email = forms.EmailField(label="Электронная почта", max_length=254)
    first_name = forms.CharField(label="Имя на сайте", min_length=3, max_length=40)
    avatar = AvatarField()

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["username", "email", "first_name", "password1", "password2", "avatar"]

    @transaction.atomic
    def save(self):
        user = super().save()
        Profile.objects.create(user=user, avatar=self.cleaned_data["avatar"])
        return user


class ProfileForm(StyledFields, forms.ModelForm):
    email = forms.EmailField(label="Электронная почта", max_length=254)
    first_name = forms.CharField(label="Имя на сайте", min_length=3, max_length=150)
    avatar = AvatarField()

    class Meta:
        model = User
        fields = ["email", "first_name", "avatar"]

    @transaction.atomic
    def save(self):
        user = super().save(commit=False)
        user.save(update_fields=["email", "first_name"])
        profile, _ = Profile.objects.get_or_create(user=user)
        if avatar := self.cleaned_data["avatar"]:
            profile.avatar = avatar
            profile.save(update_fields=["avatar"])
        return user
